# src/parser/board_meeting_parser.py

from .base import BaseParser
import re

class BoardMeetingParser(BaseParser):
    """
    Detects Board Meeting PDFs and parses key information.
    """

    KEYWORDS = [
        "board meeting", "agenda", "resolution", "company name",
        "meeting held on", "minutes of meeting"
    ]

    DATE_REGEX = r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"  # Simple DD-MM-YYYY or DD/MM/YYYY

    def detect(self, text: str) -> bool:
        """
        Detect if PDF is a Board Meeting document using keyword matching.
        """
        txt_lower = text.lower()
        return any(k in txt_lower for k in self.KEYWORDS)

    def parse(self, text: str):
        """
        Parse Board Meeting PDF and extract structured metadata.
        """
        result = {
            "document_type": "board_meeting",
            "metadata": {},
            "records": [],
            "data_quality": {
                "completeness_score": 0.0,
                "validation_warnings": []
            }
        }

        # Attempt to extract company name heuristically
        company_match = re.search(r"Company\s*Name[:\-]\s*(.+)", text, re.IGNORECASE)
        company = company_match.group(1).strip() if company_match else ""

        # Attempt to extract meeting date
        date_match = re.search(self.DATE_REGEX, text)
        meeting_date = date_match.group(0) if date_match else ""

        # Attempt to extract agenda/subject lines
        agenda_matches = re.findall(r"(Agenda|Subject)[:\-]\s*(.+)", text, re.IGNORECASE)
        agenda_list = [a[1].strip() for a in agenda_matches] if agenda_matches else []

        # Attempt to extract resolutions
        resolution_matches = re.findall(r"Resolution[:\-]\s*(.+)", text, re.IGNORECASE)
        resolutions = [r.strip() for r in resolution_matches] if resolution_matches else []

        # Fill metadata
        result["metadata"] = {
            "company_name": company,
            "meeting_date": meeting_date,
            "num_resolutions": len(resolutions)
        }

        # Fill records with each resolution
        for idx, res in enumerate(resolutions, start=1):
            record = {
                "resolution_number": idx,
                "resolution_text": res
            }
            result["records"].append(record)

        # Data quality scoring
        completeness = 0.0
        warnings = []

        if company:
            completeness += 0.3
        else:
            warnings.append("Company name not found")

        if meeting_date:
            completeness += 0.3
        else:
            warnings.append("Meeting date not found")

        if resolutions:
            completeness += 0.4
        else:
            warnings.append("No resolutions found")

        result["data_quality"]["completeness_score"] = round(completeness, 2)
        result["data_quality"]["validation_warnings"] = warnings

        return result

    def name(self) -> str:
        return "board_meeting"
