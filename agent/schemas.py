# agent/schemas.py

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


DecisionLabel = Literal["approve", "need_human_review", "reject"]
FieldConfidenceLabel = Literal["high", "medium", "low"]


def normalize_confidence_label(value: Any) -> FieldConfidenceLabel | None:
    """
    Normalize confidence from either:
      - string labels: high / medium / low
      - numeric scores: 0-1 or 0-10

    Examples:
      0.9  -> high
      0.7  -> medium
      0.3  -> low
      9    -> high
      "0.9" -> high
    """
    if value is None:
        return None

    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"high", "medium", "low"}:
            return text  # type: ignore[return-value]

        try:
            numeric = float(text)
        except ValueError:
            return None
    elif isinstance(value, (int, float)):
        numeric = float(value)
    else:
        return None

    # Support 0-10 confidence.
    if numeric > 1.0:
        numeric = numeric / 10.0

    if numeric >= 0.8:
        return "high"
    if numeric >= 0.5:
        return "medium"
    return "low"


class FieldWithEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: str | float | int | None = None
    evidence: str | None = None
    bounding_box: list[float] | str | None = None
    confidence: FieldConfidenceLabel | None = None

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, value: Any):
        return normalize_confidence_label(value)


class LineItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: str | None = None
    quantity: float | str | None = None
    unit_price: float | str | None = None
    amount: float | str | None = None
    evidence: str | None = None
    bounding_box: list[float] | str | None = None
    confidence: FieldConfidenceLabel | None = None

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, value: Any):
        return normalize_confidence_label(value)

    @model_validator(mode="after")
    def check_line_item_math(self):
        qty = to_float(self.quantity)
        unit = to_float(self.unit_price)
        amount = to_float(self.amount)

        if qty is None or unit is None or amount is None:
            return self

        expected = round(qty * unit, 2)
        if abs(expected - amount) > 0.05:
            raise ValueError(
                f"Line item math mismatch: {qty} * {unit} = {expected}, got {amount}"
            )
        return self


class InvoiceSchema(BaseModel):
    """
    Flexible schema for receipt/invoice extraction.

    SROIE receipts often only have vendor_name, invoice_date, total, and address.
    Therefore invoice_number is allowed but not required.
    """

    model_config = ConfigDict(extra="ignore")

    vendor_name: FieldWithEvidence | None = None
    vendor_address: FieldWithEvidence | None = None
    invoice_number: FieldWithEvidence | None = None
    invoice_date: FieldWithEvidence | None = None
    due_date: FieldWithEvidence | None = None
    subtotal: FieldWithEvidence | None = None
    tax: FieldWithEvidence | None = None
    shipping: FieldWithEvidence | None = None
    discount: FieldWithEvidence | None = None
    total: FieldWithEvidence | None = None
    currency: FieldWithEvidence | None = None
    line_items: list[LineItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_total_math(self):
        subtotal = field_to_float(self.subtotal)
        total = field_to_float(self.total)

        if subtotal is None or total is None:
            return self

        tax = field_to_float(self.tax) or 0.0
        shipping = field_to_float(self.shipping) or 0.0
        discount = field_to_float(self.discount) or 0.0

        expected = round(subtotal + tax + shipping - discount, 2)
        if abs(expected - total) > 0.10:
            raise ValueError(
                f"Total mismatch: {subtotal}+{tax}+{shipping}-{discount}={expected}, got {total}"
            )
        return self


class ReviewOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    doc_id: str
    input_path: str
    document_type: str = "receipt"

    fields: dict[str, Any]
    line_items: list[dict[str, Any]] = Field(default_factory=list)

    parse_success: bool = True
    schema_valid: bool
    schema_errors: list[str] = Field(default_factory=list)

    rule_results: list[dict[str, Any]] = Field(default_factory=list)

    confidence_score: float
    confidence_score_0_10: float
    confidence_breakdown: dict[str, float] = Field(default_factory=dict)

    decision: DecisionLabel
    explanation: str

    extraction_metadata: dict[str, Any] = Field(default_factory=dict)


def get_field_value(field: Any) -> Any:
    if field is None:
        return None
    if isinstance(field, FieldWithEvidence):
        return field.value
    if isinstance(field, dict):
        return field.get("value")
    return field


def get_field_confidence(field: Any) -> str | None:
    if field is None:
        return None
    if isinstance(field, FieldWithEvidence):
        return field.confidence
    if isinstance(field, dict):
        return normalize_confidence_label(field.get("confidence"))
    return None


def field_to_float(field: Any) -> float | None:
    return to_float(get_field_value(field))


def to_float(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    text = text.replace(",", "")
    text = re.sub(r"(?i)\b(usd|myr|rm|eur|gbp|cad|aud)\b", "", text)
    text = text.replace("$", "")

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def normalize_field_dict(fields: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure every known field is either a FieldWithEvidence-shaped dict or absent.
    Also normalize numeric confidence values to high/medium/low before validation.
    """
    normalized = dict(fields or {})

    for name in InvoiceSchema.model_fields:
        if name == "line_items":
            continue

        value = normalized.get(name)

        if value is not None and not isinstance(value, dict):
            normalized[name] = {
                "value": value,
                "evidence": None,
                "bounding_box": None,
                "confidence": None,
            }
        elif isinstance(value, dict):
            value = dict(value)
            value["confidence"] = normalize_confidence_label(value.get("confidence"))
            normalized[name] = value

    return normalized
