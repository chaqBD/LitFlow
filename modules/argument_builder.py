import datetime
from collections import Counter

import streamlit as st

import database as db

ALL_METHODS = {
    "Quantitative", "Qualitative", "Mixed Methods",
    "Experimental", "Systematic Review", "Case Study", "Survey",
}


def _analyse(papers: list[dict]) -> dict:
    # Common tags
    all_tags = []
    for p in papers:
        if p.get("tags"):
            all_tags.extend(t.strip() for t in p["tags"].split(",") if t.strip())
    tag_counts    = Counter(all_tags)
    common_themes = [t for t, c in tag_counts.most_common() if c >= 2]

    # Methodology profile
    methods      = [p["methodology"] for p in papers if p.get("methodology")]
    method_counts = Counter(methods)
    dominant_method = method_counts.most_common(1)[0][0] if methods else None

    # Techniques
    all_techs = []
    for p in papers:
        if p.get("techniques"):
            all_techs.extend(t.strip() for t in p["techniques"].split(",") if t.strip())
    tech_counts      = Counter(all_techs)
    common_techniques = [t for t, c in tech_counts.most_common() if c >= 2]

    # Agreement / tension pairs
    agreement_pairs    = []
    contradiction_pairs = []
    for i, p1 in enumerate(papers):
        for p2 in papers[i + 1:]:
            t1 = {t.strip() for t in (p1.get("tags") or "").split(",") if t.strip()}
            t2 = {t.strip() for t in (p2.get("tags") or "").split(",") if t.strip()}
            shared = t1 & t2
            if shared and p1.get("methodology") == p2.get("methodology"):
                agreement_pairs.append((p1["title"][:45], p2["title"][:45], list(shared)[:3]))
            elif shared and p1.get("methodology") != p2.get("methodology"):
                contradiction_pairs.append((
                    p1["title"][:45], p2["title"][:45],
                    p1.get("methodology") or "?", p2.get("methodology") or "?",
                ))

    # Year coverage
    years     = sorted(p["year"] for p in papers if p.get("year"))
    year_note = None
    if len(years) >= 2 and (years[-1] - years[0]) < 5:
        year_note = (f"Papers span only {years[-1] - years[0]} years "
                     f"({years[0]}–{years[-1]}) — consider adding older foundational work.")

    missing_methods = sorted(ALL_METHODS - set(methods))

    return dict(
        common_themes       = common_themes,
        dominant_method     = dominant_method,
        method_counts       = dict(method_counts),
        method_variety      = len(set(methods)),
        common_techniques   = common_techniques,
        all_techniques      = dict(tech_counts),
        agreement_pairs     = agreement_pairs,
        contradiction_pairs = contradiction_pairs,
        missing_methods     = missing_methods,
        year_note           = year_note,
        years               = years,
    )


