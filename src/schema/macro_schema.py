# src/schema/macro_schema.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class MacroTable(BaseModel):
    title_cn: Optional[str]
    title_en: Optional[str]
    headers_cn: Optional[List[str]] = []
    headers_en: Optional[List[str]] = []
    rows: List[Dict[str, Any]] = []

class MacroSection(BaseModel):
    heading_cn: Optional[str]
    heading_en: Optional[str]
    body_cn: Optional[str]
    body_en: Optional[str]

class MacroSchema(BaseModel):
    document_type: str = "macro_report"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    title_cn: Optional[str] = None
    title_en: Optional[str] = None
    sections: List[MacroSection] = []
    tables: List[MacroTable] = []
    summary_en: Optional[str] = ""
    data_quality: Dict[str, Any] = Field(default_factory=dict)
