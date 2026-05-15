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
# STORAGE
# ═══════════════════════════════════════════════════════════════════════

HISTORY_FILE = "case_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_to_history(record):
    history = load_history()
    for existing in history:
        if (existing.get("case_name") == record.get("case_name") and
                existing.get("date") == record.get("date")):
            return
    history.insert(0, record)
    save_history(history)

def delete_from_history(index):
    history = load_history()
    if 0 <= index < len(history):
        history.pop(index)
        save_history(history)

# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

def parse_summary_into_sections(raw_summary, original_text):
    sections = {"main_issue": "", "background": "", "findings": ""}
    issue_match = re.search(r"(the issue is[^\.]+\.|whether[^\.]+\.)", original_text, re.IGNORECASE)
    if issue_match:
        sections["main_issue"] = issue_match.group().strip()
    else:
        first_sent = raw_summary.split(".")[0] + "." if "." in raw_summary else raw_summary
        sections["main_issue"] = first_sent
    background_parts = []
    for pattern in [r"(applications? filed before[^\.]+\.)", r"(the[^\.]*tribunal[^\.]+\.)",
                    r"(the[^\.]*high court[^\.]+\.)", r"(aggrieved against[^\.]+\.)"]:
        matches = re.findall(pattern, original_text, re.IGNORECASE)
        background_parts.extend(matches[:1])
    sections["background"] = " ".join(background_parts[:3]).strip()
    sentences = raw_summary.split(".")
    mid = len(sentences) // 2
    sections["findings"] = ". ".join(sentences[mid:]).strip() or raw_summary
    return sections

def format_download_text(meta, structured, sections):
    lines = ["=" * 60, "LEGAL CASE SUMMARY", "=" * 60,
             f"Case     : {meta.get('case_name', '')}",
             f"Court    : {meta.get('court', '')}",
             f"Date     : {meta.get('date', '')}",
             f"Citation : {meta.get('citation', '')}",
             f"Appeal   : {meta.get('appeal_no', '')}",
             f"Decision : {structured.get('final_decision', '')}",
             "", "MAIN ISSUE", "-" * 40, sections.get("main_issue", ""),
             "", "BACKGROUND", "-" * 40, sections.get("background", ""),
             "", "COURT'S FINDINGS", "-" * 40, sections.get("findings", ""), ""]
    if structured.get("acts_sections"):
        lines += ["ACTS & SECTIONS REFERENCED", "-" * 40]
        lines += [f"  • {a}" for a in structured["acts_sections"]]
    lines.append("=" * 60)
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="LexBrief — Legal Case Summarizer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #f5f3ef;
}
.main .block-container { padding: 2rem 2.5rem; max-width: 1200px; }

