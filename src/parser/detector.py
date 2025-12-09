# src/parser/detector.py
from .bulk_deal_parser import BulkDealParser
from .board_meeting_parser import BoardMeetingParser
from .shareholding_parser import ShareholdingPatternParser
from .macro_parser import MacroEconomicParser
from .generic_parser import GenericParser

class DocumentDetector:

    def __init__(self, parsers: list = None):
        if parsers is None:
            # macro parser first so macro reports are detected before finance parsers
            self.parsers = [
                MacroEconomicParser(),
                BulkDealParser(),
                BoardMeetingParser(),
                ShareholdingPatternParser()
            ]
        else:
            self.parsers = parsers
        self.generic = GenericParser()

    def detect(self, text: str):
        for parser in self.parsers:
            try:
                if parser.detect(text):
                    return parser
            except Exception:
                continue
        return self.generic
