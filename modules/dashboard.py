from collections import Counter
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db


# ── Helpers ──────────────────────────────────────────────────────────────────

def _week_start(d) -> str:
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d")
    return (d - timedelta(days=d.weekday())).strftime("%Y-%m-%d")


def _compute_streak(papers: list[dict]) -> int:
    weeks = set()
    for p in papers:
        if p.get("date_added"):
            try:
                weeks.add(_week_start(p["date_added"]))
            except Exception:
                pass
    if not weeks:
        return 0
    streak = 0
    check  = _week_start(date.today())
    while check in weeks:
        streak += 1
        check   = (datetime.strptime(check, "%Y-%m-%d") - timedelta(weeks=1)).strftime("%Y-%m-%d")
    return streak


def _insight_density(papers: list[dict]) -> float:
    done = [p for p in papers if p["status"] == "Completed" and p.get("key_insights")]
    if not done:
        return 0.0
    return round(sum(len(p["key_insights"]) for p in done) / len(done), 1)


# ── Main view ─────────────────────────────────────────────────────────────────

def show_dashboard():
    st.markdown('<div class="lf-title">📚 LitFlow Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="lf-sub">Your research reading at a glance</div>', unsafe_allow_html=True)

    papers = db.get_all_papers()

    if not papers:
        st.info("No papers logged yet — add your first paper to get started!")
        st.markdown("""
**Getting started:**
1. Click **➕ Add Paper** in the sidebar
2. Fill in the structured analytical fields
3. Your progress metrics will appear here automatically
""")
        return

    df = pd.DataFrame(papers)

    # ── Top KPI row ──────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    total     = len(papers)
    completed = int((df["status"] == "Completed").sum())
    reading   = int((df["status"] == "Reading").sum())
    to_read   = int((df["status"] == "To Read").sum())
    streak    = _compute_streak(papers)

    c1.metric("Total Papers",   total)
    c2.metric("Completed",      completed,
              delta=f"{round(completed / total * 100)}%" if total else None)
    c3.metric("Reading",        reading)
    c4.metric("To Read",        to_read)
    c5.metric("Reading Streak", f"{streak} wk{'s' if streak != 1 else ''}")

    st.markdown("---")

    # ── Row 1: Status donut + Methodology bar ────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### Status Distribution")
        status_df = df["status"].value_counts().reset_index()
        status_df.columns = ["Status", "Count"]
        color_map = {"Completed": "#10B981", "Reading": "#F59E0B", "To Read": "#94A3B8"}
        fig = px.pie(status_df, values="Count", names="Status",
                     color="Status", color_discrete_map=color_map, hole=0.42)
        fig.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=270, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("#### Papers by Methodology")
        mdf = df[df["methodology"].str.strip().ne("") & df["methodology"].notna()]
        if not mdf.empty:
            mc = mdf["methodology"].value_counts().head(8).reset_index()
            mc.columns = ["Methodology", "Count"]
            fig2 = px.bar(mc, x="Count", y="Methodology", orientation="h",
                          color="Count", color_continuous_scale="Blues", text="Count")
            fig2.update_layout(margin=dict(t=0, b=0), height=270,
                               coloraxis_showscale=False,
                               yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Add methodology to papers to see distribution.")

    # ── Row 2: Year bar + Techniques bar ─────────────────────────────────────
    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.markdown("#### Papers by Year")
        ydf = df[df["year"].notna()].copy()
        if not ydf.empty:
            ydf["year"] = ydf["year"].astype(int)
            yc = ydf["year"].value_counts().sort_index().reset_index()
            yc.columns = ["Year", "Count"]
            fig3 = px.bar(yc, x="Year", y="Count", color="Count",
                          color_continuous_scale="Teal", text="Count")
            fig3.update_layout(margin=dict(t=0, b=0), height=240,
                               coloraxis_showscale=False)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Add publication years to see distribution.")

    with col_r2:
        st.markdown("#### Top Techniques")
        techs = []
        for p in papers:
            if p.get("techniques"):
                techs.extend(t.strip() for t in p["techniques"].split(",") if t.strip())
        if techs:
            tc = Counter(techs).most_common(10)
            tdf = pd.DataFrame(tc, columns=["Technique", "Count"])
            fig4 = px.bar(tdf, x="Count", y="Technique", orientation="h",
                          color="Count", color_continuous_scale="Purples", text="Count")
            fig4.update_layout(margin=dict(t=0, b=0), height=240,
                               coloraxis_showscale=False,
                               yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Add techniques to papers to see distribution.")

    # ── Cumulative progress ───────────────────────────────────────────────────
    st.markdown("#### Reading Progress Over Time")
    time_df = df[df["date_added"].notna()].copy()
    if not time_df.empty:
        time_df["date_added"] = pd.to_datetime(time_df["date_added"], errors="coerce")
        time_df = time_df.dropna(subset=["date_added"]).sort_values("date_added")
        time_df["Cumulative"] = range(1, len(time_df) + 1)
        fig5 = px.area(time_df, x="date_added", y="Cumulative",
                       color_discrete_sequence=["#3B82F6"])
        fig5.update_layout(margin=dict(t=10, b=0), height=210,
                           xaxis_title="Date", yaxis_title="Cumulative Papers")
        st.plotly_chart(fig5, use_container_width=True)

    # ── Row 3: Tags + Weekly cadence ─────────────────────────────────────────
    col_l3, col_r3 = st.columns(2)

    with col_l3:
        st.markdown("#### Top Tags")
        tags = []
        for p in papers:
            if p.get("tags"):
                tags.extend(t.strip() for t in p["tags"].split(",") if t.strip())
        if tags:
            tag_df = pd.DataFrame(Counter(tags).most_common(12), columns=["Tag", "Count"])
            fig6 = px.bar(tag_df, x="Tag", y="Count", color="Count",
                          color_continuous_scale="Oranges", text="Count")
            fig6.update_layout(margin=dict(t=0, b=0), height=230,
                               coloraxis_showscale=False, xaxis_tickangle=-30)
            st.plotly_chart(fig6, use_container_width=True)

    with col_r3:
        st.markdown("#### Papers per Week (Last 8 Weeks)")
        today  = date.today()
        weeks  = [
            (today - timedelta(weeks=i) - timedelta(days=(today - timedelta(weeks=i)).weekday()))
            for i in range(7, -1, -1)
        ]
        wkeys  = [w.strftime("%Y-%m-%d") for w in weeks]
        wcount = {k: 0 for k in wkeys}
        for p in papers:
            if p.get("date_added"):
                try:
                    ws = _week_start(p["date_added"])
                    if ws in wcount:
                        wcount[ws] += 1
                except Exception:
                    pass
        wdf = pd.DataFrame(list(wcount.items()), columns=["Week", "Papers"])
        fig7 = px.bar(wdf, x="Week", y="Papers", color="Papers",
                      color_continuous_scale="Greens", text="Papers")
        fig7.update_layout(margin=dict(t=0, b=0), height=230,
                           coloraxis_showscale=False, xaxis_tickangle=-30)
        st.plotly_chart(fig7, use_container_width=True)

    # ── Insight Density ───────────────────────────────────────────────────────
    st.markdown("---")
    density = _insight_density(papers)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Insight Density Score")
        st.metric("Avg. Insight Length", f"{density} chars / paper")
        if density == 0:
            st.caption("No completed papers with insights yet.")
        elif density < 100:
            st.caption("Low — try writing deeper per-paper insights.")
        elif density < 300:
            st.caption("Moderate — good analytical engagement.")
        else:
            st.caption("High — excellent depth of analysis!")
    with col_b:
        st.markdown("#### Reading Streak")
        if streak == 0:
            st.info("No reading streak yet — log papers this week to start one!")
        else:
            st.success(f"🔥 You've been reading for **{streak} consecutive week{'s' if streak != 1 else ''}**!")
