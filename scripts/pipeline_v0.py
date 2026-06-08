#!/usr/bin/env python3
"""
Day 3-5 InvoiceGuard baseline pipeline.

Supports two input types:
1. raw document file: .pdf/.jpg/.png/...
2. unified JSON file: reads `image_path`, `doc_id`, `document_type`, and optional ground truth fields

Examples:
  python pipeline_v0.py --input data/unified/synthetic/synthetic_000001.json --output results/one.json
  python pipeline_v0.py --input data/unified/synthetic/synthetic_000001.json --use-ground-truth-as-extraction
  python pipeline_v0.py --manifest data/splits/test_manifest.json --limit 5 --output-dir results/baseline_smoke
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from agent.confidence import compute_confidence_v1, make_decision
from agent.rule_engine import RuleEngine
from agent.schemas import InvoiceSchema, ReviewOutput, normalize_field_dict
from models.preprocessor import load_document, preprocess_image, save_page_image
from models.qwen_vl_extractor import extract_fields


rule_engine = RuleEngine()


def load_input(input_path: str | Path) -> tuple[Path, dict[str, Any] | None]:
    """
    Return (document_path, unified_record_or_none).
    If input is unified JSON, document_path is data["image_path"].
    """
    path = Path(input_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")

    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as f:
            record = json.load(f)
        image_path = Path(record.get("image_path", "")).expanduser()
        if not image_path.exists():
            # Try relative to the JSON directory for portable copied datasets.
            candidate = path.parent / str(record.get("image_path", ""))
            if candidate.exists():
                image_path = candidate
            else:
                raise FileNotFoundError(
                    f"Unified JSON image_path does not exist: {record.get('image_path')}"
                )
        return image_path, record

    return path, None


def ground_truth_as_extraction(record: dict[str, Any]) -> dict[str, Any]:
    """
    Debug/smoke-test mode: use unified JSON fields as if VLM extracted them.
    This lets you test schema/rules/confidence without loading the 7B model.
    """
    return {
        "fields": record.get("fields", {}),
        "line_items": record.get("line_items", []),
        "overall_confidence": 0.95,
        "missing_fields": [],
        "document_quality_issues": [],
        "debug_mode": "ground_truth_as_extraction",
    }


def validate_schema(fields: dict[str, Any], line_items: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    try:
        InvoiceSchema(**normalize_field_dict({**fields, "line_items": line_items}))
        return True, []
    except Exception as exc:
        return False, [str(exc)]


def process_document_v0(
    input_path: str | Path,
    output_image_dir: str | Path = "/tmp/invoiceguard/preprocessed",
    use_ground_truth_as_extraction: bool = False,
) -> dict[str, Any]:
    start = time.time()
    document_path, record = load_input(input_path)

    doc_id = record.get("doc_id") if record else str(uuid.uuid4())
    document_type = record.get("document_type", "invoice") if record else "invoice"

    pages = load_document(document_path)
    if not pages:
        raise ValueError(f"No pages loaded from {document_path}")

    preprocessed = preprocess_image(pages[0])
    output_image_dir = Path(output_image_dir)
    output_image_dir.mkdir(parents=True, exist_ok=True)

    tmp_path = output_image_dir / f"{doc_id}_page0.jpg"
    save_page_image(preprocessed, tmp_path)

    if use_ground_truth_as_extraction:
        if record is None:
            raise ValueError("--use-ground-truth-as-extraction requires a unified JSON input")
        extraction = ground_truth_as_extraction(record)
    else:
        extraction = extract_fields(tmp_path)

    fields = normalize_field_dict(extraction.get("fields", {}))
    line_items = extraction.get("line_items", []) or []

    schema_valid, schema_errors = validate_schema(fields, line_items)
    rule_results = rule_engine.run_all(fields, line_items)

    confidence, breakdown = compute_confidence_v1(
        vlm_confidence=extraction.get("overall_confidence", 0.5),
        schema_valid=schema_valid,
        rule_results=rule_results,
        fields=fields,
    )
    decision, explanation = make_decision(confidence, rule_results)

    result = {
        "doc_id": str(doc_id),
        "input_path": str(input_path),
        "document_path": str(document_path),
        "preprocessed_image_path": str(tmp_path),
        "document_type": document_type,
        "fields": fields,
        "line_items": line_items,
        "schema_valid": schema_valid,
        "schema_errors": schema_errors,
        "rule_results": rule_results,
        "confidence_score": confidence,
        "confidence_breakdown": breakdown,
        "decision": decision,
        "explanation": explanation,
        "extraction_metadata": {
            "overall_confidence": extraction.get("overall_confidence", 0.5),
            "missing_fields": extraction.get("missing_fields", []),
            "document_quality_issues": extraction.get("document_quality_issues", []),
            "elapsed_seconds": round(time.time() - start, 3),
            "used_ground_truth_as_extraction": use_ground_truth_as_extraction,
        },
    }

    # Validate output shape before returning.
    ReviewOutput(**result)
    return result


def process_manifest(
    manifest_path: str | Path,
    output_dir: str | Path,
    limit: int | None = None,
    use_ground_truth_as_extraction: bool = False,
) -> list[dict[str, Any]]:
    manifest_path = Path(manifest_path).expanduser()
    output_dir = Path(output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    with manifest_path.open("r", encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise ValueError(f"Manifest must be a list: {manifest_path}")

    if limit is not None:
        items = items[:limit]

    results: list[dict[str, Any]] = []
    for idx, item in enumerate(items, start=1):
        print(f"[{idx}/{len(items)}] Processing {item}")
        try:
            result = process_document_v0(
                item,
                output_image_dir=output_dir / "preprocessed",
                use_ground_truth_as_extraction=use_ground_truth_as_extraction,
            )
            out_path = output_dir / f"{result['doc_id']}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            results.append(result)
        except Exception as exc:
            error = {"input_path": str(item), "status": "error", "error": str(exc)}
            out_path = output_dir / f"error_{idx:04d}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(error, f, indent=2, ensure_ascii=False)
            print(f"[ERROR] {item}: {exc}")

    summary = summarize_results(results)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return results


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    if total == 0:
        return {"total": 0}

    decisions: dict[str, int] = {"approve": 0, "reject": 0, "needs_human_review": 0}
    for r in results:
        decisions[r.get("decision", "unknown")] = decisions.get(r.get("decision", "unknown"), 0) + 1

    return {
        "total": total,
        "decisions": decisions,
        "avg_confidence": round(sum(float(r.get("confidence_score", 0)) for r in results) / total, 3),
        "schema_valid_rate": round(sum(1 for r in results if r.get("schema_valid")) / total, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Day 3-5 InvoiceGuard baseline pipeline.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=str, help="Raw document path or unified JSON path")
    group.add_argument("--manifest", type=str, help="Manifest JSON containing unified JSON paths")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path for --input mode")
    parser.add_argument("--output-dir", type=str, default="results/baseline_v0", help="Output dir for --manifest mode")
    parser.add_argument("--limit", type=int, default=None, help="Limit manifest samples")
    parser.add_argument(
        "--use-ground-truth-as-extraction",
        action="store_true",
        help="Smoke-test mode: use unified JSON fields instead of loading Qwen2.5-VL",
    )

    args = parser.parse_args()

    if args.input:
        result = process_document_v0(
            args.input,
            use_ground_truth_as_extraction=args.use_ground_truth_as_extraction,
        )
        text = json.dumps(result, indent=2, ensure_ascii=False)
        print(text)
        if args.output:
            out_path = Path(args.output).expanduser()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
    else:
        process_manifest(
            args.manifest,
            output_dir=args.output_dir,
            limit=args.limit,
            use_ground_truth_as_extraction=args.use_ground_truth_as_extraction,
        )


if __name__ == "__main__":
    main()
