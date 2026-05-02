from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db

EXPECTED_METHODS = {
    "Quantitative", "Qualitative", "Mixed Methods",
    "Experimental", "Systematic Review", "Case Study",
}


def show_gap_analysis():
    st.markdown('<div class="lf-title">📊 Gap Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lf-sub">Identify methodological dominance, thematic clusters, and underexplored areas</div>',
        unsafe_allow_html=True,
    )

    papers = db.get_all_papers()
    if not papers:
        st.info("Add papers to generate gap analysis.")
        return

    methods   = [p["methodology"] for p in papers if p.get("methodology")]
    all_techs = []
    all_tags  = []
    for p in papers:
        if p.get("techniques"):
            all_techs.extend(t.strip() for t in p["techniques"].split(",") if t.strip())
        if p.get("tags"):
            all_tags.extend(t.strip() for t in p["tags"].split(",") if t.strip())
    years = [p["year"] for p in papers if p.get("year")]

    # ── Methodology ───────────────────────────────────────────────────────────
    st.markdown("### 🔬 Methodology Distribution")
    if methods:
        mc  = Counter(methods)
        mdf = pd.DataFrame(mc.most_common(), columns=["Methodology", "Count"])
        mdf["Share (%)"] = (mdf["Count"] / len(methods) * 100).round(1)

        c1, c2 = st.columns([2, 1])
        with c1:
            fig = px.bar(mdf, x="Count", y="Methodology", orientation="h",
                         color="Count", color_continuous_scale="Blues", text="Count")
            fig.update_layout(height=300, coloraxis_showscale=False,
                              yaxis={"categoryorder": "total ascending"},
                              margin=dict(t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.dataframe(mdf, use_container_width=True, hide_index=True)

        dom     = mc.most_common(1)[0]
        missing = sorted(EXPECTED_METHODS - set(methods))
        st.markdown("#### 💡 Methodology Gap Hints")
        st.warning(
            f"**Dominant approach:** {dom[0]} "
            f"({dom[1]} papers, {round(dom[1]/len(methods)*100)}% of total)"
        )
        if missing:
            st.info(f"**Underrepresented / absent approaches:** {', '.join(missing)}")
        if not mc.get("Qualitative") and mc.get("Quantitative"):
            st.markdown(
                "- No qualitative studies — subjective and contextual factors "
                "may be underexplored."
            )
        if not mc.get("Experimental"):
            st.markdown("- No experimental studies — causal claims may be observational only.")
        if not mc.get("Systematic Review") and not mc.get("Meta-Analysis"):
            st.markdown("- No systematic reviews — check whether meta-analyses exist in this domain.")
    else:
        st.info("Add methodology to papers to see distribution.")

    # ── Techniques ────────────────────────────────────────────────────────────
    st.markdown("### ⚙️ Technique Frequency")
    if all_techs:
        tc  = Counter(all_techs)
        tdf = pd.DataFrame(tc.most_common(15), columns=["Technique", "Count"])
        fig2 = px.bar(tdf, x="Technique", y="Count", color="Count",
                      color_continuous_scale="Purples", text="Count")
        fig2.update_layout(height=280, coloraxis_showscale=False,
                           xaxis_tickangle=-30, margin=dict(t=0, b=0))
        st.plotly_chart(fig2, use_container_width=True)

        dom_tech  = tc.most_common(1)[0]
        rare_techs = [t for t, c in tc.items() if c == 1]
        st.markdown("#### 💡 Technique Gap Hints")
        st.warning(f"**Most-used technique:** {dom_tech[0]} ({dom_tech[1]} papers)")
        if rare_techs:
            st.info(
                f"**Used only once:** {', '.join(rare_techs[:8])} — "
                "potentially underexplored analytical approaches."
            )
    else:
        st.info("Add techniques to papers to see distribution.")

    # ── Tag co-occurrence ─────────────────────────────────────────────────────
    st.markdown("### 🏷️ Tag Co-occurrence  (Thematic Clusters)")
    if all_tags:
        co: dict[tuple, int] = {}
        for p in papers:
            if p.get("tags"):
                pt = [t.strip() for t in p["tags"].split(",") if t.strip()]
                for i, t1 in enumerate(pt):
                    for t2 in pt[i + 1:]:
                        key = tuple(sorted([t1, t2]))
                        co[key] = co.get(key, 0) + 1

        if co:
            co_rows = sorted(co.items(), key=lambda x: -x[1])[:15]
            co_df   = pd.DataFrame(
                [(f"{a} + {b}", n) for (a, b), n in co_rows],
                columns=["Tag Pair", "Co-occurrences"],
            )
            c1, c2 = st.columns([2, 1])
            with c1:
                fig3 = px.bar(co_df, x="Co-occurrences", y="Tag Pair", orientation="h",
                              color="Co-occurrences", color_continuous_scale="Oranges")
                fig3.update_layout(height=350, coloraxis_showscale=False,
                                   yaxis={"categoryorder": "total ascending"},
                                   margin=dict(t=0, b=0))
                st.plotly_chart(fig3, use_container_width=True)
            with c2:
                st.dataframe(co_df, use_container_width=True, hide_index=True)

            top = co_df.iloc[0]
            st.info(
                f"💡 Strongest thematic link: **{top['Tag Pair']}** "
                f"({int(top['Co-occurrences'])}× co-occurrence) — "
                "central cluster in your literature."
            )
    else:
        st.info("Add tags to papers to see co-occurrence analysis.")

    # ── Temporal coverage ─────────────────────────────────────────────────────
    if years:
        st.markdown("### 📅 Temporal Coverage")
        yc  = Counter(years)
        ydf = pd.DataFrame(sorted(yc.items()), columns=["Year", "Papers"])
        fig4 = px.line(ydf, x="Year", y="Papers", markers=True,
                       color_discrete_sequence=["#3B82F6"])
        fig4.update_layout(height=220, margin=dict(t=0, b=0))
        st.plotly_chart(fig4, use_container_width=True)

        min_y, max_y    = min(years), max(years)
        missing_years   = sorted(set(range(min_y, max_y + 1)) - set(years))
        if missing_years and len(missing_years) <= 6:
            st.info(
                f"📅 Missing years in range: {', '.join(str(y) for y in missing_years)} — "
                "check whether relevant papers exist from these periods."
            )
        recent_count = sum(1 for y in years if y >= max_y - 2)
        if recent_count < 3:
            st.warning(
                f"Only {recent_count} paper(s) from {max_y - 2}–{max_y} — "
                "literature review may lack recent developments."
            )

    # ── Summary ───────────────────────────────────────────────────────────────
    st.markdown("### 📋 Overall Gap Summary")
    summary = []
    if methods:
        mc2 = Counter(methods)
        d   = mc2.most_common(1)[0]
        if d[1] / len(methods) > 0.6:
            summary.append(
                f"Most studies use **{d[0]}** ({d[1]}/{len(methods)} papers) — "
                "limited methodological diversity."
            )
        if not mc2.get("Experimental"):
            summary.append(
                "No experimental designs — causal relationships may be inferred rather than established."
            )
    if all_techs:
        tc2 = Counter(all_techs)
        summary.append(
            f"**{tc2.most_common(1)[0][0]}** dominates analytical techniques — "
            "results may be technique-dependent."
        )
    if not summary:
        summary.append(
            "No significant gaps identified yet — add more papers with methodology "
            "and technique fields for deeper analysis."
        )
    for item in summary:
        st.markdown(f"- {item}")
