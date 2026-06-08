# agent/review_agent.py

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

# Allow both:
#   python -m agent.review_agent ...
# and:
#   python agent/review_agent.py ...
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agent.confidence import compute_confidence_v1
from agent.decision import make_decision
from agent.rule_engine import RuleEngine
from agent.schemas import InvoiceSchema, ReviewOutput, normalize_field_dict


def review_prediction_record(
    record: dict[str, Any],
    *,
    known_vendor_names: set[str] | None = None,
) -> dict[str, Any]:
    """
    Review one record from scripts/run_qwen_baseline.py output.

    Simple Python pipeline:
        prediction JSON
          -> schema validation
          -> rule engine
          -> confidence score
          -> approve / need_human_review / reject
    """
    prediction = record.get("prediction", {})
    if not isinstance(prediction, dict):
        prediction = {}

    fields = prediction.get("fields", {})
    if not isinstance(fields, dict):
        fields = {}

    fields = normalize_field_dict(fields)

    line_items = prediction.get("line_items", [])
    if not isinstance(line_items, list):
        line_items = []

    parse_success = bool(record.get("parse_success", prediction.get("_parse_success", False)))

    document_quality_issues = prediction.get("document_quality_issues", [])
    if not isinstance(document_quality_issues, list):
        document_quality_issues = []

    schema_valid = True
    schema_errors: list[str] = []

    try:
        invoice_obj = InvoiceSchema(**fields, line_items=line_items)
        fields = invoice_obj.model_dump(exclude={"line_items"})
        line_items = [item.model_dump() for item in invoice_obj.line_items]
    except ValidationError as exc:
        schema_valid = False
        schema_errors = [str(e) for e in exc.errors()]
        # Keep original normalized fields so rule/confidence can still run.

    engine = RuleEngine(known_vendor_names=known_vendor_names)
    rule_results = engine.run_all(
        fields=fields,
        line_items=line_items,
        parse_success=parse_success,
        document_quality_issues=[str(x) for x in document_quality_issues],
    )

    vlm_confidence = prediction.get("overall_confidence")
    confidence_score, confidence_score_0_10, breakdown = compute_confidence_v1(
        vlm_confidence=vlm_confidence,
        schema_valid=schema_valid,
        rule_results=rule_results,
        fields=fields,
        parse_success=parse_success,
    )

    decision, explanation = make_decision(
        confidence_score_0_10=confidence_score_0_10,
        rule_results=rule_results,
        parse_success=parse_success,
    )

    output = ReviewOutput(
        doc_id=str(record.get("doc_id", "")),
        input_path=str(record.get("image_path") or record.get("json_path") or ""),
        document_type=str(record.get("document_type", "receipt")),
        fields=fields,
        line_items=line_items,
        parse_success=parse_success,
        schema_valid=schema_valid,
        schema_errors=schema_errors,
        rule_results=rule_results,
        confidence_score=confidence_score,
        confidence_score_0_10=confidence_score_0_10,
        confidence_breakdown=breakdown,
        decision=decision,
        explanation=explanation,
        extraction_metadata={
            "source": record.get("source"),
            "split": record.get("split"),
            "json_path": record.get("json_path"),
            "baseline_error": record.get("error"),
            "document_quality_issues": document_quality_issues,
            "raw_model_parse_error": prediction.get("_parse_error"),
        },
    )

    return output.model_dump()


def read_jsonl(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Input JSONL not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL line {line_idx}: {exc}") from exc


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_known_vendors(path: Path | None) -> set[str] | None:
    if path is None:
        return None

    if not path.exists():
        raise FileNotFoundError(f"Known vendor file not found: {path}")

    vendors = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            value = line.strip()
            if value:
                vendors.add(value)

    return vendors


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        decision = row.get("decision", "unknown")
        counts[decision] = counts.get(decision, 0) + 1

    return {
        "total": len(rows),
        "decision_counts": counts,
        "avg_confidence_0_10": (
            round(sum(float(r.get("confidence_score_0_10", 0.0)) for r in rows) / len(rows), 3)
            if rows else 0.0
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run simple rule/confidence/decision review agent on baseline JSONL."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Baseline JSONL from scripts/run_qwen_baseline.py.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output reviewed JSONL.",
    )
    parser.add_argument(
        "--known-vendors",
        type=str,
        default=None,
        help="Optional text file with one approved vendor name per line.",
    )
    args = parser.parse_args()

    known_vendors = load_known_vendors(Path(args.known_vendors) if args.known_vendors else None)

    rows = [
        review_prediction_record(record, known_vendor_names=known_vendors)
        for record in read_jsonl(Path(args.input))
    ]

    write_jsonl(Path(args.output), rows)

    summary = summarize(rows)

    print("=== Review Agent Summary ===")
    print(f"Total records:          {summary['total']}")
    print(f"Decision counts:        {summary['decision_counts']}")
    print(f"Avg confidence 0-10:    {summary['avg_confidence_0_10']}")
    print(f"Output:                 {args.output}")


if __name__ == "__main__":
    main()
