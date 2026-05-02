import os
import sqlite3
from datetime import datetime, timedelta

# On Railway the volume is mounted at /data; locally falls back to the cwd.
_data_dir = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "")
if _data_dir:
    os.makedirs(_data_dir, exist_ok=True)
DATABASE = os.path.join(_data_dir, "litflow.db") if _data_dir else "litflow.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT DEFAULT '',
            year INTEGER,
            aim TEXT DEFAULT '',
            research_questions TEXT DEFAULT '',
            data_used TEXT DEFAULT '',
            methodology TEXT DEFAULT '',
            techniques TEXT DEFAULT '',
            findings TEXT DEFAULT '',
            key_insights TEXT DEFAULT '',
            reflection TEXT DEFAULT '',
            status TEXT DEFAULT 'To Read',
            tags TEXT DEFAULT '',
            date_added TEXT DEFAULT (date('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS weekly_diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start TEXT NOT NULL UNIQUE,
            papers_read INTEGER DEFAULT 0,
            key_themes TEXT DEFAULT '',
            new_ideas TEXT DEFAULT '',
            challenges TEXT DEFAULT '',
            next_steps TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()


# ── Papers ──────────────────────────────────────────────────────────────────

def add_paper(data: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO papers
            (title, authors, year, aim, research_questions, data_used,
             methodology, techniques, findings, key_insights, reflection,
             status, tags, date_added)
        VALUES
            (:title, :authors, :year, :aim, :research_questions, :data_used,
             :methodology, :techniques, :findings, :key_insights, :reflection,
             :status, :tags, :date_added)
    """, data)
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid


def update_paper(paper_id: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE papers
        SET title=:title, authors=:authors, year=:year, aim=:aim,
            research_questions=:research_questions, data_used=:data_used,
            methodology=:methodology, techniques=:techniques,
            findings=:findings, key_insights=:key_insights,
            reflection=:reflection, status=:status, tags=:tags
        WHERE id=:id
    """, {**data, "id": paper_id})
    conn.commit()
    conn.close()


def delete_paper(paper_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM papers WHERE id=?", (paper_id,))
    conn.commit()
    conn.close()


def get_all_papers() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM papers ORDER BY date_added DESC, id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_paper(paper_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_papers_filtered(
    methodology=None, technique=None, tag=None,
    status=None, year_from=None, year_to=None
) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM papers WHERE 1=1"
    params: list = []
    if methodology:
        query += " AND methodology=?"; params.append(methodology)
    if technique:
        query += " AND techniques LIKE ?"; params.append(f"%{technique}%")
    if tag:
        query += " AND tags LIKE ?"; params.append(f"%{tag}%")
    if status:
        query += " AND status=?"; params.append(status)
    if year_from:
        query += " AND year >= ?"; params.append(year_from)
    if year_to:
        query += " AND year <= ?"; params.append(year_to)
    query += " ORDER BY date_added DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Weekly Diary ─────────────────────────────────────────────────────────────

def add_or_update_diary(data: dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO weekly_diary
            (week_start, papers_read, key_themes, new_ideas, challenges, next_steps)
        VALUES
            (:week_start, :papers_read, :key_themes, :new_ideas, :challenges, :next_steps)
        ON CONFLICT(week_start) DO UPDATE SET
            papers_read  = excluded.papers_read,
            key_themes   = excluded.key_themes,
            new_ideas    = excluded.new_ideas,
            challenges   = excluded.challenges,
            next_steps   = excluded.next_steps
    """, data)
    conn.commit()
    conn.close()


def get_all_diary() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM weekly_diary ORDER BY week_start DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_diary_by_week(week_start: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM weekly_diary WHERE week_start=?", (week_start,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_papers_in_week(week_start: str) -> list[dict]:
    week_end = (
        datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=7)
    ).strftime("%Y-%m-%d")
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM papers WHERE date_added >= ? AND date_added < ?",
        (week_start, week_end),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
