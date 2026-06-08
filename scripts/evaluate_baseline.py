#!/usr/bin/env python3
"""
Evaluate Qwen2.5-VL receipt/invoice extraction outputs.

Teacher-aligned version:
- exact / normalized / vendor fuzzy matching
- field-level Precision / Recall / F1
- failure case report
- optional review-agent decision distribution
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_INPUT = "outputs/baseline/qwen_train_sample_100_v2.jsonl"
DEFAULT_OUTPUT_DIR = "outputs/evaluation"
DEFAULT_NAME = "qwen_train_sample_100_v2"
DEFAULT_VENDOR_FUZZY_THRESHOLD = 0.85


# ---------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------

def read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input JSONL not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Failed to parse line {line_idx} in {path}: {exc}"
                ) from exc

            if not isinstance(record, dict):
                raise ValueError(f"Line {line_idx} is not a JSON object.")

            yield record


# ---------------------------------------------------------------------
# Field access
# ---------------------------------------------------------------------

def get_gt_value(record: Dict[str, Any], field_name: str) -> Any:
    gt = record.get("ground_truth_fields", {})
    if not isinstance(gt, dict):
        return None
    return gt.get(field_name)


def get_pred_value(record: Dict[str, Any], field_name: str) -> Any:
    prediction = record.get("prediction", {})
    if not isinstance(prediction, dict):
        return None

    fields = prediction.get("fields", {})
    if not isinstance(fields, dict):
        return None

    field_obj = fields.get(field_name)
    if isinstance(field_obj, dict):
        return field_obj.get("value")
    return field_obj


def get_pred_confidence(record: Dict[str, Any], field_name: str) -> Any:
    prediction = record.get("prediction", {})
    if not isinstance(prediction, dict):
        return None

    fields = prediction.get("fields", {})
    if not isinstance(fields, dict):
        return None

    field_obj = fields.get(field_name)
    if isinstance(field_obj, dict):
        return field_obj.get("confidence")
    return None


def get_prediction_quality_issues(record: Dict[str, Any]) -> list[str]:
    prediction = record.get("prediction", {})
    if not isinstance(prediction, dict):
        return []

    issues = prediction.get("document_quality_issues", [])
    if isinstance(issues, list):
        return [str(x) for x in issues]
    return []


def has_value(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


# ---------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------

def normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    text = text.upper()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^A-Z0-9]+", "", text)
    return text or None


def normalize_vendor_for_fuzzy(value: Any) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip().upper()
    if not text:
        return None

    replacements = {
        "SDN.": "SDN",
        "BHD.": "BHD",
        "S/B": "SDN BHD",
        "SB": "SDN BHD",
        "CO.": "CO",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^A-Z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def normalize_date(value: Any) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip().upper()
    if not text:
        return None

    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", text)

    month_map = {
        "JAN": "01", "JANUARY": "01",
        "FEB": "02", "FEBRUARY": "02",
        "MAR": "03", "MARCH": "03",
        "APR": "04", "APRIL": "04",
        "MAY": "05",
        "JUN": "06", "JUNE": "06",
        "JUL": "07", "JULY": "07",
        "AUG": "08", "AUGUST": "08",
        "SEP": "09", "SEPT": "09", "SEPTEMBER": "09",
        "OCT": "10", "OCTOBER": "10",
        "NOV": "11", "NOVEMBER": "11",
        "DEC": "12", "DECEMBER": "12",
    }

    month_pattern = (
        r"\b(\d{1,2})\s+"
        r"(JANUARY|JAN|FEBRUARY|FEB|MARCH|MAR|APRIL|APR|MAY|JUNE|JUN|"
        r"JULY|JUL|AUGUST|AUG|SEPTEMBER|SEPT|SEP|OCTOBER|OCT|"
        r"NOVEMBER|NOV|DECEMBER|DEC)\s+"
        r"(\d{2,4})\b"
    )

    match = re.search(month_pattern, text)
    if match:
        day = int(match.group(1))
        month = month_map[match.group(2)]
        year = match.group(3)
        if len(year) == 2:
            year = "20" + year
        return f"{year}{month}{day:02d}"

    numeric_match = re.search(
        r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})\b",
        text,
    )
    if numeric_match:
        day = int(numeric_match.group(1))
        month = int(numeric_match.group(2))
        year = numeric_match.group(3)
        if len(year) == 2:
            year = "20" + year
        return f"{year}{month:02d}{day:02d}"

    digits = re.sub(r"[^0-9]", "", text)
    return digits or None


def normalize_amount(value: Any) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    text = re.sub(r"[^0-9.,-]", "", text)
    text = text.replace(",", "")

    if not text or text in {"-", ".", "-."}:
        return None

    try:
        amount = Decimal(text)
    except InvalidOperation:
        return None

    return f"{amount:.2f}"


# ---------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------

def exact_match(gt: Any, pred: Any) -> bool:
    if gt is None or pred is None:
        return gt is None and pred is None
    return str(gt).strip() == str(pred).strip()


def normalized_text_match(gt: Any, pred: Any) -> bool:
    return normalize_text(gt) == normalize_text(pred)


def normalized_date_match(gt: Any, pred: Any) -> bool:
    return normalize_date(gt) == normalize_date(pred)


def normalized_amount_match(gt: Any, pred: Any) -> bool:
    return normalize_amount(gt) == normalize_amount(pred)


def fuzzy_vendor_score(gt: Any, pred: Any) -> float:
    gt_norm = normalize_vendor_for_fuzzy(gt)
    pred_norm = normalize_vendor_for_fuzzy(pred)

    if gt_norm is None and pred_norm is None:
        return 1.0
    if gt_norm is None or pred_norm is None:
        return 0.0

    return round(SequenceMatcher(None, gt_norm, pred_norm).ratio(), 4)


def fuzzy_vendor_match(gt: Any, pred: Any, threshold: float) -> bool:
    return fuzzy_vendor_score(gt, pred) >= threshold


# ---------------------------------------------------------------------
# Precision / Recall / F1
# ---------------------------------------------------------------------

def safe_rate(numer: float, denom: float) -> float:
    return 0.0 if denom == 0 else numer / denom


def compute_prf_for_field(
    rows: list[dict[str, Any]],
    gt_key: str,
    pred_key: str,
    match_key: str,
) -> dict[str, Any]:
    """
    Compute precision / recall / F1 for one extracted field.

    TP: GT exists, prediction exists, and matched.
    FP: prediction exists, but it does not match GT.
    FN: GT exists, but prediction is missing or incorrect.

    A wrong prediction counts as both FP and FN.
    """
    tp = 0
    fp = 0
    fn = 0

    for r in rows:
        gt = r.get(gt_key)
        pred = r.get(pred_key)
        matched = bool(r.get(match_key))

        gt_present = has_value(gt)
        pred_present = has_value(pred)

        if gt_present and pred_present and matched:
            tp += 1
        elif gt_present and pred_present and not matched:
            fp += 1
            fn += 1
        elif gt_present and not pred_present:
            fn += 1
        elif not gt_present and pred_present:
            fp += 1

    precision = safe_rate(tp, tp + fp)
    recall = safe_rate(tp, tp + fn)
    f1 = safe_rate(2 * precision * recall, precision + recall)

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def add_prf_metrics(metrics: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    vendor_prf = compute_prf_for_field(
        rows,
        gt_key="gt_vendor_name",
        pred_key="pred_vendor_name",
        match_key="vendor_fuzzy_match",
    )

    date_prf = compute_prf_for_field(
        rows,
        gt_key="gt_invoice_date",
        pred_key="pred_invoice_date",
        match_key="date_normalized_match",
    )

    total_prf = compute_prf_for_field(
        rows,
        gt_key="gt_total",
        pred_key="pred_total",
        match_key="total_normalized_match",
    )

    metrics.update({
        "vendor_tp": vendor_prf["tp"],
        "vendor_fp": vendor_prf["fp"],
        "vendor_fn": vendor_prf["fn"],
        "vendor_precision": vendor_prf["precision"],
        "vendor_recall": vendor_prf["recall"],
        "vendor_f1": vendor_prf["f1"],

        "date_tp": date_prf["tp"],
        "date_fp": date_prf["fp"],
        "date_fn": date_prf["fn"],
        "date_precision": date_prf["precision"],
        "date_recall": date_prf["recall"],
        "date_f1": date_prf["f1"],

        "total_tp": total_prf["tp"],
        "total_fp": total_prf["fp"],
        "total_fn": total_prf["fn"],
        "total_precision": total_prf["precision"],
        "total_recall": total_prf["recall"],
        "total_f1": total_prf["f1"],

        "macro_precision": (
            vendor_prf["precision"] + date_prf["precision"] + total_prf["precision"]
        ) / 3,
        "macro_recall": (
            vendor_prf["recall"] + date_prf["recall"] + total_prf["recall"]
        ) / 3,
        "macro_f1": (
            vendor_prf["f1"] + date_prf["f1"] + total_prf["f1"]
        ) / 3,
    })


# ---------------------------------------------------------------------
# Record evaluation
# ---------------------------------------------------------------------

def evaluate_record(record: Dict[str, Any], vendor_fuzzy_threshold: float) -> Dict[str, Any]:
    doc_id = record.get("doc_id")
    image_path = record.get("image_path")
    parse_success = bool(record.get("parse_success", False))

    gt_vendor = get_gt_value(record, "vendor_name")
    pr_vendor = get_pred_value(record, "vendor_name")

    gt_date = get_gt_value(record, "invoice_date")
    pr_date = get_pred_value(record, "invoice_date")

    gt_total = get_gt_value(record, "total")
    pr_total = get_pred_value(record, "total")

    vendor_exact = exact_match(gt_vendor, pr_vendor)
    vendor_norm = normalized_text_match(gt_vendor, pr_vendor)
    vendor_fuzzy = fuzzy_vendor_match(gt_vendor, pr_vendor, vendor_fuzzy_threshold)
    vendor_score = fuzzy_vendor_score(gt_vendor, pr_vendor)

    date_exact = exact_match(gt_date, pr_date)
    date_norm = normalized_date_match(gt_date, pr_date)

    total_exact = exact_match(gt_total, pr_total)
    total_norm = normalized_amount_match(gt_total, pr_total)

    all_exact = vendor_exact and date_exact and total_exact
    all_normalized = vendor_norm and date_norm and total_norm
    all_fuzzy = vendor_fuzzy and date_norm and total_norm

    quality_issues = get_prediction_quality_issues(record)

    error_types: List[str] = []

    if not parse_success:
        error_types.append("parse_failed")

    if not vendor_norm:
        if vendor_fuzzy:
            error_types.append("vendor_fuzzy_only_match")
        else:
            error_types.append("vendor_mismatch")

    if not date_norm:
        error_types.append("date_mismatch")

    if not total_norm:
        error_types.append("total_mismatch")

    if not total_exact and total_norm:
        error_types.append("total_format_only_mismatch")

    if quality_issues:
        error_types.append("document_quality_issue")

    return {
        "doc_id": doc_id,
        "image_path": image_path,
        "parse_success": parse_success,

        "gt_vendor_name": gt_vendor,
        "pred_vendor_name": pr_vendor,
        "pred_vendor_confidence": get_pred_confidence(record, "vendor_name"),
        "vendor_exact_match": vendor_exact,
        "vendor_normalized_match": vendor_norm,
        "vendor_fuzzy_score": vendor_score,
        "vendor_fuzzy_match": vendor_fuzzy,

        "gt_invoice_date": gt_date,
        "pred_invoice_date": pr_date,
        "pred_invoice_date_confidence": get_pred_confidence(record, "invoice_date"),
        "date_exact_match": date_exact,
        "date_normalized_match": date_norm,

        "gt_total": gt_total,
        "pred_total": pr_total,
        "pred_total_confidence": get_pred_confidence(record, "total"),
        "total_exact_match": total_exact,
        "total_normalized_match": total_norm,
        "gt_total_normalized": normalize_amount(gt_total),
        "pred_total_normalized": normalize_amount(pr_total),

        "document_quality_issues": ";".join(quality_issues),
        "all_key_fields_exact_match": all_exact,
        "all_key_fields_normalized_match": all_normalized,
        "all_key_fields_fuzzy_match": all_fuzzy,

        "error_types": ";".join(error_types),
    }


def compute_metrics(rows: List[Dict[str, Any]], vendor_fuzzy_threshold: float) -> Dict[str, Any]:
    total = len(rows)
    error_counter = Counter()

    for r in rows:
        for e in str(r.get("error_types", "")).split(";"):
            if e:
                error_counter[e] += 1

    metrics = {
        "total_records": total,
        "vendor_fuzzy_threshold": vendor_fuzzy_threshold,

        "parse_success_count": sum(bool(r["parse_success"]) for r in rows),
        "parse_success_rate": safe_rate(sum(bool(r["parse_success"]) for r in rows), total),

        "vendor_exact_accuracy": safe_rate(sum(bool(r["vendor_exact_match"]) for r in rows), total),
        "vendor_normalized_accuracy": safe_rate(sum(bool(r["vendor_normalized_match"]) for r in rows), total),
        "vendor_fuzzy_accuracy": safe_rate(sum(bool(r["vendor_fuzzy_match"]) for r in rows), total),
        "vendor_fuzzy_only_match_count": sum(
            "vendor_fuzzy_only_match" in str(r["error_types"]) for r in rows
        ),

        "date_exact_accuracy": safe_rate(sum(bool(r["date_exact_match"]) for r in rows), total),
        "date_normalized_accuracy": safe_rate(sum(bool(r["date_normalized_match"]) for r in rows), total),

        "total_exact_accuracy": safe_rate(sum(bool(r["total_exact_match"]) for r in rows), total),
        "total_normalized_accuracy": safe_rate(sum(bool(r["total_normalized_match"]) for r in rows), total),

        "all_key_fields_exact_accuracy": safe_rate(
            sum(bool(r["all_key_fields_exact_match"]) for r in rows), total
        ),
        "all_key_fields_normalized_accuracy": safe_rate(
            sum(bool(r["all_key_fields_normalized_match"]) for r in rows), total
        ),
        "all_key_fields_fuzzy_accuracy": safe_rate(
            sum(bool(r["all_key_fields_fuzzy_match"]) for r in rows), total
        ),

        "total_format_only_mismatch_count": sum(
            "total_format_only_mismatch" in str(r["error_types"]) for r in rows
        ),

        "error_type_counts": dict(error_counter),
    }

    add_prf_metrics(metrics, rows)
    return metrics


# ---------------------------------------------------------------------
# Optional decision evaluation
# ---------------------------------------------------------------------

def load_decisions(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}

    decisions: dict[str, str] = {}
    for r in read_jsonl(path):
        doc_id = r.get("doc_id")
        decision = r.get("decision")
        if doc_id and decision:
            decisions[str(doc_id)] = str(decision)
    return decisions


def attach_decisions(rows: list[dict[str, Any]], decisions: dict[str, str]) -> None:
    for r in rows:
        doc_id = str(r.get("doc_id"))
        r["decision"] = decisions.get(doc_id)


def compute_decision_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counter = Counter(r.get("decision") for r in rows if r.get("decision"))

    return {
        "decision_counts": dict(decision_counter),
        "approve_count": decision_counter.get("approve", 0),
        "need_human_review_count": decision_counter.get("need_human_review", 0),
        "reject_count": decision_counter.get("reject", 0),
    }


# ---------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------

def write_metrics(path: Path, metrics: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_failure_cases(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    failures = []
    for r in rows:
        has_failure = (
            not r["parse_success"]
            or not r["vendor_fuzzy_match"]
            or not r["date_normalized_match"]
            or not r["total_normalized_match"]
            or "total_format_only_mismatch" in str(r["error_types"])
            or "document_quality_issue" in str(r["error_types"])
        )
        if has_failure:
            failures.append(r)

    with path.open("w", encoding="utf-8") as f:
        f.write("# Failure / Review Cases\n\n")
        f.write(f"Total failure / review cases: {len(failures)}\n\n")

        if not failures:
            f.write("No failures found.\n")
            return

        for idx, r in enumerate(failures, start=1):
            f.write(f"## Case {idx}: {r['doc_id']}\n\n")
            f.write(f"- Image: `{r['image_path']}`\n")
            f.write(f"- Error types: `{r['error_types']}`\n")
            if r.get("decision"):
                f.write(f"- Agent decision: `{r['decision']}`\n")
            if r.get("document_quality_issues"):
                f.write(f"- Document quality issues: `{r['document_quality_issues']}`\n")
            f.write(f"- Parse success: `{r['parse_success']}`\n\n")

            f.write("| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |\n")
            f.write("|---|---|---|---:|---:|---:|\n")
            f.write(
                f"| vendor_name | {r['gt_vendor_name']} | {r['pred_vendor_name']} | "
                f"{r['vendor_exact_match']} | {r['vendor_normalized_match']} | "
                f"score={r['vendor_fuzzy_score']}, match={r['vendor_fuzzy_match']} |\n"
            )
            f.write(
                f"| invoice_date | {r['gt_invoice_date']} | {r['pred_invoice_date']} | "
                f"{r['date_exact_match']} | {r['date_normalized_match']} | - |\n"
            )
            f.write(
                f"| total | {r['gt_total']} | {r['pred_total']} | "
                f"{r['total_exact_match']} | {r['total_normalized_match']} | "
                f"GT norm={r['gt_total_normalized']}, Pred norm={r['pred_total_normalized']} |\n"
            )

            if "total_format_only_mismatch" in str(r["error_types"]):
                f.write(
                    "\nNote: total is numerically correct after normalization, "
                    "but raw prediction has formatting/currency differences.\n"
                )

            if "vendor_fuzzy_only_match" in str(r["error_types"]):
                f.write(
                    "\nNote: vendor failed strict normalization but passed fuzzy matching. "
                    "This is likely a naming/OCR variation rather than a complete miss.\n"
                )

            f.write("\n")


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def print_metrics(metrics: Dict[str, Any]) -> None:
    print("=== Evaluation Metrics ===")
    print(f"Total records:                      {metrics['total_records']}")
    print(f"Parse success count:                {metrics['parse_success_count']}")
    print(f"Parse success rate:                 {metrics['parse_success_rate']:.3f}")
    print(f"Vendor exact accuracy:              {metrics['vendor_exact_accuracy']:.3f}")
    print(f"Vendor normalized accuracy:         {metrics['vendor_normalized_accuracy']:.3f}")
    print(f"Vendor fuzzy accuracy:              {metrics['vendor_fuzzy_accuracy']:.3f}")
    print(f"Date exact accuracy:                {metrics['date_exact_accuracy']:.3f}")
    print(f"Date normalized accuracy:           {metrics['date_normalized_accuracy']:.3f}")
    print(f"Total exact accuracy:               {metrics['total_exact_accuracy']:.3f}")
    print(f"Total normalized accuracy:          {metrics['total_normalized_accuracy']:.3f}")
    print(f"All key fields exact accuracy:      {metrics['all_key_fields_exact_accuracy']:.3f}")
    print(f"All key fields normalized accuracy: {metrics['all_key_fields_normalized_accuracy']:.3f}")
    print(f"All key fields fuzzy accuracy:      {metrics['all_key_fields_fuzzy_accuracy']:.3f}")
    print(f"Total format-only mismatch count:   {metrics['total_format_only_mismatch_count']}")

    print()
    print("=== Precision / Recall / F1 ===")
    print(
        f"Vendor P/R/F1: {metrics['vendor_precision']:.3f} / "
        f"{metrics['vendor_recall']:.3f} / {metrics['vendor_f1']:.3f} "
        f"(TP={metrics['vendor_tp']}, FP={metrics['vendor_fp']}, FN={metrics['vendor_fn']})"
    )
    print(
        f"Date P/R/F1:   {metrics['date_precision']:.3f} / "
        f"{metrics['date_recall']:.3f} / {metrics['date_f1']:.3f} "
        f"(TP={metrics['date_tp']}, FP={metrics['date_fp']}, FN={metrics['date_fn']})"
    )
    print(
        f"Total P/R/F1:  {metrics['total_precision']:.3f} / "
        f"{metrics['total_recall']:.3f} / {metrics['total_f1']:.3f} "
        f"(TP={metrics['total_tp']}, FP={metrics['total_fp']}, FN={metrics['total_fn']})"
    )
    print(
        f"Macro P/R/F1:  {metrics['macro_precision']:.3f} / "
        f"{metrics['macro_recall']:.3f} / {metrics['macro_f1']:.3f}"
    )

    if metrics.get("decision_counts"):
        print()
        print("=== Agent Decision Distribution ===")
        print(metrics["decision_counts"])

    print()
    print("=== Error Type Counts ===")
    if metrics.get("error_type_counts"):
        for key, value in metrics.get("error_type_counts", {}).items():
            print(f"{key}: {value}")
    else:
        print("No error types found.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Qwen baseline extraction outputs."
    )
    parser.add_argument("--input", type=str, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--name", type=str, default=DEFAULT_NAME)
    parser.add_argument(
        "--vendor-fuzzy-threshold",
        type=float,
        default=DEFAULT_VENDOR_FUZZY_THRESHOLD,
        help="Vendor fuzzy threshold in [0, 1]. Default: 0.85",
    )
    parser.add_argument(
        "--review-jsonl",
        type=str,
        default=None,
        help="Optional JSONL generated by agent/review_agent.py to attach decisions.",
    )
    args = parser.parse_args()

    if not 0.0 <= args.vendor_fuzzy_threshold <= 1.0:
        raise ValueError("--vendor-fuzzy-threshold must be in [0, 1].")

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    rows = [
        evaluate_record(record, args.vendor_fuzzy_threshold)
        for record in read_jsonl(input_path)
    ]

    decisions = load_decisions(Path(args.review_jsonl) if args.review_jsonl else None)
    if decisions:
        attach_decisions(rows, decisions)

    metrics = compute_metrics(rows, args.vendor_fuzzy_threshold)
    metrics.update(compute_decision_metrics(rows))

    metrics_path = output_dir / f"{args.name}_metrics.json"
    csv_path = output_dir / f"{args.name}_field_results.csv"
    failure_path = output_dir / f"{args.name}_failure_cases.md"

    write_metrics(metrics_path, metrics)
    write_csv(csv_path, rows)
    write_failure_cases(failure_path, rows)

    print_metrics(metrics)

    print()
    print("=== Evaluation Outputs ===")
    print(f"Metrics:       {metrics_path}")
    print(f"Field results: {csv_path}")
    print(f"Failures:      {failure_path}")


if __name__ == "__main__":
    main()
