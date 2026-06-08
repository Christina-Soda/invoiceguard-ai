# agent/rule_engine.py

from __future__ import annotations

from datetime import date, datetime
from difflib import SequenceMatcher
from typing import Any

from agent.schemas import get_field_confidence, get_field_value, to_float


class RuleEngine:
    """
    Teacher-aligned baseline rule engine.

    Design principles:
    1. Keep it simple and runnable.
    2. Do not require invoice_number for SROIE receipts.
    3. Route uncertainty to human review instead of forcing automatic approval.
    4. Reject clear structural/math/parse failures.
    5. Leave PostgreSQL duplicate/vendor database checks for later stages.
    """

    def __init__(
        self,
        known_vendor_names: set[str] | None = None,
        vendor_fuzzy_threshold: float = 0.85,
        vendor_review_threshold: float = 0.70,
        high_amount_threshold: float = 50000.0,
    ):
        self.known_vendor_names = {
            normalize_vendor(v) for v in known_vendor_names or set() if normalize_vendor(v)
        }
        self.vendor_fuzzy_threshold = vendor_fuzzy_threshold
        self.vendor_review_threshold = vendor_review_threshold
        self.high_amount_threshold = high_amount_threshold

    def run_all(
        self,
        fields: dict[str, Any],
        line_items: list[dict[str, Any]] | None = None,
        *,
        parse_success: bool = True,
        document_quality_issues: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        line_items = line_items or []
        document_quality_issues = document_quality_issues or []

        results = [
            self.check_parse_success(parse_success),
            self.check_required_fields(fields),
            self.check_field_confidence(fields),
            self.check_math(fields, line_items),
            self.check_dates(fields),
            self.check_vendor(fields),
            self.check_document_quality(document_quality_issues),
            self.check_duplicate(fields),
            self.check_risk_patterns(fields),
        ]

        return [r for r in results if r is not None]

    # ------------------------------------------------------------------
    # Core rules
    # ------------------------------------------------------------------

    def check_parse_success(self, parse_success: bool) -> dict[str, Any]:
        if not parse_success:
            return fail_result(
                "parse_success_check",
                "critical",
                "Model output could not be parsed as valid JSON.",
            )
        return pass_result("parse_success_check")

    def check_required_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        """
        For SROIE receipts, critical fields are vendor_name, invoice_date, total.
        invoice_number is not required because many receipts do not contain it.
        """
        critical_required = ["vendor_name", "invoice_date", "total"]
        missing: list[str] = []

        for name in critical_required:
            value = get_field_value(fields.get(name))
            if value is None or str(value).strip() == "":
                missing.append(name)

        if missing:
            severity = "critical" if "total" in missing else "high"
            return fail_result(
                "required_fields_check",
                severity,
                f"Missing critical fields: {missing}",
            )

        return pass_result("required_fields_check")

    def check_field_confidence(self, fields: dict[str, Any]) -> dict[str, Any]:
        """
        Use field-level confidence from the VLM output.
        This is intentionally conservative: low confidence on total is high risk.
        """
        critical_fields = ["vendor_name", "invoice_date", "total"]
        low_fields = []
        medium_fields = []

        for name in critical_fields:
            conf = get_field_confidence(fields.get(name))
            if conf == "low":
                low_fields.append(name)
            elif conf == "medium":
                medium_fields.append(name)

        if low_fields:
            severity = "high" if "total" in low_fields else "medium"
            return warning_result(
                "field_confidence_check",
                severity,
                f"Low confidence critical fields: {low_fields}",
            )

        if medium_fields:
            return warning_result(
                "field_confidence_check",
                "medium",
                f"Medium confidence critical fields: {medium_fields}",
            )

        return pass_result("field_confidence_check")

    def check_math(self, fields: dict[str, Any], line_items: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Only check math when enough information exists.
        Missing subtotal/line_items should not fail simple receipt extraction.
        """
        subtotal = to_float(get_field_value(fields.get("subtotal")))
        tax = to_float(get_field_value(fields.get("tax"))) or 0.0
        shipping = to_float(get_field_value(fields.get("shipping"))) or 0.0
        discount = to_float(get_field_value(fields.get("discount"))) or 0.0
        total = to_float(get_field_value(fields.get("total")))

        if total is None:
            return fail_result(
                "math_check",
                "critical",
                "Total is missing or non-numeric.",
            )

        if subtotal is not None:
            expected = round(subtotal + tax + shipping - discount, 2)
            diff = abs(expected - total)

            if diff > 0.10:
                return fail_result(
                    "math_check",
                    "critical",
                    f"Total mismatch: expected {expected}, got {total}, diff={diff:.2f}",
                )

        if line_items and subtotal is not None:
            item_sum = 0.0
            has_amount = False

            for item in line_items:
                amount = to_float(item.get("amount"))
                if amount is not None:
                    item_sum += amount
                    has_amount = True

            if has_amount:
                item_sum = round(item_sum, 2)
                if abs(item_sum - subtotal) > 0.10:
                    return warning_result(
                        "line_items_sum_check",
                        "medium",
                        f"Line items sum {item_sum} != subtotal {subtotal}",
                    )

        return pass_result("math_check")

    def check_dates(self, fields: dict[str, Any]) -> dict[str, Any]:
        invoice_date = parse_date(get_field_value(fields.get("invoice_date")))
        due_date = parse_date(get_field_value(fields.get("due_date")))
        today = date.today()

        if invoice_date and invoice_date > today:
            return fail_result(
                "date_check",
                "high",
                f"Invoice date {invoice_date} is in the future.",
            )

        if invoice_date and due_date and due_date < invoice_date:
            return warning_result(
                "date_order_check",
                "medium",
                f"Due date {due_date} is before invoice date {invoice_date}.",
            )

        return pass_result("date_check")

    def check_vendor(self, fields: dict[str, Any]) -> dict[str, Any]:
        """
        Optional known-vendor check.

        If no known vendor list is supplied, pass.
        If supplied, use fuzzy matching rather than exact matching.
        """
        vendor = get_field_value(fields.get("vendor_name"))
        if not vendor or not self.known_vendor_names:
            return pass_result("vendor_check")

        vendor_norm = normalize_vendor(vendor)
        best_score = max(
            SequenceMatcher(None, vendor_norm, known).ratio()
            for known in self.known_vendor_names
        )

        if best_score >= self.vendor_fuzzy_threshold:
            return {
                "rule": "vendor_check",
                "status": "pass",
                "severity": "none",
                "detail": f"Known vendor fuzzy score={best_score:.3f}",
            }

        if best_score >= self.vendor_review_threshold:
            return warning_result(
                "vendor_check",
                "medium",
                f"Vendor is similar to known vendor but uncertain. fuzzy score={best_score:.3f}",
            )

        return warning_result(
            "vendor_check",
            "medium",
            f"Vendor '{vendor}' is not in the optional known-vendor list. best fuzzy score={best_score:.3f}",
        )

    def check_document_quality(self, issues: list[str]) -> dict[str, Any]:
        """
        If the model or upstream OCR reports quality issues, route to review.
        v3 prompt did not reliably detect these, but the hook is useful for future OCR/image checks.
        """
        if not issues:
            return pass_result("document_quality_check")

        high_risk = {
            "unclear_amount_digits",
            "multiple_total_candidates",
            "occluded_text",
            "broken_characters",
        }

        issue_set = {str(x) for x in issues}
        severity = "high" if issue_set & high_risk else "medium"

        return warning_result(
            "document_quality_check",
            severity,
            f"Document quality issues: {sorted(issue_set)}",
        )

    def check_duplicate(self, fields: dict[str, Any]) -> dict[str, Any]:
        # Placeholder for later PostgreSQL / duplicate invoice detection.
        return pass_result("duplicate_check")

    def check_risk_patterns(self, fields: dict[str, Any]) -> dict[str, Any]:
        total = to_float(get_field_value(fields.get("total"))) or 0.0

        if total > self.high_amount_threshold:
            return warning_result(
                "high_amount_check",
                "medium",
                f"Unusually high amount: {total}",
            )

        return pass_result("risk_check")


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def pass_result(rule: str) -> dict[str, Any]:
    return {"rule": rule, "status": "pass", "severity": "none", "detail": ""}


def warning_result(rule: str, severity: str, detail: str) -> dict[str, Any]:
    return {"rule": rule, "status": "warning", "severity": severity, "detail": detail}


def fail_result(rule: str, severity: str, detail: str) -> dict[str, Any]:
    return {"rule": rule, "status": "fail", "severity": severity, "detail": detail}


def normalize_vendor(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip().upper()
    text = text.replace("SDN.", "SDN").replace("BHD.", "BHD")
    text = text.replace("S/B", "SDN BHD")
    text = text.replace("SB", "SDN BHD")
    text = " ".join(text.split())
    return text


def parse_date(value: Any) -> date | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    # Remove common time suffix.
    text = text.split("  ")[0].strip()

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
        "%d %B %Y",
        "%d-%b-%Y",
        "%d-%B-%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None
