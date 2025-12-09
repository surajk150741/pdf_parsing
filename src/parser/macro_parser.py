import re
import camelot
import pdfplumber
from deep_translator import GoogleTranslator
from parser.base import BaseParser


def translate_text(text: str) -> str:
    if not text or not text.strip():
        return ""
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except:
        return text  # fail gracefully


def parse_table_from_text(text: str):
    """
    Parse whitespace-separated PBoC-style textual tables from raw extracted text.
    This is critical for macroeconomic reports where tables are NOT real PDF tables.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    parsed_tables = []

    number_regex = re.compile(r"^-?[\d,]+(\.\d+)?$")

    for idx, line in enumerate(lines):
        parts = line.split()
        if len(parts) < 3:
            continue

        # Look ahead to detect numeric lines
        lookahead = lines[idx + 1: idx + 6]
        numeric_rows_found = 0

        for la in lookahead:
            tokens = la.split()
            num_tokens = sum(1 for t in tokens if number_regex.match(t))
            if num_tokens >= 2:
                numeric_rows_found += 1

        if numeric_rows_found == 0:
            continue

        # This line is likely a header
        headers = parts
        rows = []

        for j in range(idx + 1, len(lines)):
            row_parts = lines[j].split()
            num_count = sum(1 for t in row_parts if number_regex.match(t))

            if num_count >= 1 and len(row_parts) >= 2:
                rows.append(row_parts)
            else:
                break

        # Normalize row dicts
        dict_rows = []
        for r in rows:
            if len(r) > len(headers):
                delta = len(r) - len(headers)
                first_col = " ".join(r[:delta + 1])
                remaining = r[delta + 1:]
                row_vals = [first_col] + remaining
            else:
                row_vals = r

            if len(row_vals) == len(headers):
                dict_rows.append({headers[i]: row_vals[i] for i in range(len(headers))})
            else:
                # best-effort
                header_map = {}
                header_map[headers[0]] = " ".join(row_vals[:- (len(headers) - 1)]) if len(row_vals) >= len(headers) else row_vals[0]
                numeric_only = row_vals[-(len(headers) - 1):]
                for i, tok in enumerate(numeric_only, start=1):
                    header_map[headers[i]] = tok
                dict_rows.append(header_map)

        if dict_rows:
            parsed_tables.append({
                "title_cn": headers[0],
                "title_en": translate_text(headers[0]),
                "headers_cn": headers,
                "headers_en": [translate_text(h) for h in headers],
                "rows": dict_rows
            })

    return parsed_tables


class MacroEconomicParser(BaseParser):
    """
    Parser for macroeconomic reports from PBoC (People’s Bank of China).
    These reports have:
    - Chinese headings
    - Multiple sections with numbered titles
    - Text-based tables (NOT real tables)
    """

    def name(self):
        return "macro_report"
    
    def matches(self, text: str) -> bool:
        """
        Detect macro reports using characteristic Chinese terms.
        """
        keywords = [
            "中国人民银行",
            "景气指数",
            "价格指数",
            "预期指数",
            "城镇居民", 
            "消费", 
            "价格", 
            "就业",
            "收入"
        ]
        return any(kw in text for kw in keywords)
    
    def detect(self, text: str) -> bool:
        return self.matches(text)


    def parse(self, text: str, pdf_path=None):
        self.pdf_path = pdf_path
        pdf_text = text

        result = {
            "document_type": "macro_report",
            "metadata": {
                "source": "People's Bank of China",
                "language": "zh-cn",
                "translated": True
            },
            "title_cn": "",
            "title_en": "",
            "sections": [],
            "tables": [],
            "summary": "",
            "data_quality": {
                "score": 0.0,
                "errors": [],
                "notes": []
            }
        }

        # --- Extract Title ---
        m = re.search(r"^\s*(.+?报告.*)", pdf_text.split("\n")[0].strip())
        if m:
            result["title_cn"] = m.group(1).strip()
            result["title_en"] = translate_text(result["title_cn"])

        # --- Extract Sections ---
        sections = []
        section_matches = re.finditer(r"(\d[\.、]\s*[^\n]+)", pdf_text)
        section_headers = [(m.start(), m.group(1)) for m in section_matches]

        for i, (pos, header) in enumerate(section_headers):
            start = pos
            end = section_headers[i + 1][0] if i + 1 < len(section_headers) else len(pdf_text)
            body_cn = pdf_text[start:end].split("\n", 1)
            body_cn = body_cn[1] if len(body_cn) > 1 else ""

            sections.append({
                "title_cn": header.strip(),
                "title_en": translate_text(header.strip()),
                "body_cn": body_cn.strip(),
                "body_en": translate_text(body_cn.strip()) if body_cn.strip() else ""
            })

        result["sections"] = sections

        # --- Extract Summary (first Chinese paragraph) ---
        paragraphs = [p.strip() for p in pdf_text.split("\n") if p.strip()]
        if paragraphs:
            result["summary"] = translate_text(paragraphs[0])

        # --- TABLE EXTRACTION PIPELINE ---
        tables_parsed = []
        table_count = 0

        # 1) Try Camelot
        if pdf_path:
            try:
                camelot_tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")
                if camelot_tables:
                    for tbl in camelot_tables:
                        df = tbl.df
                        if df.empty:
                            continue
                        headers = [h.strip() for h in df.iloc[0].tolist()]
                        rows = []
                        for ridx in range(1, len(df)):
                            row = [c.strip() for c in df.iloc[ridx].tolist()]
                            rows.append({headers[i]: row[i] for i in range(len(headers))})

                        tables_parsed.append({
                            "title_cn": headers[0],
                            "title_en": translate_text(headers[0]),
                            "headers_cn": headers,
                            "headers_en": [translate_text(h) for h in headers],
                            "rows": rows
                        })
                        table_count += 1
            except:
                result["data_quality"]["notes"].append("Camelot failed")

        # 2) Try pdfplumber
        if table_count == 0 and pdf_path:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for p in pdf.pages:
                        tbls = p.extract_tables()
                        if not tbls:
                            continue
                        for table in tbls:
                            headers = [str(h).strip() for h in table[0]]
                            rows = []
                            for row in table[1:]:
                                rows.append({headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))})

                            tables_parsed.append({
                                "title_cn": headers[0],
                                "title_en": translate_text(headers[0]),
                                "headers_cn": headers,
                                "headers_en": [translate_text(h) for h in headers],
                                "rows": rows
                            })
                            table_count += 1
            except:
                result["data_quality"]["notes"].append("pdfplumber failed")

        # 3) Final Fallback — TEXT-BASED TABLE EXTRACTION
        if table_count == 0:
            text_tables = parse_table_from_text(pdf_text)
            if text_tables:
                tables_parsed.extend(text_tables)
                table_count = len(text_tables)

        result["tables"] = tables_parsed

        return result
