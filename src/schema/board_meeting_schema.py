# src/schema/board_meeting_schema.py
import sys
parent_directory = 'C:/Users/Tvari/Desktop/personal/pdf_parsing/src'
sys.path.append(parent_directory)
from pydantic import BaseModel, Field
from typing import List, Optional

class BoardMeetingSchema(BaseModel):
    document_type: str = "board_meeting"
    metadata: dict = Field(default_factory=dict)  # company_name, meeting_date, announcement_date, source_url
    resolutions: List[str] = []
    data_quality: dict = {"score": 0.0, "errors": []}
