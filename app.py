<<<<<<< HEAD
# app.py

import streamlit as st
from src.inference.summarize import summarize_long
from src.inference.structure_summary import build_structured_summary
from src.utils.pdf_loader import extract_text_from_pdf
import re
import json
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════
# STORAGE — all cases saved to a local JSON file
# ═══════════════════════════════════════════════════════════════════════

HISTORY_FILE = "case_history.json"

def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history: list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_to_history(record: dict):
    history = load_history()
    # Avoid exact duplicates (same case name + date)
    for existing in history:
        if (existing.get("case_name") == record.get("case_name") and
                existing.get("date") == record.get("date")):
            return  # already stored
    history.insert(0, record)   # newest first
    save_history(history)

def delete_from_history(index: int):
    history = load_history()
    if 0 <= index < len(history):
        history.pop(index)
        save_history(history)


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def parse_summary_into_sections(raw_summary: str, original_text: str) -> dict:
    sections = {"main_issue": "", "background": "", "findings": ""}

    issue_match = re.search(
        r"(the issue is[^\.]+\.|whether[^\.]+\.)", original_text, re.IGNORECASE
    )
    if issue_match:
        sections["main_issue"] = issue_match.group().strip()
    else:
        first_sent = raw_summary.split(".")[0] + "." if "." in raw_summary else raw_summary
        sections["main_issue"] = first_sent

    background_parts = []
    for pattern in [
        r"(applications? filed before[^\.]+\.)",
        r"(the[^\.]*tribunal[^\.]+\.)",
        r"(the[^\.]*high court[^\.]+\.)",
        r"(aggrieved against[^\.]+\.)",
    ]:
        matches = re.findall(pattern, original_text, re.IGNORECASE)
        background_parts.extend(matches[:1])
    sections["background"] = " ".join(background_parts[:3]).strip()

    sentences = raw_summary.split(".")
    mid = len(sentences) // 2
    sections["findings"] = ". ".join(sentences[mid:]).strip()
    if not sections["findings"]:
        sections["findings"] = raw_summary

    return sections


def format_download_text(meta: dict, structured: dict, sections: dict) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("LEGAL CASE SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Case     : {meta['case_name']}")
    lines.append(f"Court    : {meta['court']}")
    lines.append(f"Date     : {meta['date']}")
    lines.append(f"Citation : {meta['citation']}")
    lines.append(f"Appeal   : {meta['appeal_no']}")
    lines.append(f"Decision : {structured['final_decision']}")
    lines.append("")
    lines.append("MAIN ISSUE")
    lines.append("-" * 40)
    lines.append(sections.get("main_issue", ""))
    lines.append("")
    lines.append("BACKGROUND")
    lines.append("-" * 40)
    lines.append(sections.get("background", ""))
    lines.append("")
    lines.append("COURT'S FINDINGS")
    lines.append("-" * 40)
    lines.append(sections.get("findings", ""))
    lines.append("")
    if structured.get("acts_sections"):
        lines.append("ACTS & SECTIONS REFERENCED")
        lines.append("-" * 40)
        for act in structured["acts_sections"]:
            lines.append(f"  • {act}")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def render_summary_sections(structured, sections, show_metadata, show_main_issue,
                             show_background, show_findings, show_decision, show_acts, show_raw,
                             raw_summary=""):
    meta = structured["metadata"]

    if show_metadata:
        st.subheader("📋 Case Metadata")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**📁 Case Name:** {meta['case_name'] or 'N/A'}")
            st.markdown(f"**🏛️ Court:** {meta['court'] or 'N/A'}")
            st.markdown(f"**📅 Date:** {meta['date'] or 'N/A'}")
        with col2:
            st.markdown(f"**🔖 Citation:** `{meta['citation'] or 'N/A'}`")
            st.markdown(f"**📌 Appeal No.:** {meta['appeal_no'] or 'N/A'}")
            if structured.get("judges"):
                st.markdown(f"**👨‍⚖️ Judges:** {', '.join(structured['judges'])}")
        st.markdown("---")

    if show_decision and structured.get("final_decision"):
        st.subheader("🏁 Final Decision")
        decision = structured["final_decision"]
        badge_class = "decision-badge-dismissed" if "Dismiss" in decision else "decision-badge-allowed"
        st.markdown(
            f'<span class="{badge_class}">{decision}</span>',
            unsafe_allow_html=True
        )
        st.markdown("")

    st.subheader("📄 Case Summary")

    if show_main_issue and sections.get("main_issue"):
        with st.expander("⚖️ Main Issue / Question of Law", expanded=True):
            st.markdown(sections["main_issue"])

    if show_background and sections.get("background"):
        with st.expander("📜 Background & Procedural History", expanded=True):
            st.markdown(sections["background"])

    if show_findings and sections.get("findings"):
        with st.expander("🔍 Court's Key Findings", expanded=True):
            st.markdown(sections["findings"])

    if show_acts and structured.get("acts_sections"):
        with st.expander("📚 Acts & Sections Referenced"):
            for act in structured["acts_sections"]:
                st.markdown(f'<span class="tag">📌 {act}</span>', unsafe_allow_html=True)
            st.markdown("")

    if show_raw and raw_summary:
        with st.expander("🤖 Raw Model Output"):
            st.text_area("LED Model Output", raw_summary, height=200)


# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Legal Case Summarizer",
    page_icon="⚖️",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
}
h1, h2, h3 {
    font-family: 'Playfair Display', serif;
}
.main-header {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem; font-weight: 700;
    color: #1a1a2e; margin-bottom: 0.2rem;
}
.sub-header {
    color: #666; font-size: 1rem; margin-bottom: 1.5rem;
}
.decision-badge-dismissed {
    background: #ffe3e3; color: #c0392b;
    padding: 0.35rem 1rem; border-radius: 20px;
    font-weight: 600; display: inline-block;
    font-size: 0.95rem;
}
.decision-badge-allowed {
    background: #d3f9d8; color: #1e7e34;
    padding: 0.35rem 1rem; border-radius: 20px;
    font-weight: 600; display: inline-block;
    font-size: 0.95rem;
}
.tag {
    background: #e7f5ff; color: #1971c2;
    padding: 0.2rem 0.6rem; border-radius: 12px;
    font-size: 0.82rem; display: inline-block; margin: 2px;
}

/* ── Case History Cards ── */
.case-card {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-left: 5px solid #3b5bdb;
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 1rem;
    transition: box-shadow 0.2s;
}
.case-card:hover {
    box-shadow: 0 4px 16px rgba(59,91,219,0.10);
}
.case-card-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 0.3rem;
}
.case-card-meta {
    font-size: 0.84rem;
    color: #777;
    margin-bottom: 0.5rem;
}
.case-card-issue {
    font-size: 0.93rem;
    color: #333;
    font-style: italic;
    border-top: 1px solid #f0f0f0;
    padding-top: 0.5rem;
    margin-top: 0.4rem;
}
.history-empty {
    text-align: center;
    color: #aaa;
    padding: 3rem 1rem;
    font-size: 1.1rem;
}
.stats-box {
    background: linear-gradient(135deg, #3b5bdb11, #3b5bdb05);
    border: 1px solid #3b5bdb22;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}
.stats-number {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #3b5bdb;
}
.stats-label {
    font-size: 0.82rem;
    color: #777;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════

st.markdown('<div class="main-header">⚖️ Legal Case Summarizer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-powered summarization for Indian legal judgments</div>', unsafe_allow_html=True)
st.divider()


# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR FILTERS
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("⚙️ Output Options")
    show_metadata   = st.toggle("Case Metadata",          value=True)
    show_main_issue = st.toggle("Main Issue",             value=True)
    show_background = st.toggle("Background / History",   value=True)
    show_findings   = st.toggle("Court Findings",         value=True)
    show_decision   = st.toggle("Final Decision",         value=True)
    show_acts       = st.toggle("Acts & Sections",        value=True)
    show_raw        = st.toggle("Raw Model Output",       value=False)
    st.divider()
    st.caption("Cases are saved automatically after summarization.")


# ═══════════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════════

tab_summarize, tab_history = st.tabs(["⚡ Summarize", "🗂️ Case History"])


# ───────────────────────────────────────────────────────────────────────
# TAB 1 — SUMMARIZE
# ───────────────────────────────────────────────────────────────────────

with tab_summarize:
    input_tab, pdf_tab = st.tabs(["📝 Paste Text", "📄 Upload PDF"])

    input_text   = ""
    source_label = ""

    with input_tab:
        input_text_area = st.text_area(
            "Paste legal case text here",
            height=280,
            placeholder="Paste the full judgment or legal document text..."
        )
        if st.button("⚡ Summarize Text", type="primary", use_container_width=True):
            input_text   = input_text_area
            source_label = "Pasted Text"

    with pdf_tab:
        uploaded_file = st.file_uploader("Upload a PDF judgment", type=["pdf"])
        if uploaded_file:
            st.success(f"✅ File uploaded: `{uploaded_file.name}`")
            if st.button("⚡ Summarize PDF", type="primary", use_container_width=True):
                with st.spinner("📖 Extracting text from PDF..."):
                    try:
                        input_text   = extract_text_from_pdf(uploaded_file)
                        source_label = uploaded_file.name
                        if not input_text.strip():
                            st.error("Could not extract text. Try a text-based PDF.")
                            input_text = ""
                    except Exception as e:
                        st.error(f"PDF extraction failed: {e}")

    # ── Process & Display ──────────────────────────────────────────────
    if input_text and input_text.strip():
        st.divider()

        with st.spinner("🧠 Generating summary with AI model..."):
            try:
                raw_summary     = summarize_long(input_text)
                structured      = build_structured_summary(raw_summary, input_text)
                summary_sections = parse_summary_into_sections(raw_summary, input_text)
                meta            = structured["metadata"]
            except Exception as e:
                st.error(f"Summarization failed: {e}")
                st.stop()

        st.success("✅ Summary Generated — saved to Case History")

        # ── Auto-save to history ───────────────────────────────────────
        history_record = {
            "saved_at":     datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source":       source_label,
            "case_name":    meta.get("case_name", "Unknown Case"),
            "court":        meta.get("court", ""),
            "date":         meta.get("date", ""),
            "citation":     meta.get("citation", ""),
            "appeal_no":    meta.get("appeal_no", ""),
            "final_decision": structured.get("final_decision", ""),
            "judges":       structured.get("judges", []),
            "acts_sections": structured.get("acts_sections", []),
            "main_issue":   summary_sections.get("main_issue", ""),
            "background":   summary_sections.get("background", ""),
            "findings":     summary_sections.get("findings", ""),
            "raw_summary":  raw_summary,
        }
        add_to_history(history_record)

        # ── Render summary ─────────────────────────────────────────────
        render_summary_sections(
            structured, summary_sections,
            show_metadata, show_main_issue, show_background,
            show_findings, show_decision, show_acts, show_raw,
            raw_summary
        )

        # ── Download ───────────────────────────────────────────────────
        st.divider()
        full_output = format_download_text(meta, structured, summary_sections)
        st.download_button(
            label="⬇️ Download Full Summary (.txt)",
            data=full_output,
            file_name="legal_summary.txt",
            mime="text/plain",
            use_container_width=True
        )


# ───────────────────────────────────────────────────────────────────────
# TAB 2 — CASE HISTORY
# ───────────────────────────────────────────────────────────────────────

with tab_history:
    history = load_history()

    # ── Stats Row ──────────────────────────────────────────────────────
    if history:
        dismissed = sum(1 for h in history if "Dismiss" in h.get("final_decision", ""))
        allowed   = sum(1 for h in history if "Allowed" in h.get("final_decision", ""))
        courts    = list(set(h.get("court", "") for h in history if h.get("court")))

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="stats-box">
                <div class="stats-number">{len(history)}</div>
                <div class="stats-label">Total Cases</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stats-box">
                <div class="stats-number" style="color:#c0392b">{dismissed}</div>
                <div class="stats-label">Dismissed</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="stats-box">
                <div class="stats-number" style="color:#1e7e34">{allowed}</div>
                <div class="stats-label">Allowed</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="stats-box">
                <div class="stats-number">{len(courts)}</div>
                <div class="stats-label">Courts</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("")

    # ── Search & Filter Row ────────────────────────────────────────────
    st.subheader("🔍 Search & Filter")
    col_search, col_decision, col_court = st.columns([3, 1.5, 1.5])

    with col_search:
        search_query = st.text_input(
            "Search by case name, issue, citation or keyword",
            placeholder="e.g. Union of India, HRA, Section 59..."
        )
    with col_decision:
        filter_decision = st.selectbox(
            "Final Decision",
            ["All", "Dismissed", "Allowed", "Remanded", "Unknown"]
        )
    with col_court:
        all_courts = ["All"] + sorted(set(
            h.get("court", "Unknown") for h in history if h.get("court")
        ))
        filter_court = st.selectbox("Court", all_courts)

    # Date range filter
    col_date1, col_date2, col_clear = st.columns([2, 2, 1])
    with col_date1:
        date_from = st.text_input("Saved From (YYYY-MM-DD)", placeholder="2024-01-01")
    with col_date2:
        date_to   = st.text_input("Saved To (YYYY-MM-DD)",   placeholder="2026-12-31")
    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear All Filters"):
            search_query    = ""
            filter_decision = "All"
            filter_court    = "All"
            date_from       = ""
            date_to         = ""

    st.divider()

    # ── Apply filters ──────────────────────────────────────────────────
    filtered = history

    if search_query.strip():
        q = search_query.lower()
        filtered = [
            h for h in filtered if
            q in h.get("case_name", "").lower() or
            q in h.get("main_issue", "").lower() or
            q in h.get("citation", "").lower() or
            q in h.get("findings", "").lower() or
            q in h.get("appeal_no", "").lower()
        ]

    if filter_decision != "All":
        filtered = [
            h for h in filtered
            if filter_decision.lower() in h.get("final_decision", "").lower()
        ]

    if filter_court != "All":
        filtered = [h for h in filtered if h.get("court") == filter_court]

    if date_from.strip():
        filtered = [h for h in filtered if h.get("saved_at", "") >= date_from]

    if date_to.strip():
        filtered = [h for h in filtered if h.get("saved_at", "") <= date_to + " 99"]

    # ── Results count ──────────────────────────────────────────────────
    if history:
        st.caption(f"Showing **{len(filtered)}** of **{len(history)}** cases")

    # ── Render case cards ──────────────────────────────────────────────
    if not history:
        st.markdown("""
        <div class="history-empty">
            📂 No cases yet.<br>
            <span style="font-size:0.9rem">Summarize a case and it will appear here automatically.</span>
        </div>
        """, unsafe_allow_html=True)

    elif not filtered:
        st.info("No cases match your search/filter criteria.")

    else:
        for idx, record in enumerate(filtered):
            decision = record.get("final_decision", "")
            border_color = (
                "#c0392b" if "Dismiss" in decision else
                "#1e7e34" if "Allowed" in decision else
                "#888"
            )

            # Card HTML
            st.markdown(f"""
            <div class="case-card" style="border-left-color:{border_color}">
                <div class="case-card-title">
                    {record.get('case_name', 'Unnamed Case')}
                </div>
                <div class="case-card-meta">
                    🏛️ {record.get('court', 'N/A')} &nbsp;|&nbsp;
                    📅 {record.get('date', 'N/A')} &nbsp;|&nbsp;
                    🔖 {record.get('citation', 'N/A')} &nbsp;|&nbsp;
                    💾 Saved: {record.get('saved_at', 'N/A')} &nbsp;|&nbsp;
                    📄 {record.get('source', 'N/A')}
                </div>
                {"<span class='decision-badge-dismissed'>" + decision + "</span>" if "Dismiss" in decision else
                 "<span class='decision-badge-allowed'>" + decision + "</span>" if "Allow" in decision else
                 "<span style='background:#f0f0f0;padding:0.2rem 0.7rem;border-radius:12px;font-size:0.85rem'>" + (decision or "Unknown") + "</span>"}
                <div class="case-card-issue">
                    {record.get('main_issue', '')[:200] + '...' if len(record.get('main_issue','')) > 200 else record.get('main_issue','')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Expand / Delete buttons
            btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 6])

            with btn_col1:
                expand_key = f"expand_{idx}_{record.get('saved_at','')}"
                if st.button("📖 View Full Summary", key=expand_key):
                    st.session_state[f"show_{idx}"] = not st.session_state.get(f"show_{idx}", False)

            with btn_col2:
                dl_text = format_download_text(
                    {
                        "case_name": record.get("case_name", ""),
                        "court":     record.get("court", ""),
                        "date":      record.get("date", ""),
                        "citation":  record.get("citation", ""),
                        "appeal_no": record.get("appeal_no", ""),
                    },
                    {
                        "final_decision": record.get("final_decision", ""),
                        "acts_sections":  record.get("acts_sections", []),
                    },
                    {
                        "main_issue": record.get("main_issue", ""),
                        "background": record.get("background", ""),
                        "findings":   record.get("findings", ""),
                    }
                )
                safe_name = re.sub(r"[^\w]", "_", record.get("case_name", "case"))[:40]
                st.download_button(
                    "⬇️ Download",
                    data=dl_text,
                    file_name=f"{safe_name}_summary.txt",
                    mime="text/plain",
                    key=f"dl_{idx}_{record.get('saved_at','')}"
                )

            with btn_col3:
                # Find actual index in full history for deletion
                actual_idx = history.index(record) if record in history else -1
                if st.button("🗑️ Delete", key=f"del_{idx}_{record.get('saved_at','')}"):
                    if actual_idx >= 0:
                        delete_from_history(actual_idx)
                        st.success("Deleted.")
                        st.rerun()

            # ── Expanded full summary ──────────────────────────────────
            if st.session_state.get(f"show_{idx}", False):
                with st.container():
                    st.markdown("---")
                    # Rebuild structured & sections from stored data
                    stored_structured = {
                        "metadata": {
                            "case_name": record.get("case_name", ""),
                            "court":     record.get("court", ""),
                            "date":      record.get("date", ""),
                            "citation":  record.get("citation", ""),
                            "appeal_no": record.get("appeal_no", ""),
                        },
                        "final_decision": record.get("final_decision", ""),
                        "judges":         record.get("judges", []),
                        "acts_sections":  record.get("acts_sections", []),
                    }
                    stored_sections = {
                        "main_issue": record.get("main_issue", ""),
                        "background": record.get("background", ""),
                        "findings":   record.get("findings", ""),
                    }
                    render_summary_sections(
                        stored_structured, stored_sections,
                        show_metadata, show_main_issue, show_background,
                        show_findings, show_decision, show_acts, show_raw,
                        record.get("raw_summary", "")
                    )
                    st.markdown("---")

        # ── Bulk clear ─────────────────────────────────────────────────
        st.markdown("")
        if st.button("🗑️ Delete ALL Cases from History", type="secondary"):
            save_history([])
            st.success("All history cleared.")
            st.rerun()
=======
import streamlit as st
from src.inference.summarize import summarize_long
from src.utils.pdf_loader import extract_text_from_pdf

st.set_page_config(page_title="Legal Summarizer", layout="wide")

st.title("📄 Legal Document Summarizer")

st.markdown("Upload a legal document or paste text to generate an AI-powered summary.")

# -----------------------------
# INPUT TYPE
# -----------------------------
option = st.radio("Choose Input Type", ["Text", "PDF"])

# =============================
# TEXT INPUT
# =============================
if option == "Text":

    user_input = st.text_area("Paste Legal Document", height=300)

    if st.button("Summarize Text"):

        if not user_input.strip():
            st.warning("⚠️ Please enter some text first.")
        else:
            try:
                with st.spinner("🧠 Summarizing document..."):
                    result = summarize_long(user_input)

                if not result.strip():
                    st.error("❌ Model returned empty summary.")
                else:
                    st.success("✅ Summary Generated")

                    st.subheader("📄 Summary Output")
                    st.text_area("Summary", result, height=300)

                    st.download_button(
                        label="⬇ Download Summary",
                        data=result,
                        file_name="summary.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"❌ Error during summarization: {str(e)}")


# =============================
# PDF INPUT
# =============================
elif option == "PDF":

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file is not None:

        st.info("📂 File uploaded successfully")

        if st.button("Summarize PDF"):

            try:
                # Step 1: Extract text
                with st.spinner("📖 Extracting text from PDF..."):
                    text = extract_text_from_pdf(uploaded_file)

                if not text or not text.strip():
                    st.error("❌ Could not extract text from PDF.")
                else:
                    st.success("✅ PDF text extracted")

                    # Optional: Show extracted length
                    st.caption(f"📊 Extracted characters: {len(text)}")

                    # Step 2: Summarize
                    with st.spinner("🧠 Generating summary (this may take a while for large documents)..."):
                        result = summarize_long(text)

                    if not result.strip():
                        st.error("❌ Model returned empty summary.")
                    else:
                        st.success("✅ Summary Generated")

                        # Step 3: Display
                        st.subheader("📄 Summary Output")
                        st.text_area("Summary", result, height=300)

                        # Step 4: Download
                        st.download_button(
                            label="⬇ Download Summary",
                            data=result,
                            file_name="summary.txt",
                            mime="text/plain"
                        )

            except Exception as e:
                st.error(f"❌ Error during PDF summarization: {str(e)}")
