#!/usr/bin/env python3
"""
Downloader + parser with document type detection + validation
Usage:
    python src/downloader.py input.csv

Outputs:
    output/pdfs/
    output/txts/
    output/json/
    output/logs/report.csv
"""
import csv
import re
import sys
from pathlib import Path
import json
import requests

# PDF parsers
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except:
    HAS_PDFPLUMBER = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except:
    HAS_PYPDF = False

# Document parsers
from parser.detector import DocumentDetector
from parser.bulk_deal_parser import BulkDealParser
from parser.board_meeting_parser import BoardMeetingParser
from parser.shareholding_parser import ShareholdingPatternParser
from parser.macro_parser import MacroEconomicParser
from parser.generic_parser import GenericParser

# Validator
from validator import validate_and_score

URL_PDF_RE = re.compile(r'https?://[^\s,\]\)"\']+?\.pdf', re.IGNORECASE)

# -------------------------------
# Extract PDF URLs
# -------------------------------
def extract_pdf_urls(text: str):
    if not text:
        return []
    return URL_PDF_RE.findall(text)

# -------------------------------
# Download PDF
# -------------------------------
def download_pdf(url: str, dest_path: Path) -> (bool, str):
    headers = {"User-Agent": "Mozilla/5.0 (PDF Downloader)"}
    try:
        with requests.get(url, headers=headers, stream=True, timeout=25) as r:
            r.raise_for_status()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
        return True, ""
    except Exception as e:
        return False, str(e)

# -------------------------------
# Parse PDF to text
# -------------------------------
def parse_pdf(pdf_path: Path) -> (bool, str, str):
    try:
        if HAS_PDFPLUMBER:
            try:
                texts = []
                with pdfplumber.open(pdf_path) as pdf:
                    for p in pdf.pages:
                        t = p.extract_text()
                        if t:
                            texts.append(t)
                return True, "\n\n".join(texts), ""
            except Exception as e:
                err = f"pdfplumber failed: {str(e)}"
        else:
            err = "pdfplumber not installed"

        if HAS_PYPDF:
            try:
                reader = PdfReader(str(pdf_path))
                texts = []
                for p in reader.pages:
                    try:
                        t = p.extract_text()
                        if t:
                            texts.append(t)
                    except:
                        pass
                return True, "\n\n".join(texts), err
            except Exception as e:
                return False, "", f"pypdf failed: {err} | {str(e)}"

        return False, "", "No PDF parser available"
    except Exception as e:
        return False, "", str(e)

# -------------------------------
# Sanitize filename
# -------------------------------
def clean_filename(name: str) -> str:
    keep = (" ", ".", "_", "-")
    return "".join(c for c in name if c.isalnum() or c in keep).rstrip()

# -------------------------------
# Main pipeline
# -------------------------------
def main(csv_file: str):

    csv_path = Path(csv_file)
    out = Path("output")
    pdf_dir = out / "pdfs"
    txt_dir = out / "txts"
    json_dir = out / "json"
    log_dir = out / "logs"

    pdf_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    report_path = log_dir / "report.csv"

    # Initialize detector with all three parsers
    detector = DocumentDetector(parsers=[
        MacroEconomicParser(),
        BulkDealParser(),
        BoardMeetingParser(),
        ShareholdingPatternParser()
    ])

    # CSV headers for logging (now include validation score/errors)
    with open(report_path, "w", newline="", encoding="utf-8") as logf:
        csv.writer(logf).writerow([
            "url", "filename", "download_status",
            "parse_status", "parser_used", "validation_score", "validation_errors", "error_message"
        ])

    seen = set()
    total_urls = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            joined = " ".join(row)
            urls = extract_pdf_urls(joined)

            for url in urls:
                url = url.strip()
                if url in seen:
                    continue
                seen.add(url)
                total_urls += 1

                print(f"\n[{total_urls}] Processing: {url}")

                # Filename
                raw_name = Path(url).name
                filename = clean_filename(raw_name)
                if not filename.lower().endswith(".pdf"):
                    filename += ".pdf"

                dest_pdf = pdf_dir / filename

                counter = 1
                while dest_pdf.exists():
                    dest_pdf = pdf_dir / f"{filename[:-4]}_{counter}.pdf"
                    counter += 1

                # === DOWNLOAD ===
                dl_success, dl_error = download_pdf(url, dest_pdf)
                if not dl_success:
                    print(f"  ❌ Download failed: {dl_error}")
                    with open(report_path, "a", newline="", encoding="utf-8") as logf:
                        csv.writer(logf).writerow([
                            url, dest_pdf.name, "failed", "skipped_not_downloaded", "none", "", dl_error
                        ])
                    continue
                print(f"  ✔ Downloaded: {dest_pdf.name}")

                # === PARSE + DETECTION ===
                validation_score = ""
                validation_errors = ""
                try:
                    parse_success, text, parse_error = parse_pdf(dest_pdf)
                    if not parse_success:
                        parser_used = "none"
                        parsed_output = None
                        print(f"  ❌ Parsing failed: {parse_error}")
                    else:
                        parser_class = detector.detect(text)
                        # Pass PDF path to parser if it needs it (for table parsers)
                        if hasattr(parser_class, 'pdf_path'):
                            parser_class.pdf_path = dest_pdf
                        parser_used = parser_class.name()
                        parsed_output = parser_class.parse(text)

                        # Run validator
                        validated_json, errors = validate_and_score(parser_used, parsed_output, source_url=url)
                        validation_score = validated_json.get("data_quality", {}).get("score", "")
                        validation_errors = "; ".join(errors) if errors else ""

                        # Save TXT
                        txt_path = txt_dir / (dest_pdf.stem + ".txt")
                        with open(txt_path, "w", encoding="utf-8") as tf:
                            tf.write(text)

                        # Save validated JSON
                        json_path = json_dir / (dest_pdf.stem + ".json")
                        with open(json_path, "w", encoding="utf-8") as jf:
                            jf.write(json.dumps(validated_json, indent=2))

                        print(f"  ✔ Parsed using: {parser_used} | validation_score={validation_score}")

                except Exception as e:
                    parse_success = False
                    parse_error = str(e)
                    parser_used = "error"
                    print(f"  ❌ Exception during parse/validation: {parse_error}")

                # === LOG ===
                with open(report_path, "a", newline="", encoding="utf-8") as logf:
                    csv.writer(logf).writerow([
                        url,
                        dest_pdf.name,
                        "success" if dl_success else "failed",
                        "success" if parse_success else "failed",
                        parser_used,
                        validation_score,
                        validation_errors,
                        parse_error if not parse_success else ""
                    ])

    print("\n=====================================")
    print("Pipeline Completed.")
    print(f"Total unique URLs found: {total_urls}")
    print(f"Full report saved to: {report_path}")
    print("=====================================")

# -------------------------------
# Entry
# -------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/downloader.py input.csv")
        sys.exit(1)
    main(sys.argv[1])
