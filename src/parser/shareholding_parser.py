# src/parser/shareholding_parser.py

from .base import BaseParser
import camelot
import re

class ShareholdingPatternParser(BaseParser):
    """
    Detects Shareholding Pattern PDFs and parses tables into structured JSON.
    """

    KEYWORDS = [
        "shareholding pattern", "shareholding", "shareholders", "category",
        "percentage", "promoter", "public", "fiis"
    ]

    def detect(self, text: str) -> bool:
        txt_lower = text.lower()
        return any(k in txt_lower for k in self.KEYWORDS)

    def parse(self, text: str):
        """
        Parse the PDF into structured JSON representing shareholding details.
        Uses camelot for table extraction.
        """
        result = {
            "document_type": "shareholding_pattern",
            "metadata": {},
            "records": [],
            "data_quality": {
                "completeness_score": 0.0,
                "validation_warnings": []
            }
        }

        records = []

        # Attempt table extraction with camelot
        try:
            tables = camelot.read_pdf(self.pdf_path, pages='all', flavor='stream')
            if tables:
                for table in tables:
                    df = table.df
                    if df.empty:
                        continue

                    # Use first row as header
                    headers = df.iloc[0].tolist()
                    for idx in range(1, len(df)):
                        row = df.iloc[idx].tolist()
                        # Skip empty rows
                        if all(not cell.strip() for cell in row):
                            continue
                        record = {headers[i]: row[i] for i in range(len(headers))}
                        records.append(record)

                result["records"] = records
                result["data_quality"]["completeness_score"] = 1.0 if records else 0.5

            else:
                # Fallback: store first 1000 chars of text
                result["records"] = [{"text": text[:1000]}]
                result["data_quality"]["completeness_score"] = 0.3
                result["data_quality"]["validation_warnings"].append("No tables found")

        except Exception as e:
            result["records"] = [{"text": text[:1000]}]
            result["data_quality"]["completeness_score"] = 0.3
            result["data_quality"]["validation_warnings"].append(
                f"Camelot table extraction failed: {str(e)}"
            )

        return result

    def name(self) -> str:
        return "shareholding_pattern"
