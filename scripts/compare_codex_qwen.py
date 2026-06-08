#!/usr/bin/env python3
"""
Compare latest ChatGPT/Codex receipt predictions with Qwen2.5-VL baseline results.

This version is tailored for the latest ChatGPT JSONL file format:

{
  "doc_id": "sroie_train_X51008114266",
  "original_doc_id": "X51008114266",
  "prediction": {
    "fields": {
      "vendor_name": {"value": "...", "evidence": "...", "bounding_box": null, "confidence": 0.9},
      "vendor_address": {"value": "...", "evidence": "...", "bounding_box": null, "confidence": 0.9},
      "invoice_date": {"value": "...", "evidence": "...", "bounding_box": null, "confidence": 0.9},
      "total": {"value": "...", "evidence": "...", "bounding_box": null, "confidence": 0.9},
      "currency": {"value": "...", "evidence": "...", "bounding_box": null, "confidence": 0.9}
    },
    "line_items": [],
    "overall_confidence": 0.9,
    "missing_fields": [],
    "document_quality_issues": []
  },
  "parse_success": true
}

Main comparison fields:
    - vendor_name
    - invoice_date
    - total

Qwen input should be the original baseline JSONL, for example:
    outputs/baseline/qwen_train_sample_100_v2.jsonl

The script automatically selects only Qwen records whose doc_id appears in
the ChatGPT/Codex JSONL file.
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
from typing import Any


DEFAULT_VENDOR_FUZZY_THRESHOLD = 0.85
COMPARE_FIELDS = ["vendor_name", "invoice_date", "total"]


# ---------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSONL at line {line_idx} in {path}: {exc}"
                ) from exc

            if not isinstance(obj, dict):
                raise ValueError(f"Line {line_idx} in {path} is not a JSON object.")

            rows.append(obj)

    return rows


# ---------------------------------------------------------------------
# Field access
# ---------------------------------------------------------------------

def get_doc_id(record: dict[str, Any]) -> str:
    return str(record.get("doc_id", ""))


def get_original_doc_id(record: dict[str, Any]) -> str | None:
    value = record.get("original_doc_id")
    if value:
        return str(value)

    doc_id = get_doc_id(record)
    if doc_id.startswith("sroie_train_"):
        return doc_id.replace("sroie_train_", "", 1)
    if doc_id.startswith("sroie_test_"):
        return doc_id.replace("sroie_test_", "", 1)
    return doc_id or None


def get_gt_value(qwen_record: dict[str, Any], field: str) -> Any:
    gt = qwen_record.get("ground_truth_fields", {})
    if isinstance(gt, dict):
        return gt.get(field)
    return None


def get_prediction_value(record: dict[str, Any], field: str) -> Any:
    """
    Supports:
    1. Nested Qwen/ChatGPT format:
       record["prediction"]["fields"][field]["value"]

    2. Flat fallback:
       record[field]
    """
    prediction = record.get("prediction")

    if isinstance(prediction, dict):
        fields = prediction.get("fields", {})
        if isinstance(fields, dict):
            field_obj = fields.get(field)
            if isinstance(field_obj, dict):
                return field_obj.get("value")
            return field_obj

    return record.get(field)


def get_prediction_confidence(record: dict[str, Any], field: str) -> Any:
    prediction = record.get("prediction")

    if isinstance(prediction, dict):
        fields = prediction.get("fields", {})
        if isinstance(fields, dict):
            field_obj = fields.get(field)
            if isinstance(field_obj, dict):
                return field_obj.get("confidence")

    return record.get(f"{field}_confidence")


def get_parse_success(record: dict[str, Any]) -> bool:
    if "parse_success" in record:
        return bool(record.get("parse_success"))

    prediction = record.get("prediction")
    if isinstance(prediction, dict) and "_parse_success" in prediction:
        return bool(prediction.get("_parse_success"))

    return True


def get_quality_issues(record: dict[str, Any]) -> list[str]:
    prediction = record.get("prediction")
    if not isinstance(prediction, dict):
        return []

    issues = prediction.get("document_quality_issues", [])
    if isinstance(issues, list):
        return [str(x) for x in issues]
    return []


# ---------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------

def normalize_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip().upper()
    if not text:
        return None

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^A-Z0-9]+", "", text)
    return text or None


def normalize_vendor_for_fuzzy(value: Any) -> str | None:
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
        "&": " AND ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Normalize common punctuation and spacing.
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text or None


def normalize_date(value: Any) -> str | None:
    """
    Normalize date strings to YYYYMMDD when possible.

    SROIE receipts are usually DD/MM/YY, DD-MM-YY, or DD-MM-YYYY.

    Examples:
        21-05-17      -> 20170521
        19/05/18      -> 20180519
        04-06-2018    -> 20180604
        10 MAY 2018   -> 20180510
    """
    if value is None:
        return None

    text = str(value).strip().upper()
    if not text:
        return None

    # Remove time strings.
    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", text)

    month_map = {
        "JAN": 1, "JANUARY": 1,
        "FEB": 2, "FEBRUARY": 2,
        "MAR": 3, "MARCH": 3,
        "APR": 4, "APRIL": 4,
        "MAY": 5,
        "JUN": 6, "JUNE": 6,
        "JUL": 7, "JULY": 7,
        "AUG": 8, "AUGUST": 8,
        "SEP": 9, "SEPT": 9, "SEPTEMBER": 9,
        "OCT": 10, "OCTOBER": 10,
        "NOV": 11, "NOVEMBER": 11,
        "DEC": 12, "DECEMBER": 12,
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
        year = parse_year(match.group(3))
        return f"{year:04d}{month:02d}{day:02d}"

    numeric_match = re.search(
        r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})\b",
        text,
    )
    if numeric_match:
        # Malaysia/SROIE receipt style: day first.
        day = int(numeric_match.group(1))
        month = int(numeric_match.group(2))
        year = parse_year(numeric_match.group(3))
        return f"{year:04d}{month:02d}{day:02d}"

    digits = re.sub(r"[^0-9]", "", text)
    return digits or None


def parse_year(year_text: str) -> int:
    year = int(year_text)
    if len(year_text) == 2:
        return 2000 + year
    return year


def normalize_amount(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    text = re.sub(r"(?i)\b(rm|myr|usd|sgd|eur|gbp)\b", "", text)
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

def vendor_fuzzy_score(gt: Any, pred: Any) -> float:
    gt_norm = normalize_vendor_for_fuzzy(gt)
    pred_norm = normalize_vendor_for_fuzzy(pred)

    if gt_norm is None and pred_norm is None:
        return 1.0

    if gt_norm is None or pred_norm is None:
        return 0.0

    return round(SequenceMatcher(None, gt_norm, pred_norm).ratio(), 4)


def match_field(
    field: str,
    gt: Any,
    pred: Any,
    vendor_fuzzy_threshold: float,
) -> tuple[bool, str, float | None, str | None, str | None]:
    """
    Return:
        matched
        match_type
        score
        normalized_gt
        normalized_pred
    """
    if field == "vendor_name":
        score = vendor_fuzzy_score(gt, pred)
        return (
            score >= vendor_fuzzy_threshold,
            "vendor_fuzzy",
            score,
            normalize_vendor_for_fuzzy(gt),
            normalize_vendor_for_fuzzy(pred),
        )

    if field == "invoice_date":
        gt_norm = normalize_date(gt)
        pred_norm = normalize_date(pred)
        return gt_norm == pred_norm, "date_normalized", None, gt_norm, pred_norm

    if field == "total":
        gt_norm = normalize_amount(gt)
        pred_norm = normalize_amount(pred)
        return gt_norm == pred_norm, "amount_normalized", None, gt_norm, pred_norm

    gt_norm = normalize_text(gt)
    pred_norm = normalize_text(pred)
    return gt_norm == pred_norm, "text_normalized", None, gt_norm, pred_norm


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------

def has_value(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def safe_rate(numer: float, denom: float) -> float:
    return 0.0 if denom == 0 else numer / denom


def update_prf_counts(counter: dict[str, int], gt: Any, pred: Any, matched: bool) -> None:
    """
    Fixed-field extraction PRF:
        TP: GT exists, prediction exists, and matched.
        FP: prediction exists, but does not match GT.
        FN: GT exists, but prediction is missing or incorrect.

    If GT and prediction both exist but mismatch, it counts as both FP and FN.
    """
    gt_present = has_value(gt)
    pred_present = has_value(pred)

    if gt_present and pred_present and matched:
        counter["tp"] += 1
    elif gt_present and pred_present and not matched:
        counter["fp"] += 1
        counter["fn"] += 1
    elif gt_present and not pred_present:
        counter["fn"] += 1
    elif not gt_present and pred_present:
        counter["fp"] += 1


def prf_from_counts(counter: dict[str, int]) -> dict[str, float | int]:
    tp = counter["tp"]
    fp = counter["fp"]
    fn = counter["fn"]

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


# ---------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------

def select_qwen_rows_for_chatgpt_doc_ids(
    qwen_rows: list[dict[str, Any]],
    chatgpt_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    chatgpt_doc_ids = {get_doc_id(r) for r in chatgpt_rows}
    selected = [r for r in qwen_rows if get_doc_id(r) in chatgpt_doc_ids]
    selected_ids = {get_doc_id(r) for r in selected}
    missing = sorted(chatgpt_doc_ids - selected_ids)
    return selected, missing


def compare_records(
    qwen_rows: list[dict[str, Any]],
    chatgpt_rows: list[dict[str, Any]],
    vendor_fuzzy_threshold: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    chatgpt_by_id = {get_doc_id(r): r for r in chatgpt_rows}

    comparison_rows: list[dict[str, Any]] = []

    qwen_prf = {field: {"tp": 0, "fp": 0, "fn": 0} for field in COMPARE_FIELDS}
    chatgpt_prf = {field: {"tp": 0, "fp": 0, "fn": 0} for field in COMPARE_FIELDS}

    outcome_counter = Counter()
    parse_counter = Counter()

    for qwen in qwen_rows:
        doc_id = get_doc_id(qwen)
        chatgpt = chatgpt_by_id.get(doc_id)

        if chatgpt is None:
            continue

        qwen_parse = get_parse_success(qwen)
        chatgpt_parse = get_parse_success(chatgpt)
        parse_counter[f"qwen_parse_{qwen_parse}"] += 1
        parse_counter[f"chatgpt_parse_{chatgpt_parse}"] += 1

        row: dict[str, Any] = {
            "doc_id": doc_id,
            "original_doc_id": get_original_doc_id(qwen) or get_original_doc_id(chatgpt),
            "image_path": qwen.get("image_path"),
            "qwen_parse_success": qwen_parse,
            "chatgpt_parse_success": chatgpt_parse,
            "qwen_quality_issues": ";".join(get_quality_issues(qwen)),
            "chatgpt_quality_issues": ";".join(get_quality_issues(chatgpt)),
        }

        qwen_correct_count = 0
        chatgpt_correct_count = 0

        for field in COMPARE_FIELDS:
            gt_value = get_gt_value(qwen, field)
            qwen_value = get_prediction_value(qwen, field)
            chatgpt_value = get_prediction_value(chatgpt, field)

            qwen_match, qwen_match_type, qwen_score, qwen_gt_norm, qwen_pred_norm = match_field(
                field, gt_value, qwen_value, vendor_fuzzy_threshold
            )
            chatgpt_match, chatgpt_match_type, chatgpt_score, chatgpt_gt_norm, chatgpt_pred_norm = match_field(
                field, gt_value, chatgpt_value, vendor_fuzzy_threshold
            )

            update_prf_counts(qwen_prf[field], gt_value, qwen_value, qwen_match)
            update_prf_counts(chatgpt_prf[field], gt_value, chatgpt_value, chatgpt_match)

            qwen_correct_count += int(qwen_match)
            chatgpt_correct_count += int(chatgpt_match)

            row[f"gt_{field}"] = gt_value
            row[f"qwen_{field}"] = qwen_value
            row[f"chatgpt_{field}"] = chatgpt_value

            row[f"qwen_{field}_confidence"] = get_prediction_confidence(qwen, field)
            row[f"chatgpt_{field}_confidence"] = get_prediction_confidence(chatgpt, field)

            row[f"qwen_{field}_match"] = qwen_match
            row[f"chatgpt_{field}_match"] = chatgpt_match

            row[f"qwen_{field}_match_type"] = qwen_match_type
            row[f"chatgpt_{field}_match_type"] = chatgpt_match_type

            row[f"qwen_{field}_normalized_gt"] = qwen_gt_norm
            row[f"qwen_{field}_normalized_pred"] = qwen_pred_norm
            row[f"chatgpt_{field}_normalized_gt"] = chatgpt_gt_norm
            row[f"chatgpt_{field}_normalized_pred"] = chatgpt_pred_norm

            if field == "vendor_name":
                row["qwen_vendor_fuzzy_score"] = qwen_score
                row["chatgpt_vendor_fuzzy_score"] = chatgpt_score

        if qwen_correct_count > chatgpt_correct_count:
            outcome = "qwen_better"
        elif chatgpt_correct_count > qwen_correct_count:
            outcome = "chatgpt_better"
        else:
            outcome = "tie"

        row["qwen_correct_fields"] = qwen_correct_count
        row["chatgpt_correct_fields"] = chatgpt_correct_count
        row["case_outcome"] = outcome

        outcome_counter[outcome] += 1
        comparison_rows.append(row)

    metrics: dict[str, Any] = {
        "total_compared_records": len(comparison_rows),
        "case_outcome_counts": dict(outcome_counter),
        "parse_counts": dict(parse_counter),
        "vendor_fuzzy_threshold": vendor_fuzzy_threshold,
        "comparison_fields": COMPARE_FIELDS,
    }

    for model_name, prf_dict in [("qwen", qwen_prf), ("chatgpt", chatgpt_prf)]:
        precision_values = []
        recall_values = []
        f1_values = []

        for field in COMPARE_FIELDS:
            prf = prf_from_counts(prf_dict[field])
            metrics[f"{model_name}_{field}_tp"] = prf["tp"]
            metrics[f"{model_name}_{field}_fp"] = prf["fp"]
            metrics[f"{model_name}_{field}_fn"] = prf["fn"]
            metrics[f"{model_name}_{field}_precision"] = prf["precision"]
            metrics[f"{model_name}_{field}_recall"] = prf["recall"]
            metrics[f"{model_name}_{field}_f1"] = prf["f1"]

            precision_values.append(float(prf["precision"]))
            recall_values.append(float(prf["recall"]))
            f1_values.append(float(prf["f1"]))

        metrics[f"{model_name}_macro_precision"] = sum(precision_values) / len(precision_values)
        metrics[f"{model_name}_macro_recall"] = sum(recall_values) / len(recall_values)
        metrics[f"{model_name}_macro_f1"] = sum(f1_values) / len(f1_values)

    return comparison_rows, metrics


# ---------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------

def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []

    lines.append("# ChatGPT vs Qwen2.5-VL Receipt Extraction Comparison\n\n")
    lines.append("This comparison uses the same receipt images and compares three key fields: `vendor_name`, `invoice_date`, and `total`.\n\n")

    lines.append("## Summary\n\n")
    lines.append(f"- Compared records: `{metrics['total_compared_records']}`\n")
    lines.append(f"- Vendor fuzzy threshold: `{metrics['vendor_fuzzy_threshold']}`\n")
    lines.append(f"- Case outcomes: `{metrics['case_outcome_counts']}`\n")
    lines.append(f"- Parse counts: `{metrics['parse_counts']}`\n\n")

    lines.append("## Field-level Precision / Recall / F1\n\n")
    lines.append("| Model | Field | Precision | Recall | F1 | TP | FP | FN |\n")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|\n")

    for model_name in ["qwen", "chatgpt"]:
        for field in COMPARE_FIELDS:
            lines.append(
                f"| {model_name} | {field} | "
                f"{metrics[f'{model_name}_{field}_precision']:.3f} | "
                f"{metrics[f'{model_name}_{field}_recall']:.3f} | "
                f"{metrics[f'{model_name}_{field}_f1']:.3f} | "
                f"{metrics[f'{model_name}_{field}_tp']} | "
                f"{metrics[f'{model_name}_{field}_fp']} | "
                f"{metrics[f'{model_name}_{field}_fn']} |\n"
            )

    lines.append(
        f"| qwen | macro_avg | {metrics['qwen_macro_precision']:.3f} | "
        f"{metrics['qwen_macro_recall']:.3f} | {metrics['qwen_macro_f1']:.3f} | - | - | - |\n"
    )
    lines.append(
        f"| chatgpt | macro_avg | {metrics['chatgpt_macro_precision']:.3f} | "
        f"{metrics['chatgpt_macro_recall']:.3f} | {metrics['chatgpt_macro_f1']:.3f} | - | - | - |\n"
    )

    lines.append("\n## Case-by-case Comparison\n\n")

    for idx, row in enumerate(rows, start=1):
        lines.append(f"### Case {idx}: {row['doc_id']}\n\n")

        if row.get("image_path"):
            lines.append(f"- Image: `{row['image_path']}`\n")

        lines.append(f"- Outcome: `{row['case_outcome']}`\n")
        lines.append(f"- Qwen correct fields: `{row['qwen_correct_fields']}/3`\n")
        lines.append(f"- ChatGPT correct fields: `{row['chatgpt_correct_fields']}/3`\n")
        lines.append(f"- Qwen quality issues: `{row.get('qwen_quality_issues', '')}`\n")
        lines.append(f"- ChatGPT quality issues: `{row.get('chatgpt_quality_issues', '')}`\n\n")

        lines.append("| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |\n")
        lines.append("|---|---|---|---:|---|---:|\n")

        for field in COMPARE_FIELDS:
            lines.append(
                f"| {field} | {row.get(f'gt_{field}')} | "
                f"{row.get(f'qwen_{field}')} | {row.get(f'qwen_{field}_match')} | "
                f"{row.get(f'chatgpt_{field}')} | {row.get(f'chatgpt_{field}_match')} |\n"
            )

        lines.append(
            f"\nVendor fuzzy scores: "
            f"Qwen=`{row.get('qwen_vendor_fuzzy_score')}`, "
            f"ChatGPT=`{row.get('chatgpt_vendor_fuzzy_score')}`\n\n"
        )

    path.write_text("".join(lines), encoding="utf-8")


def print_summary(metrics: dict[str, Any], missing_qwen_doc_ids: list[str]) -> None:
    print("=== ChatGPT vs Qwen2.5-VL Comparison ===")
    print(f"Compared records: {metrics['total_compared_records']}")
    print(f"Case outcomes:    {metrics['case_outcome_counts']}")
    print(f"Parse counts:     {metrics['parse_counts']}")

    if missing_qwen_doc_ids:
        print()
        print("WARNING: ChatGPT doc_ids missing from Qwen baseline:")
        for doc_id in missing_qwen_doc_ids:
            print(f"  - {doc_id}")

    print()
    print("=== Macro P/R/F1 ===")
    print(
        f"Qwen:    {metrics['qwen_macro_precision']:.3f} / "
        f"{metrics['qwen_macro_recall']:.3f} / {metrics['qwen_macro_f1']:.3f}"
    )
    print(
        f"ChatGPT: {metrics['chatgpt_macro_precision']:.3f} / "
        f"{metrics['chatgpt_macro_recall']:.3f} / {metrics['chatgpt_macro_f1']:.3f}"
    )

    print()
    print("=== Field F1 ===")
    for field in COMPARE_FIELDS:
        print(
            f"{field}: Qwen={metrics[f'qwen_{field}_f1']:.3f}, "
            f"ChatGPT={metrics[f'chatgpt_{field}_f1']:.3f}"
        )


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare latest ChatGPT predictions with Qwen2.5-VL baseline results."
    )

    parser.add_argument(
        "--qwen",
        type=str,
        required=True,
        help="Qwen baseline JSONL, e.g. outputs/baseline/qwen_train_sample_100_v2.jsonl",
    )

    parser.add_argument(
        "--chatgpt",
        "--codex",
        dest="chatgpt",
        type=str,
        required=True,
        help="Latest ChatGPT/Codex predictions JSONL.",
    )

    parser.add_argument(
        "--output-md",
        type=str,
        required=True,
        help="Output markdown report path.",
    )

    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Optional summary metrics JSON path.",
    )

    parser.add_argument(
        "--output-csv",
        type=str,
        default=None,
        help="Optional case-by-case CSV path.",
    )

    parser.add_argument(
        "--vendor-fuzzy-threshold",
        type=float,
        default=DEFAULT_VENDOR_FUZZY_THRESHOLD,
        help="Vendor fuzzy threshold in [0, 1]. Default: 0.85.",
    )

    args = parser.parse_args()

    if not 0.0 <= args.vendor_fuzzy_threshold <= 1.0:
        raise ValueError("--vendor-fuzzy-threshold must be in [0, 1].")

    qwen_all_rows = read_jsonl(Path(args.qwen))
    chatgpt_rows = read_jsonl(Path(args.chatgpt))

    qwen_rows, missing_qwen_doc_ids = select_qwen_rows_for_chatgpt_doc_ids(
        qwen_rows=qwen_all_rows,
        chatgpt_rows=chatgpt_rows,
    )

    comparison_rows, metrics = compare_records(
        qwen_rows=qwen_rows,
        chatgpt_rows=chatgpt_rows,
        vendor_fuzzy_threshold=args.vendor_fuzzy_threshold,
    )

    metrics["total_qwen_input_records"] = len(qwen_all_rows)
    metrics["total_chatgpt_input_records"] = len(chatgpt_rows)
    metrics["missing_qwen_doc_ids_for_chatgpt"] = missing_qwen_doc_ids

    write_markdown(Path(args.output_md), comparison_rows, metrics)

    if args.output_json:
        write_json(Path(args.output_json), metrics)

    if args.output_csv:
        write_csv(Path(args.output_csv), comparison_rows)

    print_summary(metrics, missing_qwen_doc_ids)

    print()
    print("=== Outputs ===")
    print(f"Markdown: {args.output_md}")
    if args.output_json:
        print(f"JSON:     {args.output_json}")
    if args.output_csv:
        print(f"CSV:      {args.output_csv}")


if __name__ == "__main__":
    main()
