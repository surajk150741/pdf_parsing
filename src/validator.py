# src/validator.py
from typing import Tuple, Any, Dict, List
from pydantic import ValidationError
from schema.macro_schema import MacroSchema
from schema.bulk_deal_schema import BulkDealSchema
from schema.board_meeting_schema import BoardMeetingSchema
from schema.shareholding_schema import ShareholdingSchema

# Map parser name -> schema class
SCHEMA_MAP = {
    "bulk_deal": BulkDealSchema,
    "board_meeting": BoardMeetingSchema,
    "shareholding_pattern": ShareholdingSchema,
    "macro_report": MacroSchema,
    "generic": None,  # no strict schema for generic
}

def compute_score_and_errors(parser_name: str, raw: dict) -> Tuple[float, List[str]]:
    """
    Basic scoring:
     - start at 1.0
     - deduct for missing important blocks (heuristics)
    Returns (score, error_list)
    """
    score = 1.0
    errors = []

    if parser_name == "generic":
        score -= 0.30
        errors.append("Used generic parser; structured extraction not attempted.")

    if parser_name == "bulk_deal":
        recs = raw.get("records") or []
        if not recs:
            score -= 0.20
            errors.append("No records found in bulk_deal.")
        md = raw.get("metadata", {})
        if not md.get("company_name"):
            score -= 0.10
            errors.append("company_name missing in metadata.")

    elif parser_name == "board_meeting":
        res = raw.get("resolutions") or []
        if not res:
            score -= 0.20
            errors.append("No resolutions extracted.")
        md = raw.get("metadata", {})
        if not md.get("company_name"):
            score -= 0.10
            errors.append("company_name missing in metadata.")
        if not md.get("meeting_date"):
            score -= 0.10
            errors.append("meeting_date missing in metadata.")

    elif parser_name == "shareholding_pattern":
        sh = raw.get("shareholders") or []
        if not sh:
            score -= 0.20
            errors.append("No shareholder rows extracted.")
        md = raw.get("metadata", {})
        if not md.get("company_name"):
            score -= 0.10
            errors.append("company_name missing in metadata.")

    elif parser_name == "macro_report":
        # heuristics for macro reports
        sections = raw.get("sections") or []
        tables = raw.get("tables") or []
        # if sections are empty or only have very short bodies, penalize
        if not sections:
            score -= 0.25
            errors.append("No sections detected in macro_report.")
        else:
            # penalize if all sections have empty body
            non_empty = any((s.get("body_cn") or s.get("body_en")) for s in sections)
            if not non_empty:
                score -= 0.15
                errors.append("Sections present but bodies appear empty.")
        if not tables:
            score -= 0.25
            errors.append("No tables detected/extracted.")
        # also check if title is present
        md_title = raw.get("title_cn") or raw.get("title_en")
        if not md_title:
            score -= 0.10
            errors.append("Title not extracted.")

    # clamp score
    score = max(0.0, round(score, 2))
    return score, errors

def validate_and_score(parser_name: str, parsed_output: dict, source_url: str = "") -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate parsed_output against schema (if available).
    Returns:
      - validated_json (possibly augmented with data_quality)
      - errors (list of strings)
    """
    schema_cls = SCHEMA_MAP.get(parser_name)

    # attach source_url if present
    if isinstance(parsed_output, dict):
        md = parsed_output.setdefault("metadata", {})
        if source_url:
            md.setdefault("source_url", source_url)

    errors: List[str] = []
    validated = parsed_output.copy() if isinstance(parsed_output, dict) else {"document_type": parser_name, "metadata": {}, "records": [], "data_quality": {}}

    # If there is a schema, try to validate/normalize using it
    if schema_cls is not None:
        try:
            model = schema_cls.parse_obj(validated)
            # use model.dict() to get normalized data
            validated = model.model_dump()
        except ValidationError as ve:
            # Collect pydantic errors
            errs = ve.errors() if hasattr(ve, "errors") else [str(ve)]
            for e in errs:
                errors.append(str(e))
            # don't fail; keep raw validated as-is
    # else: generic - no validation

    # Compute score and warnings
    score, heuristic_errors = compute_score_and_errors(parser_name, validated)
    errors.extend(heuristic_errors)

    # Attach data_quality
    dq = validated.get("data_quality", {})
    dq["score"] = score
    if errors:
        dq["errors"] = errors
    else:
        dq["errors"] = []
    validated["data_quality"] = dq

    return validated, errors
