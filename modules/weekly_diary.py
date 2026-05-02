from collections import Counter
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def show_weekly_diary():
    st.markdown('<div class="lf-title">📝 Weekly Diary</div>', unsafe_allow_html=True)
    st.markdown('<div class="lf-sub">Track your reading progress and research reflections week by week</div>',
                unsafe_allow_html=True)

    tab_write, tab_history = st.tabs(["✍️ Write Entry", "📅 History"])

    # ── Write entry ───────────────────────────────────────────────────────────
    with tab_write:
        raw_date = st.date_input("Select week (any day — snaps to Monday)",
                                 value=_monday(date.today()))
        week_start = _monday(raw_date)
        week_end   = week_start + timedelta(days=6)
        week_str   = week_start.strftime("%Y-%m-%d")

        st.markdown(
            f"**Week: {week_start.strftime('%B %d')} – {week_end.strftime('%B %d, %Y')}**"
        )

        # Auto-populate from papers logged this week
        week_papers = db.get_papers_in_week(week_str)
        auto_count  = len(week_papers)

        auto_tags, auto_methods = [], []
        for p in week_papers:
            if p.get("tags"):
                auto_tags.extend(t.strip() for t in p["tags"].split(",") if t.strip())
            if p.get("methodology"):
                auto_methods.append(p["methodology"])

        if week_papers:
            top_tags_list = [t for t, _ in Counter(auto_tags).most_common(3)]
            st.info(
                f"📊 Auto-detected this week: **{auto_count}** paper(s) logged"
                + (f" | Tags: {', '.join(top_tags_list)}" if top_tags_list else "")
                + (f" | Methods: {', '.join(set(auto_methods))}" if auto_methods else "")
            )

        existing = db.get_diary_by_week(week_str)

        auto_themes_str = ", ".join(
            t for t, _ in Counter(auto_tags).most_common(5)
        )

        with st.form("diary_form"):
            papers_count = st.number_input(
                "Papers Read / Added This Week",
                min_value=0,
                value=existing["papers_read"] if existing else auto_count,
                help="Auto-populated from logged papers. Edit if needed.",
            )
            key_themes = st.text_area(
                "Key Themes Emerging",
                value=existing["key_themes"] if existing else auto_themes_str,
                height=80,
                placeholder="Recurring themes, theoretical lenses, keywords you keep seeing…",
            )
            new_ideas = st.text_area(
                "New Ideas Generated",
                value=existing["new_ideas"] if existing else "",
                height=80,
                placeholder="Hypotheses, connections, potential research directions sparked by reading…",
            )
            challenges = st.text_area(
                "Conceptual / Methodological Challenges",
                value=existing["challenges"] if existing else "",
                height=80,
                placeholder="Concepts that are unclear, methodological questions, contradictions noticed…",
            )
            next_steps = st.text_area(
                "Next Steps",
                value=existing["next_steps"] if existing else "",
                height=80,
                placeholder="Papers to read next, gaps to address, arguments to develop…",
            )
            submitted = st.form_submit_button("💾 Save Diary Entry", type="primary")

        if submitted:
            db.add_or_update_diary(dict(
                week_start   = week_str,
                papers_read  = int(papers_count),
                key_themes   = key_themes,
                new_ideas    = new_ideas,
                challenges   = challenges,
                next_steps   = next_steps,
            ))
            st.success(f"✅ Diary saved for week of {week_start.strftime('%B %d, %Y')}!")

    # ── History ───────────────────────────────────────────────────────────────
    with tab_history:
        diary = db.get_all_diary()
        if not diary:
            st.info("No diary entries yet.")
            return

        df_d = pd.DataFrame(diary).sort_values("week_start")
        fig  = px.bar(df_d, x="week_start", y="papers_read",
                      color="papers_read", color_continuous_scale="Blues",
                      text="papers_read", title="Papers per Week")
        fig.update_layout(height=250, coloraxis_showscale=False,
                          xaxis_tickangle=-30, margin=dict(t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        for entry in diary:
            dt    = datetime.strptime(entry["week_start"], "%Y-%m-%d")
            label = dt.strftime("%B %d, %Y")
            with st.expander(f"📅 Week of {label}  —  {entry['papers_read']} papers"):
                c1, c2 = st.columns(2)
                with c1:
                    if entry.get("key_themes"):
                        st.markdown(f"**Themes:** {entry['key_themes']}")
                    if entry.get("challenges"):
                        st.markdown(f"**Challenges:** {entry['challenges']}")
                with c2:
                    if entry.get("new_ideas"):
                        st.markdown(f"**New Ideas:** {entry['new_ideas']}")
                    if entry.get("next_steps"):
                        st.markdown(f"**Next Steps:** {entry['next_steps']}")
