from datetime import date

import streamlit as st

import database as db

METHODOLOGIES = [
    "Select...",
    "Quantitative",
    "Qualitative",
    "Mixed Methods",
    "Systematic Review",
    "Meta-Analysis",
    "Case Study",
    "Experimental",
    "Survey",
    "Theoretical / Conceptual",
    "Computational",
]

STATUSES = ["To Read", "Reading", "Completed"]


def show_paper_entry(edit_paper: dict | None = None):
    is_edit = edit_paper is not None

    if is_edit:
        st.markdown('<div class="lf-title">✏️ Edit Paper</div>', unsafe_allow_html=True)
        st.markdown('<div class="lf-sub">Update the analytical record for this paper</div>',
                    unsafe_allow_html=True)
        if st.button("← Back to Library"):
            st.session_state.pop("edit_paper_id", None)
            st.session_state["nav_page"] = "📖 Paper Library"
            st.rerun()
        st.markdown("---")
    else:
        st.markdown('<div class="lf-title">➕ Add Paper</div>', unsafe_allow_html=True)
        st.markdown('<div class="lf-sub">Encode your reading into structured research variables</div>',
                    unsafe_allow_html=True)

    form_key = f"paper_form_edit_{edit_paper['id']}" if is_edit else "paper_form_new"

    with st.form(form_key, clear_on_submit=not is_edit):

        # ── Identity ─────────────────────────────────────────────────────────
        st.markdown('<div class="lf-section">📄 Paper Identity</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            title = st.text_input(
                "Title *",
                value=edit_paper.get("title", "") if is_edit else "",
                placeholder="Full paper title",
            )
        with col2:
            year_val = int(edit_paper["year"]) if is_edit and edit_paper.get("year") else date.today().year
            year = st.number_input("Year", min_value=1900, max_value=2035,
                                   value=year_val, step=1)

        authors = st.text_input(
            "Authors",
            value=edit_paper.get("authors", "") if is_edit else "",
            placeholder="e.g. Smith, J., Jones, A.",
        )

        # ── Research details ─────────────────────────────────────────────────
        st.markdown('<div class="lf-section">🎯 Research Details</div>', unsafe_allow_html=True)
        aim = st.text_area(
            "Aim / Purpose",
            value=edit_paper.get("aim", "") if is_edit else "",
            height=80,
            placeholder="What is the main objective of this study?",
        )
        research_questions = st.text_area(
            "Research Questions",
            value=edit_paper.get("research_questions", "") if is_edit else "",
            height=80,
            placeholder="Explicit or inferred research questions",
        )
        data_used = st.text_input(
            "Data / Dataset Used",
            value=edit_paper.get("data_used", "") if is_edit else "",
            placeholder="e.g. Survey of 500 SMEs, CRSP panel data, ImageNet",
        )

        # ── Methodology ──────────────────────────────────────────────────────
        st.markdown('<div class="lf-section">🔬 Methodology & Techniques</div>', unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            current_method = edit_paper.get("methodology", "Select...") if is_edit else "Select..."
            method_opts = METHODOLOGIES[:]
            if current_method and current_method not in method_opts:
                method_opts.append(current_method)
            methodology = st.selectbox(
                "Methodology",
                method_opts,
                index=method_opts.index(current_method) if current_method in method_opts else 0,
            )
        with col4:
            current_status = edit_paper.get("status", "To Read") if is_edit else "To Read"
            status = st.selectbox(
                "Status",
                STATUSES,
                index=STATUSES.index(current_status) if current_status in STATUSES else 0,
            )

        techniques = st.text_input(
            "Analytical Techniques",
            value=edit_paper.get("techniques", "") if is_edit else "",
            placeholder="e.g. SEM, Regression, CNN, Thematic Analysis  (comma-separated)",
        )

        # ── Findings & insights ───────────────────────────────────────────────
        st.markdown('<div class="lf-section">💡 Findings & Insights</div>', unsafe_allow_html=True)
        findings = st.text_area(
            "Key Findings",
            value=edit_paper.get("findings", "") if is_edit else "",
            height=100,
            placeholder="What did the study find?",
        )
        key_insights = st.text_area(
            "Your Key Insights ✨",
            value=edit_paper.get("key_insights", "") if is_edit else "",
            height=100,
            placeholder="Your distilled understanding — what this means for your own research",
        )
        reflection = st.text_area(
            "Critical Reflection",
            value=edit_paper.get("reflection", "") if is_edit else "",
            height=80,
            placeholder="Strengths, limitations, contradictions with other papers, methodological notes",
        )

        # ── Tags & metadata ───────────────────────────────────────────────────
        st.markdown('<div class="lf-section">🏷️ Tags & Metadata</div>', unsafe_allow_html=True)
        tags = st.text_input(
            "Tags",
            value=edit_paper.get("tags", "") if is_edit else "",
            placeholder="e.g. TAM, XAI, Supply Chain, FinTech  (comma-separated)",
        )
        if not is_edit:
            date_added = st.date_input("Date Added", value=date.today())

        st.markdown("---")
        submitted = st.form_submit_button(
            "💾 Update Paper" if is_edit else "➕ Add Paper",
            type="primary",
            use_container_width=False,
        )

    if submitted:
        if not title.strip():
            st.error("Title is required!")
            return

        data = dict(
            title             = title.strip(),
            authors           = authors.strip(),
            year              = int(year),
            aim               = aim.strip(),
            research_questions= research_questions.strip(),
            data_used         = data_used.strip(),
            methodology       = methodology if methodology != "Select..." else "",
            techniques        = techniques.strip(),
            findings          = findings.strip(),
            key_insights      = key_insights.strip(),
            reflection        = reflection.strip(),
            status            = status,
            tags              = tags.strip(),
        )

        if is_edit:
            db.update_paper(edit_paper["id"], data)
            st.success(f"✅ **{title}** updated successfully!")
            st.session_state.pop("edit_paper_id", None)
            if st.button("← Return to Library"):
                st.session_state["nav_page"] = "📖 Paper Library"
                st.rerun()
        else:
            data["date_added"] = date_added.strftime("%Y-%m-%d")
            pid = db.add_paper(data)
            st.success(f"✅ Paper added! (ID {pid})")
            st.balloons()
