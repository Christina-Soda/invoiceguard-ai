# agent/decision.py

from __future__ import annotations

from typing import Any


APPROVE = "approve"
NEED_HUMAN_REVIEW = "need_human_review"
REJECT = "reject"


def make_decision(
    confidence_score_0_10: float,
    rule_results: list[dict[str, Any]],
    *,
    parse_success: bool = True,
    approve_threshold: float = 8.0,
    reject_threshold: float = 2.0,
) -> tuple[str, str]:
    """
    Convert confidence + rule results into final decision.

    Teacher-aligned simple scale:
        0-2   -> reject
        3-7   -> need_human_review
        8-10  -> approve

    Safety overrides:
        - parse failure -> reject
        - critical rule failure -> reject
        - high failure/warning -> need_human_review
        - any warning -> need_human_review
    """
    if not parse_success:
        return REJECT, "Reject because the model output could not be parsed as valid JSON."

    critical_fails = [
        r for r in rule_results
        if r.get("status") == "fail" and r.get("severity") == "critical"
    ]
    high_fails = [
        r for r in rule_results
        if r.get("status") == "fail" and r.get("severity") == "high"
    ]
    high_warnings = [
        r for r in rule_results
        if r.get("status") == "warning" and r.get("severity") == "high"
    ]
    warnings = [
        r for r in rule_results
        if r.get("status") == "warning"
    ]

    if critical_fails:
        return (
            REJECT,
            f"Reject because of critical rule failures: {[r.get('rule') for r in critical_fails]}",
        )

    if confidence_score_0_10 <= reject_threshold:
        return (
            REJECT,
            f"Reject because confidence score {confidence_score_0_10:.1f}/10 is at or below {reject_threshold:.1f}.",
        )

    if high_fails:
        return (
            NEED_HUMAN_REVIEW,
            f"Needs human review because of high-severity rule failures: {[r.get('rule') for r in high_fails]}",
        )

    if high_warnings:
        return (
            NEED_HUMAN_REVIEW,
            f"Needs human review because of high-severity warnings: {[r.get('rule') for r in high_warnings]}",
        )

    if confidence_score_0_10 < approve_threshold:
        return (
            NEED_HUMAN_REVIEW,
            f"Needs human review because confidence score {confidence_score_0_10:.1f}/10 is below {approve_threshold:.1f}.",
        )

    if warnings:
        return (
            NEED_HUMAN_REVIEW,
            f"Needs human review because warnings are present: {[r.get('rule') for r in warnings]}",
        )

    return APPROVE, f"Approve. All checks passed with confidence {confidence_score_0_10:.1f}/10."
