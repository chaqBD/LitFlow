import streamlit as st

import database as db

STATUS_ICON = {"Completed": "🟢", "Reading": "🟡", "To Read": "⚪"}


def show_paper_library():
    st.markdown('<div class="lf-title">📖 Paper Library</div>', unsafe_allow_html=True)
    st.markdown('<div class="lf-sub">Browse, search, edit and manage your literature database</div>',
                unsafe_allow_html=True)

    papers = db.get_all_papers()
    if not papers:
        st.info("No papers yet — use **➕ Add Paper** to get started!")
        return

    # ── Search & filter bar ───────────────────────────────────────────────────
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search = st.text_input("🔍 Search", placeholder="title, author, tag…")
    with col2:
        status_f = st.selectbox("Status", ["All", "To Read", "Reading", "Completed"])
    with col3:
        sort_by = st.selectbox("Sort", ["Recent", "Year ↓", "Title A–Z"])

    filtered = papers
    if search:
        q = search.lower()
        filtered = [
            p for p in filtered
            if q in (p.get("title") or "").lower()
            or q in (p.get("authors") or "").lower()
            or q in (p.get("tags") or "").lower()
            or q in (p.get("techniques") or "").lower()
        ]
    if status_f != "All":
        filtered = [p for p in filtered if p["status"] == status_f]

    if sort_by == "Year ↓":
        filtered = sorted(filtered, key=lambda x: x.get("year") or 0, reverse=True)
    elif sort_by == "Title A–Z":
        filtered = sorted(filtered, key=lambda x: (x.get("title") or "").lower())

    st.markdown(f"**{len(filtered)}** of **{len(papers)}** papers")
    st.markdown("---")

    # ── Paper cards ───────────────────────────────────────────────────────────
    for p in filtered:
        pid  = p["id"]
        icon = STATUS_ICON.get(p["status"], "⚪")
        year_str = str(p["year"]) if p.get("year") else "n.d."

        with st.expander(f"{icon} **{p['title']}** — {p.get('authors') or 'Unknown'}, {year_str}"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Status:** {p['status']}")
                st.markdown(f"**Methodology:** {p.get('methodology') or '—'}")
                st.markdown(f"**Techniques:** {p.get('techniques') or '—'}")
                st.markdown(f"**Data Used:** {p.get('data_used') or '—'}")
            with col_b:
                st.markdown(f"**Date Added:** {p.get('date_added') or '—'}")
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

            st.markdown("")
            col_edit, col_del, _ = st.columns([1, 1, 5])
            with col_edit:
                if st.button("✏️ Edit", key=f"edit_{pid}"):
                    st.session_state["edit_paper_id"] = pid
                    st.session_state["nav_page"]      = "➕ Add Paper"
                    st.rerun()

            with col_del:
                if st.button("🗑️ Delete", key=f"del_{pid}"):
                    st.session_state[f"confirm_del_{pid}"] = True

            if st.session_state.get(f"confirm_del_{pid}"):
                st.warning(f"Permanently delete **{p['title']}**? This cannot be undone.")
                c_yes, c_no, _ = st.columns([1, 1, 5])
                with c_yes:
                    if st.button("Yes, delete", key=f"yes_{pid}", type="primary"):
                        db.delete_paper(pid)
                        st.session_state.pop(f"confirm_del_{pid}", None)
                        st.rerun()
                with c_no:
                    if st.button("Cancel", key=f"no_{pid}"):
                        st.session_state.pop(f"confirm_del_{pid}", None)
                        st.rerun()
