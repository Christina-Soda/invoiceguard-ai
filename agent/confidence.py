# agent/confidence.py

from __future__ import annotations

from typing import Any

from .schemas import get_field_confidence, get_field_value


FIELD_CONFIDENCE_TO_SCORE = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.35,
    None: 0.5,
}


def compute_confidence_v1(
    vlm_confidence: float | None,
    schema_valid: bool,
    rule_results: list[dict[str, Any]],
    fields: dict[str, Any],
    *,
    parse_success: bool = True,
) -> tuple[float, float, dict[str, float]]:
    """
    Teacher-aligned baseline confidence score.

    Returns:
        confidence_0_1
        confidence_0_10
        breakdown

    The teacher suggested a simple 0-10 interpretation:
        0-2   -> reject
        3-7   -> need_human_review
        8-10  -> approve

    Internally we compute 0-1 and expose 0-10 for reporting.
    """
    critical_required = ["vendor_name", "invoice_date", "total"]

    if not parse_success:
        breakdown = {
            "parse_score": 0.0,
            "vlm_self_confidence": 0.0,
            "schema_score": 0.0,
            "rule_score": 0.0,
            "completeness_score": 0.0,
            "field_confidence_score": 0.0,
        }
        return 0.0, 0.0, breakdown

    present = 0
    field_scores: list[float] = []

    for name in critical_required:
        field = fields.get(name)
        value = get_field_value(field)

        if value is not None and str(value).strip() != "":
            present += 1

        confidence_label = get_field_confidence(field)
        field_scores.append(FIELD_CONFIDENCE_TO_SCORE.get(confidence_label, 0.5))

    completeness_score = present / len(critical_required)
    field_confidence_score = sum(field_scores) / len(field_scores)

    critical_fails = sum(
        1 for r in rule_results
        if r.get("status") == "fail" and r.get("severity") == "critical"
    )
    high_fails = sum(
        1 for r in rule_results
        if r.get("status") == "fail" and r.get("severity") == "high"
    )
    high_warnings = sum(
        1 for r in rule_results
        if r.get("status") == "warning" and r.get("severity") == "high"
    )
    medium_warnings = sum(
        1 for r in rule_results
        if r.get("status") == "warning" and r.get("severity") == "medium"
    )

    rule_score = max(
        0.0,
        1.0
        - critical_fails * 0.50
        - high_fails * 0.30
        - high_warnings * 0.20
        - medium_warnings * 0.10,
    )

    parse_score = 1.0
    schema_score = 1.0 if schema_valid else 0.55
    vlm_score = normalize_vlm_confidence(vlm_confidence)

    breakdown = {
        "parse_score": parse_score,
        "vlm_self_confidence": vlm_score,
        "schema_score": schema_score,
        "rule_score": rule_score,
        "completeness_score": completeness_score,
        "field_confidence_score": field_confidence_score,
    }

    weights = {
        "parse_score": 0.10,
        "vlm_self_confidence": 0.15,
        "schema_score": 0.15,
        "rule_score": 0.35,
        "completeness_score": 0.15,
        "field_confidence_score": 0.10,
    }

    confidence_0_1 = sum(breakdown[k] * weights[k] for k in weights)
    confidence_0_1 = round(clamp01(confidence_0_1), 3)
    confidence_0_10 = round(confidence_0_1 * 10.0, 1)

    return confidence_0_1, confidence_0_10, breakdown


def normalize_vlm_confidence(vlm_confidence: float | None) -> float:
    """
    Accept either 0-1 or 0-10 VLM confidence.
    """
    if vlm_confidence is None:
        return 0.5

    value = float(vlm_confidence)

    if value > 1.0:
        value = value / 10.0

    return clamp01(value)


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))
