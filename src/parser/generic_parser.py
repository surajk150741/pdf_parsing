# src/parser/generic_parser.py
import sys
parent_directory = 'C:/Users/Tvari/Desktop/personal/pdf_parsing/src'
sys.path.append(parent_directory)
from .base import BaseParser

class GenericParser(BaseParser):

    def detect(self, text: str) -> bool:
        # Always default to true as fallback
        return True

    def parse(self, text: str):
        return {
            "document_type": "generic",
            "full_text": text,
            "metadata": {},
            "records": [],
            "data_quality": {
                "completeness_score": 0.2,
                "validation_warnings": [
                    "Generic extraction only. No structured fields."
                ]
            }
        }

    def name(self) -> str:
        return "generic"
