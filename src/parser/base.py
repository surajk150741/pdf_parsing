# src/parser/base.py
import sys
parent_directory = 'C:/Users/Tvari/Desktop/personal/pdf_parsing/src'
sys.path.append(parent_directory)
from abc import ABC, abstractmethod

class BaseParser(ABC):
    """
    Abstract parser class that each document-type parser must implement.
    """

    @abstractmethod
    def detect(self, text: str) -> bool:
        """Return True if this parser is suitable for the given PDF text."""
        pass

    @abstractmethod
    def parse(self, text: str):
        """
        Parse text and return a structured Python dict.
        Should match the final JSON schema.
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """Return parser/document type name."""
        pass
