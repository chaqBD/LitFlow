import calendar
import io
from collections import defaultdict
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import database as db

DAYS     = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
STATUSES = ["Planned", "Reading", "Completed", "Skipped"]

_STATUS_VAL  = {"": 0, "Planned": 1, "Reading": 2, "Completed": 3, "Skipped": -1}
_STATUS_ICON = {"Planned": "📋", "Reading": "📖", "Completed": "✅", "Skipped": "⏭️", "": "—"}
_STATUS_CLR  = {"Planned": "#DBEAFE", "Reading": "#FEF3C7",
                "Completed": "#D1FAE5", "Skipped": "#FEE2E2", "": "#F1F5F9"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _week_label(ws: str) -> str:
    dt = datetime.strptime(ws, "%Y-%m-%d")
    we = dt + timedelta(days=6)
    return f"{dt.strftime('%b %d')} – {we.strftime('%b %d, %Y')}"


def _plan_to_df(entries: list[dict]) -> pd.DataFrame:
    plan_map = {e["day_of_week"]: e for e in entries}
    rows = []
    for day in DAYS:
        e = plan_map.get(day, {})
        rows.append({
            "Day":          day,
            "Title":        e.get("planned_title", ""),
            "Author":       e.get("planned_author", ""),
            "Focus / RQ":   e.get("focus", ""),
            "Data Source":  e.get("data_source", ""),
            "Methodology":  e.get("methodology", ""),
            "Findings":     e.get("findings", ""),
            "Limitations":  e.get("limitations", ""),
            "Status":       e.get("status", "Planned"),
            "Notes":        e.get("notes", ""),
        })
    return pd.DataFrame(rows)


def _df_to_entries(df: pd.DataFrame) -> list[dict]:
    return [
        dict(
            day_of_week    = row["Day"],
            planned_title  = str(row.get("Title", "") or ""),
            planned_author = str(row.get("Author", "") or ""),
            focus          = str(row.get("Focus / RQ", "") or ""),
            data_source    = str(row.get("Data Source", "") or ""),
            methodology    = str(row.get("Methodology", "") or ""),
            findings       = str(row.get("Findings", "") or ""),
            limitations    = str(row.get("Limitations", "") or ""),
            status         = str(row.get("Status", "Planned") or "Planned"),
            notes          = str(row.get("Notes", "") or ""),
        )
        for _, row in df.iterrows()
    ]


def _ws(d) -> str:
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d")
    return (d - timedelta(days=d.weekday())).strftime("%Y-%m-%d")


# ── Tab 1: Weekly Planner ─────────────────────────────────────────────────────

def _weekly_planner():
    raw = st.date_input("Select week", value=_monday(date.today()),
                        help="Any date — snaps to Monday", key="planner_date")
    ws  = _monday(raw).strftime("%Y-%m-%d")
    st.markdown(f"**Week: {_week_label(ws)}**")

    entries = db.get_plan_by_week(ws)
    df      = _plan_to_df(entries)

    st.caption("Edit cells directly. Click **💾 Save Plan** when done.")

    edited = st.data_editor(
        df,
        column_config={
            "Day":         st.column_config.TextColumn("Day", disabled=True, width=90),
            "Title":       st.column_config.TextColumn("Paper / Title", width=220),
            "Author":      st.column_config.TextColumn("Author", width=130),
            "Focus / RQ":  st.column_config.TextColumn("Focus / RQ", width=150),
            "Data Source": st.column_config.TextColumn("Data Source", width=130),
            "Methodology": st.column_config.TextColumn("Methodology", width=120),
            "Findings":    st.column_config.TextColumn("Findings", width=160),
            "Limitations": st.column_config.TextColumn("Limitations", width=140),
            "Status":      st.column_config.SelectboxColumn(
                               "Status", options=STATUSES, width=110, required=True),
            "Notes":       st.column_config.TextColumn("Notes", width=140),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key=f"plan_editor_{ws}",
    )

    c1, c2, _ = st.columns([1, 1, 5])
    with c1:
        if st.button("💾 Save Plan", type="primary", use_container_width=True):
            db.upsert_plan_entries(ws, _df_to_entries(edited))
            st.success("Plan saved!")

    with c2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            edited.to_excel(writer, sheet_name=f"Week {ws}", index=False)
        st.download_button(
            "📥 Export (.xlsx)",
            data=buf.getvalue(),
            file_name=f"litflow_plan_{ws}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    # Quick stats strip
    st.markdown("---")
    has_paper = int(edited["Title"].str.strip().ne("").sum())
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Papers Planned",  has_paper)
    c2.metric("📋 Planned",      int((edited["Status"] == "Planned").sum()))
    c3.metric("📖 Reading",      int((edited["Status"] == "Reading").sum()))
    c4.metric("✅ Completed",    int((edited["Status"] == "Completed").sum()))
    c5.metric("⏭️ Skipped",     int((edited["Status"] == "Skipped").sum()))


# ── Tab 2: Plan vs Actual ─────────────────────────────────────────────────────

def _plan_vs_actual():
    raw = st.date_input("Select week", value=_monday(date.today()), key="pva_date")
    ws  = _monday(raw).strftime("%Y-%m-%d")
    st.markdown(f"**Week: {_week_label(ws)}**")

    plan        = db.get_plan_by_week(ws)
    plan_map    = {e["day_of_week"]: e for e in plan}
    actuals     = db.get_papers_in_week(ws)

    planned_count   = sum(1 for e in plan if e.get("planned_title"))
    completed_count = sum(1 for e in plan if e.get("status") == "Completed")
    rate            = round(completed_count / planned_count * 100) if planned_count else 0

    # KPI strip
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Papers Planned",        planned_count)
    c2.metric("Completed (vs plan)",   completed_count)
    c3.metric("Papers Logged (actual)", len(actuals))
    c4.metric("Plan Completion Rate",  f"{rate}%",
              delta="On track" if rate >= 70 else "Below target")

    if rate == 100 and planned_count:
        st.success("🎉 Perfect week — every planned paper completed!")
    elif rate >= 70:
        st.info(f"Strong week — {rate}% completion.")
    elif planned_count:
        st.warning(f"Partial completion — {rate}% of planned papers done.")

    st.markdown("---")

    # Side-by-side comparison
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("### 📋 Planned")
        if not plan:
            st.info("No plan set for this week. Use the Weekly Planner tab.")
        else:
            for day in DAYS:
                e    = plan_map.get(day)
                icon = _STATUS_ICON.get(e["status"] if e else "", "—")
                if e and e.get("planned_title"):
                    bg = _STATUS_CLR.get(e["status"], "#F1F5F9")
                    st.markdown(
                        f'<div style="background:{bg};border-radius:8px;'
                        f'padding:8px 12px;margin-bottom:6px;">'
                        f'<b>{day}</b> &nbsp; {icon} {e["planned_title"]}'
                        + (f'<br><small>{e["planned_author"]}</small>' if e.get("planned_author") else "")
                        + (f'<br><small>Focus: {e["focus"]}</small>' if e.get("focus") else "")
                        + "</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="background:#F8FAFC;border-radius:8px;'
                        f'padding:8px 12px;margin-bottom:6px;color:#94A3B8;">'
                        f'<b>{day}</b> &nbsp; — not planned</div>',
                        unsafe_allow_html=True,
                    )

    with col_r:
        st.markdown("### ✅ Actual Papers Logged")
        if not actuals:
            st.info("No papers logged this week.")
        else:
            for p in actuals:
                icon = "✅" if p["status"] == "Completed" else \
                       "📖" if p["status"] == "Reading"   else "📋"
                bg   = "#D1FAE5" if p["status"] == "Completed" else \
                       "#FEF3C7" if p["status"] == "Reading"   else "#F1F5F9"
                st.markdown(
                    f'<div style="background:{bg};border-radius:8px;'
                    f'padding:8px 12px;margin-bottom:6px;">'
                    f'{icon} <b>{p["title"]}</b>'
                    + (f'<br><small>{p.get("authors","")}</small>' if p.get("authors") else "")
                    + (f'<br><small>{p.get("methodology","")} · {p.get("techniques","")}</small>'
                       if p.get("methodology") else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )

        # Match rate badge
        if planned_count and actuals:
            match = sum(
                1 for p in actuals
                for e in plan
                if e.get("planned_title", "").lower()[:15] in p["title"].lower()
            )
            if match:
                st.success(f"🔗 {match} logged paper(s) match the plan by title.")


# ── Tab 3: Monthly Map ────────────────────────────────────────────────────────

def _monthly_map():
    today = date.today()
    c1, c2 = st.columns(2)
    year  = c1.selectbox("Year",  list(range(today.year - 2, today.year + 2)),
                         index=2, key="map_year")
    month = c2.selectbox("Month", list(range(1, 13)), index=today.month - 1,
                         format_func=lambda m: calendar.month_name[m], key="map_month")

    first_day   = date(year, month, 1)
    last_day    = date(year, month, calendar.monthrange(year, month)[1])
    range_start = _monday(first_day)
    range_end   = _monday(last_day) + timedelta(days=6)

    entries = db.get_plan_by_date_range(
        range_start.strftime("%Y-%m-%d"),
        range_end.strftime("%Y-%m-%d"),
    )
    actuals = db.get_papers_in_date_range(
        range_start.strftime("%Y-%m-%d"),
        range_end.strftime("%Y-%m-%d"),
    )

    # Build day → status / title maps
    day_status: dict[date, str] = {}
    day_title:  dict[date, str] = {}
    for e in entries:
        di  = DAYS.index(e["day_of_week"])
        day = datetime.strptime(e["week_start"], "%Y-%m-%d").date() + timedelta(days=di)
        day_status[day] = e.get("status", "")
        day_title[day]  = e.get("planned_title", "")

    actual_by_day: dict[date, list[str]] = defaultdict(list)
    for p in actuals:
        if p.get("date_added"):
            try:
                d = datetime.strptime(p["date_added"], "%Y-%m-%d").date()
                actual_by_day[d].append(p["title"])
            except Exception:
                pass

    # Build calendar grid (rows = weeks, cols = Mon–Sun)
    weeks = []
    w = range_start
    while w <= range_end:
        weeks.append(w)
        w += timedelta(weeks=1)

    z_vals, hover, cell_text = [], [], []
    for wk in weeks:
        zrow, hrow, trow = [], [], []
        for di in range(7):
            d = wk + timedelta(days=di)
            if d.month != month:
                zrow.append(None); hrow.append(""); trow.append("")
            else:
                status = day_status.get(d, "")
                zrow.append(_STATUS_VAL.get(status, 0))
                title  = day_title.get(d, "")
                logged = actual_by_day.get(d, [])
                htxt   = f"<b>{d.strftime('%A %b %d')}</b><br>"
                htxt  += f"Planned: {title}<br>Status: {status}" if title else "Not planned"
                if logged:
                    htxt += f"<br>Logged: {'; '.join(logged[:2])}"
                hrow.append(htxt)
                icon   = _STATUS_ICON.get(status, "")
                trow.append(icon)
        z_vals.append(zrow); hover.append(hrow); cell_text.append(trow)

    week_labels = [
        f"Wk {(wk - first_day).days // 7 + 1}  {wk.strftime('%b %d')}"
        for wk in weeks
    ]

    fig = go.Figure(go.Heatmap(
        z          = z_vals,
        x          = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        y          = week_labels,
        text       = hover,
        customdata = cell_text,
        hovertemplate = "%{text}<extra></extra>",
        colorscale = [
            [0.00, "#F1F5F9"],  # not planned
            [0.25, "#BFDBFE"],  # planned
            [0.50, "#FDE68A"],  # reading
            [0.75, "#6EE7B7"],  # completed
            [1.00, "#FCA5A5"],  # skipped
        ],
        showscale = False,
        zmin=-1, zmax=3,
    ))
    fig.update_layout(
        height=max(220, len(weeks) * 65),
        margin=dict(t=10, b=10, l=80, r=10),
        xaxis=dict(side="top"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Legend row
    lc = st.columns(5)
    for col, (label, clr) in zip(lc, [
        ("Not Planned", "#94A3B8"), ("📋 Planned", "#3B82F6"),
        ("📖 Reading",  "#F59E0B"), ("✅ Completed", "#10B981"),
        ("⏭️ Skipped",  "#EF4444"),
    ]):
        col.markdown(
            f'<span style="color:{clr};font-size:1.1rem">■</span> {label}',
            unsafe_allow_html=True,
        )

    # Monthly stats
    st.markdown("---")
    month_entries = [e for e in entries if e.get("planned_title")]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Papers Planned",    len(month_entries))
    c2.metric("✅ Completed",      sum(1 for e in month_entries if e["status"] == "Completed"))
    c3.metric("⏭️ Skipped",       sum(1 for e in month_entries if e["status"] == "Skipped"))
    c4.metric("Papers Logged",     len(actuals))

    # Detailed monthly list
    if month_entries or actuals:
        st.markdown("---")
        tab_plan, tab_actual = st.tabs(["📋 Full Monthly Plan", "📚 All Papers Logged"])
        with tab_plan:
            if month_entries:
                df_plan = pd.DataFrame([{
                    "Week Start": e["week_start"],
                    "Day":        e["day_of_week"],
                    "Title":      e.get("planned_title", ""),
                    "Author":     e.get("planned_author", ""),
                    "Focus":      e.get("focus", ""),
                    "Methodology":e.get("methodology", ""),
                    "Status":     e.get("status", ""),
                } for e in month_entries])
                st.dataframe(df_plan, use_container_width=True, hide_index=True)

                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as w:
                    df_plan.to_excel(w, sheet_name="Monthly Plan", index=False)
                st.download_button(
                    f"📥 Export {calendar.month_name[month]} Plan (.xlsx)",
                    data=buf.getvalue(),
                    file_name=f"litflow_monthly_plan_{year}_{month:02d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.info("No planned papers for this month.")

        with tab_actual:
            if actuals:
                df_actual = pd.DataFrame([{
                    "Date Added":  p.get("date_added", ""),
                    "Title":       p.get("title", ""),
                    "Authors":     p.get("authors", ""),
                    "Methodology": p.get("methodology", ""),
                    "Techniques":  p.get("techniques", ""),
                    "Status":      p.get("status", ""),
                } for p in actuals])
                st.dataframe(df_actual, use_container_width=True, hide_index=True)
            else:
                st.info("No papers logged this month.")


# ── Tab 4: Reading Velocity ───────────────────────────────────────────────────

def _reading_velocity():
    all_plan   = db.get_all_plan_entries()
    all_papers = db.get_all_papers()

    if not all_plan and not all_papers:
        st.info("No data yet — add papers and set weekly plans to see velocity metrics.")
        return

    # Aggregate plan by week
    plan_by_week: dict[str, dict] = defaultdict(lambda: {"planned": 0, "completed": 0, "skipped": 0})
    for e in all_plan:
        if e.get("planned_title"):
            wk = e["week_start"]
            plan_by_week[wk]["planned"]   += 1
            if e["status"] == "Completed": plan_by_week[wk]["completed"] += 1
            if e["status"] == "Skipped":   plan_by_week[wk]["skipped"]   += 1

    # Aggregate actual papers by week
    actual_by_week: dict[str, int] = defaultdict(int)
    for p in all_papers:
        if p.get("date_added"):
            try:
                actual_by_week[_ws(p["date_added"])] += 1
            except Exception:
                pass

    all_weeks = sorted(set(list(plan_by_week.keys()) + list(actual_by_week.keys())))
    if not all_weeks:
        st.info("No weekly data available yet.")
        return

    rows = []
    for wk in all_weeks:
        pw = plan_by_week[wk]
        rows.append({
            "Week":                wk,
            "Planned":             pw["planned"],
            "Completed (plan)":    pw["completed"],
            "Actually Logged":     actual_by_week.get(wk, 0),
            "Completion Rate (%)": round(pw["completed"] / pw["planned"] * 100)
                                   if pw["planned"] else 0,
        })
    df = pd.DataFrame(rows)

    # ── Grouped bar: planned / completed / logged ─────────────────────────────
    st.markdown("#### Papers Planned vs Completed vs Actually Logged — per Week")
    fig = go.Figure()
    fig.add_bar(x=df["Week"], y=df["Planned"],          name="Planned",          marker_color="#94A3B8")
    fig.add_bar(x=df["Week"], y=df["Completed (plan)"], name="Completed (plan)",  marker_color="#10B981")
    fig.add_bar(x=df["Week"], y=df["Actually Logged"],  name="Actually Logged",  marker_color="#3B82F6")
    fig.update_layout(
        barmode="group", height=300, margin=dict(t=10, b=0),
        xaxis_tickangle=-30,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Completion rate line ───────────────────────────────────────────────────
    st.markdown("#### Plan Completion Rate (%) per Week")
    rate_df = df[df["Planned"] > 0]
    if not rate_df.empty:
        fig2 = go.Figure()
        fig2.add_scatter(x=rate_df["Week"], y=rate_df["Completion Rate (%)"],
                         mode="lines+markers", name="Completion %",
                         line=dict(color="#F59E0B", width=2),
                         marker=dict(size=8))
        fig2.add_hline(y=80, line_dash="dash", line_color="#10B981",
                       annotation_text="80% target", annotation_position="right")
        fig2.update_layout(height=220, margin=dict(t=10, b=0),
                           yaxis=dict(range=[0, 110]))
        st.plotly_chart(fig2, use_container_width=True)

    # ── KPI summary ───────────────────────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    avg_rate = df[df["Planned"] > 0]["Completion Rate (%)"].mean()
    best_wk  = df.loc[df["Actually Logged"].idxmax(), "Week"] if len(df) else "—"
    c1.metric("Total Planned",       int(df["Planned"].sum()))
    c2.metric("Total Completed",     int(df["Completed (plan)"].sum()))
    c3.metric("Total Logged",        int(df["Actually Logged"].sum()))
    c4.metric("Avg Completion Rate", f"{avg_rate:.0f}%" if not pd.isna(avg_rate) else "—")
    c5.metric("Most Productive Week", best_wk)

    # ── Full table ─────────────────────────────────────────────────────────────
    with st.expander("📊 Full Weekly Data Table"):
        st.dataframe(df, use_container_width=True, hide_index=True)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, sheet_name="Velocity", index=False)
        st.download_button(
            "📥 Export Velocity Data (.xlsx)",
            data=buf.getvalue(),
            file_name="litflow_velocity.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ── Main entry ────────────────────────────────────────────────────────────────

def show_reading_plan():
    st.markdown('<div class="lf-title">📅 Reading Plan</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lf-sub">Plan weekly literature, track Plan vs Actual, and monitor reading velocity</div>',
        unsafe_allow_html=True,
    )

    t1, t2, t3, t4 = st.tabs([
        "📅 Weekly Planner",
        "✅ Plan vs Actual",
        "🗓️ Monthly Map",
        "📈 Reading Velocity",
    ])
    with t1: _weekly_planner()
    with t2: _plan_vs_actual()
    with t3: _monthly_map()
    with t4: _reading_velocity()
