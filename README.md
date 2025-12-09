Macroeconomic PDF Parsing & Search System
Automated Financial Document Extraction + Search System Architecture (Hiring Task Solution)
<p align="center"> <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" /> <img src="https://img.shields.io/badge/Parsing-PDFplumber%20%7C%20Camelot-green" /> <img src="https://img.shields.io/badge/Translation-LLM%20Enhanced-orange" /> <img src="https://img.shields.io/badge/Tests-Pytest-red" /> <img src="https://img.shields.io/badge/Status-Production%20Ready-brightgreen" /> <img src="https://img.shields.io/badge/Architecture-LLM%20Search%20System-purple" /> </p>
Overview

This project builds an automated pipeline for:

1. Downloading financial/macro-economic PDFs

2. Extracting text & tables (including Chinese-language documents)

3. Translating & structuring the content

4. Producing clean JSON outputs

5. Validating output quality

6. Designing a full LLM-powered financial search system.


**Key Features**
1. End-to-End PDF Parsing Pipeline

   1. Automatic PDF downloading
   2. Text extraction using pdfplumber
   3. Table extraction using Camelot
   4. Chinese → English translation
   5. Title/section detection
   6. Clean JSON outputs
   7. Robust logging

2. Modular Parser Framework
   1. MacroEconomicParser:	Extracts macro-economic reports (Chinese/English): Used
   2. GenericParser:	Fallback for unknown file formats: Used
   3. BulkDealParser:	Parses stock bulk deal disclosures: Not required for current task
   4. BoardMeetingParser:	Parses board meeting announcements: Not required for current task
   5. ShareholdingPatternParser:	Parses shareholding pattern filings: Not required for current task
  
**Why keep the unused parsers?**

- Even though BulkDealParser, BoardMeetingParser, and ShareholdingPatternParser are not used for the uploaded macroeconomic PDFs, these formats commonly appear in financial scraping pipelines.

**Keeping them offers:**

- Future extensibility

- Support for regulatory filings (SEBI/Exchange)

- Ability to expand system into a full “financial document processor”

- Faster onboarding of new document types

- They do not interfere with the current macroeconomic PDF flow and can remain safely.

**JSON Validation + Scoring**

The **validator.py** file:

- Enforces schema correctness

- Checks essential fields

- Ensures translations exist

- Verifies table extraction results

- Produces a validation score (0–1)

- Used in the pipeline for logging quality

- Includes pytest-based unit tests.

**Output Structure**

Every processed file generates:

- Extracted Text:	/output/txts/*.txt
- Structured JSON:	/output/json/*.json
- Original PDF:	/output/pdfs/*.pdf
- Pipeline Logs:	/output/logs/

**Running the Pipeline**

1. Create and activate a virtual environment
   
   1. python -m venv venv
   2. venv\Scripts\activate     # Windows
   3. source venv/bin/activate  # Mac/Linux

2. Install dependencies

   1. pip install -r requirements.txt

3. Run

   1. python src/downloader.py Documents.csv

**Search System Architecture**

- A full solution is documented and a flow chart is drawn in following miro flaw chat board: **[pdf_parser_board]([https://github.com/your-repo-link-here](https://miro.com/welcomeonboard/QkJSOWlBQzNCNVM1WG1RSFJiOFdsVjlWMDdGU3kvaG1qUWh0TFN2cnJvQ2VtYjg5bWJaUitWWG5GekdjRHQvT3g4WnNtOGl1WitOOVpzcW5yWC9UOGNUOFVOVjlzV1k0cktIZHk3M2c0bDZ6R3hJNmpjaTlObVlUaW9JVXcvajByVmtkMG5hNDA3dVlncnBvRVB2ZXBnPT0hdjE=?share_link_id=798986267253))**
