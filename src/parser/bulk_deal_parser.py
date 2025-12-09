# src/parser/bulk_deal_parser.py

from .base import BaseParser
import camelot
import pdfplumber

class BulkDealParser(BaseParser):
    """
    Detects Bulk Deal documents and parses tables into structured JSON.
    """

    KEYWORDS = [
        "bulk deal", "bulk transaction", "trading", "securities",
        "shares acquired", "acquirer", "date of transaction"
    ]

    def detect(self, text: str) -> bool:
        """
        Detect if this PDF is a Bulk Deal document based on keyword matching.
        """
        txt_lower = text.lower()
        return any(k in txt_lower for k in self.KEYWORDS)

    def parse(self, text: str):
        """
        Parse the bulk deal PDF into structured JSON.
        Uses camelot for table extraction if tables exist.
        """
        # Basic metadata
        result = {
            "document_type": "bulk_deal",
            "metadata": {},
            "records": [],
            "data_quality": {
                "completeness_score": 0.0,
                "validation_warnings": []
            }
        }

        # Attempt table extraction using camelot
        try:
            # Parse all pages with camelot
            tables = camelot.read_pdf(self.pdf_path, pages='all', flavor='stream')
            if tables:
                records = []
                for table in tables:
                    df = table.df
                    # Skip empty tables
                    if df.empty:
                        continue
                    # Convert rows to dicts: first row as header
                    headers = df.iloc[0].tolist()
                    for idx in range(1, len(df)):
                        row = df.iloc[idx].tolist()
                        record = {headers[i]: row[i] for i in range(len(headers))}
                        records.append(record)
                result["records"] = records
                result["data_quality"]["completeness_score"] = 1.0 if records else 0.5
            else:
                # Fallback: just return full text
                result["records"] = [{"text": text[:2000]}]
                result["data_quality"]["completeness_score"] = 0.3

        except Exception as e:
            # Fallback: just return text
            result["records"] = [{"text": text[:2000]}]
            result["data_quality"]["validation_warnings"].append(
                f"Camelot table extraction failed: {str(e)}"
            )
            result["data_quality"]["completeness_score"] = 0.3

        return result

    def name(self) -> str:
        return "bulk_deal"