[data-testid="stSidebar"] { background: #0f1923; border-right: 1px solid #1e2d3d; }
[data-testid="stSidebar"] * { color: #c9b99a !important; font-family: 'DM Sans', sans-serif !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color: #e8d5b0 !important; font-family: 'Cormorant Garamond', serif !important; }
[data-testid="stSidebar"] hr { border-color: #1e2d3d !important; }

.hero {
    background: linear-gradient(135deg, #0f1923 0%, #1a2d3e 50%, #0f1923 100%);
    border-radius: 16px; padding: 3rem 3.5rem; margin-bottom: 2rem;
    position: relative; overflow: hidden; border: 1px solid #2a3f52;
}
.hero::before {
    content: ''; position: absolute; top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, #c9a84c22 0%, transparent 70%); border-radius: 50%;
}
.hero-eyebrow { font-size: 0.72rem; font-weight: 600; color: #c9a84c; letter-spacing: 0.22em; text-transform: uppercase; margin-bottom: 0.8rem; }
.hero-title { font-family: 'Cormorant Garamond', serif; font-size: 3.2rem; font-weight: 700; color: #f0e6d0; line-height: 1.1; margin-bottom: 0.8rem; }
.hero-title span { color: #c9a84c; font-style: italic; }
.hero-sub { font-size: 1rem; color: #7a9ab5; font-weight: 300; max-width: 560px; line-height: 1.6; }
.hero-badge { display: inline-block; background: #c9a84c18; border: 1px solid #c9a84c44; color: #c9a84c; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.3rem 0.8rem; border-radius: 20px; margin-top: 1.2rem; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }
.stat-card { background: #fff; border: 1px solid #e2ddd6; border-radius: 12px; padding: 1.2rem 1.4rem; text-align: center; transition: transform 0.2s, box-shadow 0.2s; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.stat-num { font-family: 'Cormorant Garamond', serif; font-size: 2.4rem; font-weight: 700; color: #0f1923; line-height: 1; margin-bottom: 0.3rem; }
.stat-num.gold { color: #b8860b; } .stat-num.red { color: #8b1a1a; } .stat-num.green { color: #1a5c2e; }
.stat-label { font-size: 0.72rem; font-weight: 600; color: #9e9589; letter-spacing: 0.12em; text-transform: uppercase; }

.stTabs [data-baseweb="tab-list"] { background: transparent; gap: 0.5rem; border-bottom: 2px solid #e2ddd6; }
.stTabs [data-baseweb="tab"] { font-family: 'DM Sans', sans-serif; font-size: 0.88rem; font-weight: 500; color: #7a7068; background: transparent; border: none; border-radius: 8px 8px 0 0; padding: 0.6rem 1.2rem; transition: all 0.2s; }
.stTabs [aria-selected="true"] { color: #0f1923 !important; background: #fff !important; border-bottom: 2px solid #c9a84c !important; font-weight: 600 !important; }

.stButton > button { font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important; border-radius: 8px !important; transition: all 0.2s !important; }
.stButton > button[kind="primary"] { background: #0f1923 !important; color: #f0e6d0 !important; border: none !important; }
.stButton > button[kind="primary"]:hover { background: #1a2d3e !important; box-shadow: 0 4px 16px rgba(15,25,35,0.25) !important; transform: translateY(-1px) !important; }

.result-header { background: linear-gradient(135deg, #0f1923, #1a2d3e); border-radius: 14px; padding: 1.8rem 2rem; margin-bottom: 1.5rem; border-left: 4px solid #c9a84c; }
.result-case-name { font-family: 'Cormorant Garamond', serif; font-size: 1.6rem; font-weight: 700; color: #f0e6d0; margin-bottom: 0.5rem; line-height: 1.2; }
.result-meta { font-size: 0.82rem; color: #7a9ab5; margin-bottom: 0.8rem; }
.result-meta span { margin-right: 1.2rem; }

.decision-pill { display: inline-block; padding: 0.3rem 1rem; border-radius: 20px; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
.pill-dismissed { background: #8b1a1a22; color: #c0392b; border: 1px solid #8b1a1a44; }
.pill-allowed   { background: #1a5c2e22; color: #1e7e34; border: 1px solid #1a5c2e44; }
.pill-unknown   { background: #c9a84c22; color: #b8860b; border: 1px solid #c9a84c44; }

.section-card { background: #fff; border: 1px solid #e8e2d9; border-radius: 12px; padding: 1.4rem 1.6rem; margin-bottom: 1rem; border-left: 3px solid #c9a84c; }
.section-label { font-size: 0.68rem; font-weight: 700; color: #c9a84c; letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 0.6rem; }
.section-text { font-size: 0.95rem; color: #3a3530; line-height: 1.7; }

.act-tag { display: inline-block; background: #eef2f8; color: #2a4a72; font-size: 0.78rem; font-weight: 500; padding: 0.25rem 0.7rem; border-radius: 6px; margin: 3px; border: 1px solid #d0daea; }

.hcard { background: #fff; border: 1px solid #e2ddd6; border-radius: 12px; padding: 1.3rem 1.5rem; margin-bottom: 1rem; border-left: 4px solid #c9a84c; transition: box-shadow 0.2s, transform 0.2s; }
.hcard:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.07); transform: translateY(-1px); }
.hcard.dismissed { border-left-color: #8b1a1a; }
.hcard.allowed   { border-left-color: #1a5c2e; }
.hcard-title { font-family: 'Cormorant Garamond', serif; font-size: 1.15rem; font-weight: 700; color: #0f1923; margin-bottom: 0.3rem; line-height: 1.3; }
.hcard-meta { font-size: 0.78rem; color: #9e9589; margin-bottom: 0.6rem; }
.hcard-issue { font-size: 0.88rem; color: #5a5348; font-style: italic; line-height: 1.5; padding-top: 0.6rem; border-top: 1px solid #f0ece6; margin-top: 0.5rem; }

.empty-state { text-align: center; padding: 4rem 2rem; color: #b0a898; }
.empty-icon { font-size: 3rem; margin-bottom: 1rem; display: block; }
.empty-text { font-family: 'Cormorant Garamond', serif; font-size: 1.4rem; color: #9e9589; margin-bottom: 0.5rem; }
.empty-sub { font-size: 0.88rem; color: #b8b0a5; }

.stTextInput > div > div > input { border-radius: 8px !important; border: 1.5px solid #e2ddd6 !important; font-family: 'DM Sans', sans-serif !important; background: #fff !important; color: #1a1410 !important; }
.stTextInput > div > div > input:focus { border-color: #c9a84c !important; box-shadow: 0 0 0 3px #c9a84c18 !important; }
[data-testid="stFileUploader"] { background: #faf8f5; border: 2px dashed #d4c9b8; border-radius: 12px; transition: border-color 0.2s; }
[data-testid="stFileUploader"]:hover { border-color: #c9a84c; }
hr { border: none; border-top: 1px solid #e8e2d9; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style='padding:1rem 0 0.5rem'>
        <div style='font-family:Cormorant Garamond,serif;font-size:1.5rem;font-weight:700;color:#e8d5b0'>⚖️ LexBrief</div>
        <div style='font-size:0.72rem;color:#4a6a82;letter-spacing:0.1em;text-transform:uppercase;margin-top:0.2rem'>Legal Intelligence Tool</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='font-size:0.72rem;letter-spacing:0.12em;text-transform:uppercase;color:#4a6a82;font-weight:600;margin-bottom:0.8rem'>Summary Sections</div>", unsafe_allow_html=True)
    show_metadata   = st.toggle("Case Metadata",        value=True)
    show_main_issue = st.toggle("Main Issue",           value=True)
    show_background = st.toggle("Background & History", value=True)
    show_findings   = st.toggle("Court Findings",       value=True)
    show_decision   = st.toggle("Final Decision",       value=True)
    show_acts       = st.toggle("Acts & Sections",      value=True)
    show_raw        = st.toggle("Raw Model Output",     value=False)
    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.75rem;color:#3a5a72;line-height:1.6'>
        Powered by<br>
        <strong style='color:#c9a84c'>LED (Longformer)</strong><br>
        Fine-tuned on ILC dataset<br>
        Indian legal judgments
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">AI-Powered Legal Intelligence</div>
    <div class="hero-title">Indian Court Judgment<br><span>Summarizer</span></div>
    <div class="hero-sub">Upload any Supreme Court or High Court judgment PDF. Get a structured, plain-language summary in seconds.</div>
    <div class="hero-badge">⚡ Trained on Indian Legal Corpus</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════

tab_sum, tab_hist = st.tabs(["⚡  Summarize a Case", "🗂️  Case History"])

# ── TAB 1 ─────────────────────────────────────────────────────────────
with tab_sum:
    inp_tab, pdf_tab = st.tabs(["📝  Paste Text", "📄  Upload PDF"])
    input_text = ""
    source_label = ""

    with inp_tab:
        st.markdown("<br>", unsafe_allow_html=True)
        input_text_area = st.text_area("Paste the full judgment text below", height=280,
            placeholder="Paste complete judgment text here...")
        if st.button("⚡  Generate Summary", type="primary", use_container_width=True):
            input_text = input_text_area
            source_label = "Pasted Text"

    with pdf_tab:
        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Drop your PDF judgment here", type=["pdf"],
            help="Text-based PDFs work best.")
        if uploaded_file:
            st.success(f"✅  **{uploaded_file.name}** ready to summarize")
            if st.button("⚡  Summarize PDF", type="primary", use_container_width=True):
                with st.spinner("Reading PDF..."):
                    try:
                        input_text = extract_text_from_pdf(uploaded_file)
                        source_label = uploaded_file.name
                        if not input_text.strip():
                            st.error("Could not extract text. Please use a text-based PDF.")
                            input_text = ""
                    except Exception as e:
                        st.error(f"PDF error: {e}")

    if input_text and input_text.strip():
        st.markdown("<br>", unsafe_allow_html=True)
        with st.spinner("🧠  AI is reading the judgment..."):
            try:
                raw_summary      = summarize_long(input_text)
                structured       = build_structured_summary(raw_summary, input_text)
                summary_sections = parse_summary_into_sections(raw_summary, input_text)
                meta             = structured["metadata"]
            except Exception as e:
                st.error(f"Summarization failed: {e}")
                st.stop()

        add_to_history({
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": source_label,
            "case_name": meta.get("case_name", "Unknown Case"),
            "court": meta.get("court", ""),
            "date": meta.get("date", ""),
            "citation": meta.get("citation", ""),
            "appeal_no": meta.get("appeal_no", ""),
            "final_decision": structured.get("final_decision", ""),
            "judges": structured.get("judges", []),
            "acts_sections": structured.get("acts_sections", []),
            "main_issue": summary_sections.get("main_issue", ""),
            "background": summary_sections.get("background", ""),
            "findings": summary_sections.get("findings", ""),
            "raw_summary": raw_summary,
        })

        decision   = structured.get("final_decision", "")
        pill_class = "pill-dismissed" if "Dismiss" in decision else "pill-allowed" if "Allow" in decision else "pill-unknown"

        st.markdown(f"""
        <div class="result-header">
            <div class="result-case-name">{meta.get('case_name') or 'Case Summary'}</div>
            <div class="result-meta">
                <span>🏛️ {meta.get('court') or 'N/A'}</span>
                <span>📅 {meta.get('date') or 'N/A'}</span>
                <span>🔖 {meta.get('citation') or 'N/A'}</span>
            </div>
            <span class="decision-pill {pill_class}">{decision or 'Unknown'}</span>
        </div>""", unsafe_allow_html=True)

        if show_main_issue and summary_sections.get("main_issue"):
            st.markdown(f'<div class="section-card"><div class="section-label">⚖️ Main Legal Issue</div><div class="section-text">{summary_sections["main_issue"]}</div></div>', unsafe_allow_html=True)
        if show_background and summary_sections.get("background"):
            st.markdown(f'<div class="section-card"><div class="section-label">📜 Background & Procedural History</div><div class="section-text">{summary_sections["background"]}</div></div>', unsafe_allow_html=True)
        if show_findings and summary_sections.get("findings"):
            st.markdown(f'<div class="section-card"><div class="section-label">🔍 Court\'s Key Findings</div><div class="section-text">{summary_sections["findings"]}</div></div>', unsafe_allow_html=True)

        if show_metadata:
            with st.expander("📋 Full Case Metadata"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Case Name:** {meta.get('case_name','N/A')}")
                    st.markdown(f"**Court:** {meta.get('court','N/A')}")
                    st.markdown(f"**Date:** {meta.get('date','N/A')}")
                with c2:
                    st.markdown(f"**Citation:** `{meta.get('citation','N/A')}`")
                    st.markdown(f"**Appeal No.:** {meta.get('appeal_no','N/A')}")
                    if structured.get("judges"):
                        st.markdown(f"**Judges:** {', '.join(structured['judges'])}")

        if show_acts and structured.get("acts_sections"):
            tags = "".join([f'<span class="act-tag">📌 {a}</span>' for a in structured["acts_sections"]])
            st.markdown(f'<div class="section-card"><div class="section-label">📚 Acts & Sections Referenced</div><div style="margin-top:0.4rem">{tags}</div></div>', unsafe_allow_html=True)

        if show_raw:
            with st.expander("🤖 Raw Model Output"):
                st.text_area("", raw_summary, height=200)

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("⬇️  Download Summary (.txt)",
            data=format_download_text(meta, structured, summary_sections),
            file_name="legal_summary.txt", mime="text/plain", use_container_width=True)
        st.success("✅ Summary saved to Case History")

# ── TAB 2 ─────────────────────────────────────────────────────────────
with tab_hist:
    history   = load_history()
    dismissed = sum(1 for h in history if "Dismiss" in h.get("final_decision",""))
    allowed   = sum(1 for h in history if "Allow"   in h.get("final_decision",""))
    courts    = set(h.get("court","") for h in history if h.get("court"))

    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-card"><div class="stat-num gold">{len(history)}</div><div class="stat-label">Total Cases</div></div>
        <div class="stat-card"><div class="stat-num red">{dismissed}</div><div class="stat-label">Dismissed</div></div>
        <div class="stat-card"><div class="stat-num green">{allowed}</div><div class="stat-label">Allowed</div></div>
        <div class="stat-card"><div class="stat-num">{len(courts)}</div><div class="stat-label">Courts</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.72rem;font-weight:700;color:#9e9589;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.8rem'>Search & Filter</div>", unsafe_allow_html=True)
    col_s, col_d, col_c = st.columns([3, 1.5, 1.5])
    with col_s:
        search_q = st.text_input("", placeholder="🔍  Search case name, citation, keyword...", label_visibility="collapsed")
    with col_d:
        filt_dec = st.selectbox("Decision", ["All", "Dismissed", "Allowed", "Remanded"], label_visibility="collapsed")
    with col_c:
        filt_court = st.selectbox("Court", ["All Courts"] + sorted(courts), label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    filtered = history
    if search_q.strip():
        q = search_q.lower()
        filtered = [h for h in filtered if q in h.get("case_name","").lower() or
                    q in h.get("main_issue","").lower() or q in h.get("citation","").lower() or
                    q in h.get("findings","").lower()]
    if filt_dec != "All":
        filtered = [h for h in filtered if filt_dec.lower() in h.get("final_decision","").lower()]
    if filt_court != "All Courts":
        filtered = [h for h in filtered if h.get("court") == filt_court]

    if history:
        st.markdown(f"<div style='font-size:0.82rem;color:#9e9589;margin-bottom:1rem'>Showing <strong>{len(filtered)}</strong> of <strong>{len(history)}</strong> cases</div>", unsafe_allow_html=True)

    if not history:
        st.markdown("""<div class="empty-state"><span class="empty-icon">📂</span>
        <div class="empty-text">No cases summarized yet</div>
        <div class="empty-sub">Summarize your first judgment and it will appear here</div></div>""", unsafe_allow_html=True)
    elif not filtered:
        st.info("No cases match your search criteria.")
    else:
        for idx, record in enumerate(filtered):
            dec        = record.get("final_decision","")
            card_class = "dismissed" if "Dismiss" in dec else "allowed" if "Allow" in dec else ""
            pill_cls   = "pill-dismissed" if "Dismiss" in dec else "pill-allowed" if "Allow" in dec else "pill-unknown"
            issue_text = record.get("main_issue","")
            preview    = (issue_text[:180] + "…") if len(issue_text) > 180 else issue_text

            st.markdown(f"""
            <div class="hcard {card_class}">
                <div class="hcard-title">{record.get('case_name','Unnamed Case')}</div>
                <div class="hcard-meta">
                    🏛️ {record.get('court','N/A')} &nbsp;·&nbsp; 📅 {record.get('date','N/A')} &nbsp;·&nbsp;
                    🔖 {record.get('citation','N/A')} &nbsp;·&nbsp; 💾 {record.get('saved_at','N/A')}
                    &nbsp;&nbsp;<span class="decision-pill {pill_cls}">{dec or 'Unknown'}</span>
                </div>
                <div class="hcard-issue">{preview}</div>
            </div>""", unsafe_allow_html=True)

            b1, b2, b3, _ = st.columns([2, 2, 1, 5])
            with b1:
                if st.button("📖 View", key=f"exp_{idx}_{record.get('saved_at','')}"):
                    st.session_state[f"show_{idx}"] = not st.session_state.get(f"show_{idx}", False)
            with b2:
                dl = format_download_text(
                    {"case_name": record.get("case_name",""), "court": record.get("court",""),
                     "date": record.get("date",""), "citation": record.get("citation",""), "appeal_no": record.get("appeal_no","")},
                    {"final_decision": record.get("final_decision",""), "acts_sections": record.get("acts_sections",[])},
                    {"main_issue": record.get("main_issue",""), "background": record.get("background",""), "findings": record.get("findings","")}
                )
                safe = re.sub(r"[^\w]", "_", record.get("case_name","case"))[:35]
                st.download_button("⬇️ Download", data=dl, file_name=f"{safe}.txt",
                                   mime="text/plain", key=f"dl_{idx}_{record.get('saved_at','')}")
            with b3:
                actual = history.index(record) if record in history else -1
                if st.button("🗑️", key=f"del_{idx}_{record.get('saved_at','')}", help="Delete"):
                    if actual >= 0:
                        delete_from_history(actual)
                        st.rerun()

            if st.session_state.get(f"show_{idx}", False):
                st.markdown("---")
                for label, key in [("⚖️ Main Issue","main_issue"),("📜 Background","background"),("🔍 Findings","findings")]:
                    val = record.get(key,"")
                    if val:
                        st.markdown(f'<div class="section-card"><div class="section-label">{label}</div><div class="section-text">{val}</div></div>', unsafe_allow_html=True)
                acts = record.get("acts_sections",[])
                if acts:
                    tags = "".join([f'<span class="act-tag">📌 {a}</span>' for a in acts])
                    st.markdown(f'<div class="section-card"><div class="section-label">📚 Acts Referenced</div><div style="margin-top:0.4rem">{tags}</div></div>', unsafe_allow_html=True)
                st.markdown("---")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️  Clear All History", type="secondary"):
            save_history([])
            st.rerun()