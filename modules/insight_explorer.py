from collections import Counter

import streamlit as st

import database as db


def show_insight_explorer():
    st.markdown('<div class="lf-title">🔍 Insight Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="lf-sub">Filter your literature and surface patterns across papers</div>',
                unsafe_allow_html=True)

    papers = db.get_all_papers()
    if not papers:
        st.info("Add papers first to explore insights.")
        return

    methodologies = sorted({p["methodology"] for p in papers if p.get("methodology")})
    all_tags, all_techs = [], []
    for p in papers:
        if p.get("tags"):
            all_tags.extend(t.strip() for t in p["tags"].split(",") if t.strip())
        if p.get("techniques"):
            all_techs.extend(t.strip() for t in p["techniques"].split(",") if t.strip())

    unique_tags  = sorted(set(all_tags))
    unique_techs = sorted(set(all_techs))
    years        = sorted({p["year"] for p in papers if p.get("year")})

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown("#### Filters")
    c1, c2, c3, c4 = st.columns(4)
    sel_method = c1.selectbox("Methodology", ["All"] + methodologies)
    sel_tech   = c2.selectbox("Technique",   ["All"] + unique_techs)
    sel_tag    = c3.selectbox("Tag",         ["All"] + unique_tags)
    sel_status = c4.selectbox("Status",      ["All", "To Read", "Reading", "Completed"])

    c5, c6 = st.columns(2)
    year_strs = ["Any"] + [str(y) for y in years]
    year_from = c5.selectbox("Year From", year_strs)
    year_to   = c6.selectbox("Year To",   ["Any"] + [str(y) for y in reversed(years)])

    filtered = db.get_papers_filtered(
        methodology = sel_method if sel_method != "All" else None,
        technique   = sel_tech   if sel_tech   != "All" else None,
        tag         = sel_tag    if sel_tag     != "All" else None,
        status      = sel_status if sel_status  != "All" else None,
        year_from   = int(year_from) if year_from != "Any" else None,
        year_to     = int(year_to)   if year_to   != "Any" else None,
    )

    st.markdown("---")

    if not filtered:
        st.warning("No papers match the selected filters.")
        return

    # ── Summary strip ─────────────────────────────────────────────────────────
    c_a, c_b, c_c = st.columns(3)
    c_a.metric("Papers Found", len(filtered))

    m_counts = Counter(p["methodology"] for p in filtered if p.get("methodology"))
    c_b.metric("Dominant Method", m_counts.most_common(1)[0][0] if m_counts else "—")

    f_tags = []
    for p in filtered:
        if p.get("tags"):
            f_tags.extend(t.strip() for t in p["tags"].split(",") if t.strip())
    c_c.metric("Top Tag", Counter(f_tags).most_common(1)[0][0] if f_tags else "—")

    active = []
    if sel_method != "All": active.append(f"methodology = {sel_method}")
    if sel_tech   != "All": active.append(f"technique = {sel_tech}")
    if sel_tag    != "All": active.append(f"tag = {sel_tag}")
    if sel_status != "All": active.append(f"status = {sel_status}")
    if year_from  != "Any": active.append(f"from {year_from}")
    if year_to    != "Any": active.append(f"to {year_to}")
    if active:
        st.info("🔎 " + "  |  ".join(active))

    st.markdown("---")

    # ── Paper cards ───────────────────────────────────────────────────────────
    for p in filtered:
        year_str = str(p["year"]) if p.get("year") else "n.d."
        with st.expander(f"**{p['title']}** — {p.get('authors') or ''}, {year_str}"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Methodology:** {p.get('methodology') or '—'}")
                st.markdown(f"**Techniques:** {p.get('techniques') or '—'}")
                st.markdown(f"**Status:** {p['status']}")
            with c2:
                raw_tags = p.get("tags", "")
                if raw_tags:
                    chips = " ".join(
                        f'<span class="lf-tag">{t.strip()}</span>'
                        for t in raw_tags.split(",") if t.strip()
                    )
                    st.markdown(f"**Tags:** {chips}", unsafe_allow_html=True)

            if p.get("aim"):
                st.markdown(f"**Aim:** {p['aim']}")
            if p.get("research_questions"):
                st.markdown(f"**RQs:** {p['research_questions']}")
            if p.get("findings"):
                st.markdown(f"**Findings:** {p['findings']}")
            if p.get("key_insights"):
                st.markdown(
                    f'<div class="lf-insight">💡 {p["key_insights"]}</div>',
                    unsafe_allow_html=True,
                )
            if p.get("reflection"):
                st.markdown(f"**Reflection:** {p['reflection']}")
