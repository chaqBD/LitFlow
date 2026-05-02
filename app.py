import streamlit as st
import database as db

db.init_db()

st.set_page_config(
    page_title="LitFlow — Research Reading System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar dark theme */
[data-testid="stSidebar"] { background: #0F172A; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #CBD5E1 !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 2px; }

/* Page titles */
.lf-title  { font-size:2rem; font-weight:800; color:#0F172A; line-height:1.2; }
.lf-sub    { color:#64748B; font-size:0.95rem; margin-bottom:1.5rem; margin-top:4px; }

/* Cards */
.lf-card {
    background:white; border:1px solid #E2E8F0;
    border-radius:12px; padding:1.25rem;
    border-left:4px solid #3B82F6;
    margin-bottom:0.75rem;
}

/* Tag chips */
.lf-tag {
    background:#EFF6FF; color:#1D4ED8;
    border-radius:20px; padding:2px 10px;
    font-size:0.78rem; margin:2px; display:inline-block;
}
.lf-tag-green  { background:#D1FAE5; color:#065F46; }
.lf-tag-amber  { background:#FEF3C7; color:#92400E; }
.lf-tag-slate  { background:#F1F5F9; color:#475569; }

/* Section headers */
.lf-section {
    font-size:1.1rem; font-weight:700; color:#0F172A;
    border-bottom:2px solid #3B82F6; padding-bottom:6px;
    margin:1.5rem 0 0.75rem;
}
/* Insight highlight */
.lf-insight {
    background:#F0FDF4; border-left:3px solid #10B981;
    padding:0.75rem 1rem; border-radius:6px;
    font-style:italic; margin:0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📚 LitFlow")
    st.caption("Research Reading & Insight System")
    st.markdown("---")

    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "🏠 Dashboard"

    page = st.radio(
        "nav",
        options=[
            "🏠 Dashboard",
            "➕ Add Paper",
            "📖 Paper Library",
            "🔍 Insight Explorer",
            "📝 Weekly Diary",
            "🧩 Argument Builder",
            "📊 Gap Analysis",
            "📤 Export",
        ],
        key="nav_page",
        label_visibility="collapsed",
    )

    st.markdown("---")
    papers = db.get_all_papers()
    total     = len(papers)
    completed = sum(1 for p in papers if p["status"] == "Completed")
    reading   = sum(1 for p in papers if p["status"] == "Reading")
    to_read   = sum(1 for p in papers if p["status"] == "To Read")
    st.markdown("**Quick Stats**")
    st.markdown(f"Total: **{total}** &nbsp;|&nbsp; ✅ **{completed}** &nbsp;|&nbsp; 📖 **{reading}** &nbsp;|&nbsp; 🔖 **{to_read}**")

# ── Page routing ─────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    from modules.dashboard import show_dashboard
    show_dashboard()

elif page == "➕ Add Paper":
    from modules.paper_entry import show_paper_entry
    edit_id    = st.session_state.get("edit_paper_id")
    edit_paper = db.get_paper(edit_id) if edit_id else None
    show_paper_entry(edit_paper=edit_paper)

elif page == "📖 Paper Library":
    from modules.paper_library import show_paper_library
    show_paper_library()

elif page == "🔍 Insight Explorer":
    from modules.insight_explorer import show_insight_explorer
    show_insight_explorer()

elif page == "📝 Weekly Diary":
    from modules.weekly_diary import show_weekly_diary
    show_weekly_diary()

elif page == "🧩 Argument Builder":
    from modules.argument_builder import show_argument_builder
    show_argument_builder()

elif page == "📊 Gap Analysis":
    from modules.gap_analysis import show_gap_analysis
    show_gap_analysis()

elif page == "📤 Export":
    from modules.export_module import show_export
    show_export()
