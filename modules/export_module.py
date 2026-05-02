import io
from datetime import date

import pandas as pd
import streamlit as st

import database as db

PAPER_COLS = [
    "id", "title", "authors", "year", "status", "methodology", "techniques",
    "aim", "research_questions", "data_used", "findings",
    "key_insights", "reflection", "tags", "date_added",
]


def _papers_df(papers: list[dict]) -> pd.DataFrame:
    df   = pd.DataFrame(papers)
    cols = [c for c in PAPER_COLS if c in df.columns]
    return df[cols]


def _to_excel(df: pd.DataFrame, sheet: str = "Data") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, sheet_name=sheet, index=False)
    return buf.getvalue()


def _papers_excel(papers: list[dict]) -> bytes:
    buf = io.BytesIO()
    df  = _papers_df(papers)
    summary = pd.DataFrame({
        "Metric": ["Total", "Completed", "Reading", "To Read"],
        "Count":  [
            len(papers),
            sum(1 for p in papers if p["status"] == "Completed"),
            sum(1 for p in papers if p["status"] == "Reading"),
            sum(1 for p in papers if p["status"] == "To Read"),
        ],
    })
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="Papers", index=False)
        summary.to_excel(w, sheet_name="Summary", index=False)
    return buf.getvalue()


def show_export():
    st.markdown('<div class="lf-title">📤 Export</div>', unsafe_allow_html=True)
    st.markdown('<div class="lf-sub">Download your literature database and diary entries</div>',
                unsafe_allow_html=True)

    papers = db.get_all_papers()
    diary  = db.get_all_diary()
    today  = date.today()

    # ── Full literature database ──────────────────────────────────────────────
    st.markdown("### 📚 Literature Database")
    if papers:
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "📥 All Papers (.xlsx)",
                data=_papers_excel(papers),
                file_name=f"litflow_papers_{today}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                "📥 All Papers (.csv)",
                data=_papers_df(papers).to_csv(index=False),
                file_name=f"litflow_papers_{today}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("No papers to export yet.")

    # ── Filtered export ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔍 Filtered Export")

    if papers:
        all_tags, methodologies = [], []
        for p in papers:
            if p.get("tags"):
                all_tags.extend(t.strip() for t in p["tags"].split(",") if t.strip())
            if p.get("methodology"):
                methodologies.append(p["methodology"])

        c1, c2, c3 = st.columns(3)
        status_f = c1.selectbox("Status",      ["All", "To Read", "Reading", "Completed"],
                                key="exp_status")
        method_f = c2.selectbox("Methodology", ["All"] + sorted(set(methodologies)),
                                key="exp_method")
        tag_f    = c3.selectbox("Tag",         ["All"] + sorted(set(all_tags)),
                                key="exp_tag")

        filtered = db.get_papers_filtered(
            methodology = method_f if method_f != "All" else None,
            tag         = tag_f    if tag_f    != "All" else None,
            status      = status_f if status_f != "All" else None,
        )

        if filtered:
            st.markdown(f"**{len(filtered)} papers** match filters")
            c4, c5 = st.columns(2)
            with c4:
                st.download_button(
                    "📥 Filtered (.xlsx)",
                    data=_to_excel(_papers_df(filtered), "Filtered Papers"),
                    file_name=f"litflow_filtered_{today}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with c5:
                st.download_button(
                    "📥 Filtered (.csv)",
                    data=_papers_df(filtered).to_csv(index=False),
                    file_name=f"litflow_filtered_{today}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        else:
            st.warning("No papers match selected filters.")

    # ── Weekly diary ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📝 Weekly Diary Export")
    if diary:
        df_d = pd.DataFrame(diary)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "📥 Diary (.xlsx)",
                data=_to_excel(df_d, "Weekly Diary"),
                file_name=f"litflow_diary_{today}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                "📥 Diary (.csv)",
                data=df_d.to_csv(index=False),
                file_name=f"litflow_diary_{today}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("No diary entries to export yet.")

    # ── Preview ───────────────────────────────────────────────────────────────
    if papers:
        st.markdown("---")
        st.markdown("### 👁️ Data Preview")
        t1, t2 = st.tabs(["Papers", "Diary"])
        with t1:
            st.dataframe(_papers_df(papers), use_container_width=True)
        with t2:
            if diary:
                st.dataframe(pd.DataFrame(diary), use_container_width=True)
            else:
                st.info("No diary entries yet.")