def show_argument_builder():
    st.markdown('<div class="lf-title">🧩 Argument Builder</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lf-sub">Select 2–6 papers to synthesize themes, agreements, contradictions, and gaps</div>',
        unsafe_allow_html=True,
    )

    papers = db.get_all_papers()
    if len(papers) < 2:
        st.info("Add at least 2 papers to use the Argument Builder.")
        return

    options = {
        f"{p['title']} ({p.get('authors', '')} {p.get('year', '')})": p
        for p in papers
    }

    selected_titles = st.multiselect(
        "Select Papers to Analyse  (2–6 recommended)",
        list(options.keys()),
        help="Choose papers whose arguments you want to compare and synthesize.",
    )

    if len(selected_titles) < 2:
        st.info("Select at least 2 papers to begin.")
        return

    selected = [options[t] for t in selected_titles]

    if not st.button("🧩 Build Argument", type="primary"):
        return

    r = _analyse(selected)

    st.markdown("---")
    st.markdown("## Synthesis Report")
    st.caption(f"Based on {len(selected)} selected papers")

    # ── Common themes ─────────────────────────────────────────────────────────
    st.markdown("### 🎯 Common Themes")
    if r["common_themes"]:
        chips = " ".join(
            f'<span class="lf-tag">{t}</span>' for t in r["common_themes"]
        )
        st.markdown(f"Shared across ≥ 2 papers: {chips}", unsafe_allow_html=True)
    else:
        st.markdown(
            "No shared tags found. Papers may cover distinct phenomena — "
            "verify they address the same research domain before building a joint argument."
        )

    # ── Methodological profile ────────────────────────────────────────────────
    st.markdown("### 🔬 Methodological Profile")
    c1, c2 = st.columns(2)
    with c1:
        if r["method_counts"]:
            for m, n in r["method_counts"].items():
                st.markdown(f"- **{m}**: {n} paper(s)")
        else:
            st.markdown("No methodologies recorded.")
    with c2:
        if r["common_techniques"]:
            st.markdown("**Shared Techniques:**")
            for t in r["common_techniques"]:
                st.markdown(f"- {t}")
        unique_techs = [t for t, c in r["all_techniques"].items() if c == 1]
        if unique_techs:
            st.markdown(f"**Unique techniques:** {', '.join(unique_techs[:6])}")

    if r["method_variety"] == 1 and r["dominant_method"]:
        st.info(
            f"All selected papers use **{r['dominant_method']}** — methodologically homogeneous. "
            "Consider including contrasting approaches for a triangulated argument."
        )
    elif r["method_variety"] >= 3:
        st.success(
            f"Methodological diversity across **{r['method_variety']}** approaches — "
            "strong foundation for a multi-perspective argument."
        )

    # ── Agreement ─────────────────────────────────────────────────────────────
    st.markdown("### ✅ Agreement Indicators")
    if r["agreement_pairs"]:
        for p1, p2, shared in r["agreement_pairs"]:
            st.markdown(
                f"- **{p1}** and **{p2}** share methodology and tags "
                f"*{', '.join(shared)}* — likely converging evidence."
            )
    else:
        st.markdown("No direct methodological agreements detected among selected papers.")

    # ── Tensions ──────────────────────────────────────────────────────────────
    st.markdown("### ⚡ Potential Tensions / Contradictions")
    if r["contradiction_pairs"]:
        for p1, p2, m1, m2 in r["contradiction_pairs"]:
            st.markdown(
                f"- **{p1}** ({m1}) vs **{p2}** ({m2}) — same topic, different methods. "
                "Results may not be directly comparable; explore why they diverge."
            )
    else:
        st.markdown("No methodological tensions detected among selected papers.")

    # ── Gaps ──────────────────────────────────────────────────────────────────
    st.markdown("### 🔭 Gaps in Selected Literature")
    gaps = []
    if r["missing_methods"]:
        gaps.append(f"**Missing perspectives:** {', '.join(r['missing_methods'][:4])}")
    if r["year_note"]:
        gaps.append(r["year_note"])
    if r["method_variety"] == 1:
        gaps.append("All papers use one methodology — risk of methodological bias.")
    if not r["common_themes"]:
        gaps.append("No shared themes — papers may not form a coherent literature stream.")

    if gaps:
        for g in gaps:
            st.markdown(f"- {g}")
    else:
        st.success("Selected papers appear balanced and coherent.")

    # ── Suggested argument frame ───────────────────────────────────────────────
    st.markdown("### 📝 Suggested Argument Frame")
    themes_str = ", ".join(r["common_themes"][:3]) if r["common_themes"] else "this domain"
    dom        = r["dominant_method"] or "mixed"
    agreement_note = (
        f"Papers show convergence on {r['agreement_pairs'][0][2][0]}. "
        if r["agreement_pairs"] else ""
    )
    gap_note = (
        f"Key methodological gaps include {', '.join(r['missing_methods'][:2])} approaches."
        if r["missing_methods"] else ""
    )
    st.info(
        f"**Draft:** The literature on *{themes_str}* is primarily approached through "
        f"{dom} methods. {agreement_note}"
        + (f"Diversity across {', '.join(r['method_counts'].keys())} suggests ongoing debate "
           f"about appropriate analytical frameworks. " if r["method_variety"] > 1 else "")
        + gap_note
    )

    # ── Export report ─────────────────────────────────────────────────────────
    st.markdown("---")
    lines = [
        "ARGUMENT BUILDER REPORT",
        f"Generated: {datetime.date.today()}",
        "",
        "SELECTED PAPERS:",
        *[f"  - {t}" for t in selected_titles],
        "",
        f"COMMON THEMES: {', '.join(r['common_themes']) or 'None'}",
        "",
        "METHODOLOGICAL PROFILE:",
        *[f"  - {m}: {n} paper(s)" for m, n in r["method_counts"].items()],
        "",
        f"SHARED TECHNIQUES: {', '.join(r['common_techniques']) or 'None'}",
        "",
        "AGREEMENT PAIRS:",
        *(
            [f"  - {p1} & {p2} ({', '.join(s)})" for p1, p2, s in r["agreement_pairs"]]
            if r["agreement_pairs"] else ["  None"]
        ),
        "",
        "TENSIONS:",
        *(
            [f"  - {p1} ({m1}) vs {p2} ({m2})" for p1, p2, m1, m2 in r["contradiction_pairs"]]
            if r["contradiction_pairs"] else ["  None"]
        ),
        "",
        "GAPS:",
        *(["  " + g for g in gaps] if gaps else ["  None"]),
    ]
    st.download_button(
        "📥 Download Report (.txt)",
        data="\n".join(lines),
        file_name=f"litflow_argument_{datetime.date.today()}.txt",
        mime="text/plain",
    )
