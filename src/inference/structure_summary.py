# src/inference/structure_summary.py

import re


def extract_case_metadata(text: str) -> dict:
    """Extract case name, court, date, citation from raw document text."""
    metadata = {
        "case_name": "",
        "court": "",
        "date": "",
        "citation": "",
        "appeal_no": "",
    }

    # Citation (e.g., 2026 INSC 74)
    citation_match = re.search(r"\d{4}\s+INSC\s+\d+", text)
    if citation_match:
        metadata["citation"] = citation_match.group()

    # Appeal/Case number
    appeal_match = re.search(
        r"(CIVIL APPEAL NOS?\.[\d\-\s]+OF\s+\d{4}|"
        r"CRIMINAL APPEAL NOS?\.[\d\-\s]+OF\s+\d{4}|"
        r"WRIT PETITION.*?OF\s+\d{4})",
        text, re.IGNORECASE
    )
    if appeal_match:
        metadata["appeal_no"] = appeal_match.group().strip()

    # Appellant vs Respondent
    vs_match = re.search(
        r"([\w\s&,\.]+)\s*[…\.]+\s*Appellant.*?VERSUS.*?([\w\s&,\.]+)\s*[…\.]+\s*Respondent",
        text, re.DOTALL | re.IGNORECASE
    )
    if vs_match:
        appellant = vs_match.group(1).strip().replace("\n", " ")
        respondent = vs_match.group(2).strip().replace("\n", " ")
        metadata["case_name"] = f"{appellant} vs {respondent}"

    # Court
    if "SUPREME COURT OF INDIA" in text.upper():
        metadata["court"] = "Supreme Court of India"
    elif "HIGH COURT" in text.upper():
        hc_match = re.search(r"High Court of[\w\s]+", text, re.IGNORECASE)
        metadata["court"] = hc_match.group().strip() if hc_match else "High Court"

    # Date (e.g., JANUARY 20, 2026)
    date_match = re.search(
        r"(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|"
        r"SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2},?\s+\d{4}",
        text, re.IGNORECASE
    )
    if date_match:
        metadata["date"] = date_match.group().strip().title()

    return metadata


def extract_sections(text: str) -> dict:
    """Extract structured sections from legal case text."""
    sections = {
        "acts_sections": [],
        "lower_court_history": [],
        "appellant_arguments": [],
        "respondent_arguments": [],
        "court_findings": [],
        "final_decision": "",
        "judges": [],
    }

    # Acts and Sections referenced
    acts = re.findall(
        r"Section\s+[\d\w\(\)]+\s+of\s+(?:the\s+)?[\w\s,]+Act[\w\s,\d]*",
        text, re.IGNORECASE
    )
    sections["acts_sections"] = list(set(acts[:10]))  # deduplicate, limit 10

    # Judge names (J. pattern)
    judges = re.findall(r"([A-Z][A-Z\s]+),?\s+J\.", text)
    sections["judges"] = list(set([j.strip().title() for j in judges]))

    # Final decision keywords
    if "appeals are, accordingly, dismissed" in text.lower():
        sections["final_decision"] = "Appeals Dismissed"
    elif "appeals are allowed" in text.lower():
        sections["final_decision"] = "Appeals Allowed"
    elif "petition dismissed" in text.lower():
        sections["final_decision"] = "Petition Dismissed"
    elif "matter remanded" in text.lower():
        sections["final_decision"] = "Matter Remanded"

    return sections


def build_structured_summary(raw_summary: str, original_text: str) -> dict:
    """
    Combine metadata extraction + raw LED summary into structured output.
    Returns a dict with all sections for the UI to render.
    """
    metadata = extract_case_metadata(original_text)
    sections = extract_sections(original_text)

    return {
        "metadata": metadata,
        "raw_summary": raw_summary,
        "acts_sections": sections["acts_sections"],
        "final_decision": sections["final_decision"],
        "judges": sections["judges"],
    }