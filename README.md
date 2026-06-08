# InvoiceGuard AI Baseline v1

InvoiceGuard AI is a receipt and invoice Document AI baseline. It uses Qwen2.5-VL to extract key fields from receipt images, evaluates predictions against SROIE ground truth, applies rule-based review checks, computes confidence scores, and outputs one of three decisions:

- `approve`
- `need_human_review`
- `reject`

This repository version focuses on a simple, reproducible baseline rather than a full production LangGraph agent.

## GPU Machine

The Qwen2.5-VL baseline was run on an **NVIDIA L40S GPU**.

## Dataset

Dataset: SROIE receipt dataset

Main evaluated fields:

- `vendor_name`
- `invoice_date`
- `total`

Additional extracted fields:

- `vendor_address`
- `currency`

## Repository Structure

```text
invoiceguard-ai/
├── agent/
│   ├── confidence.py
│   ├── decision.py
│   ├── review_agent.py
│   ├── rule_engine.py
│   └── schemas.py
├── prompts/
│   ├── receipt_review_v1.txt
│   ├── receipt_review_v2.txt
│   └── receipt_review_v3.txt
├── scripts/
│   ├── compare_codex_qwen.py
│   ├── evaluate_baseline.py
│   ├── preprocess_sroie.py
│   ├── run_qwen_baseline.py
│   └── sample_manifest.py
├── outputs/
│   ├── baseline/
│   ├── comparison/
│   ├── evaluation/
│   ├── examples/
│   └── review/
└── reports/
    ├── baseline_v1_report.md
    └── baseline_v1_report.pdf
```

## Workflow

```text
receipt image
  -> Qwen2.5-VL extraction
  -> structured JSON prediction
  -> field-level evaluation
  -> rule engine
  -> confidence scoring
  -> approve / need_human_review / reject
```

## 1. Run Qwen Baseline

### Train sample

```bash
python scripts/run_qwen_baseline.py   --sample-jsonl outputs/samples/sroie_train_sample_100.jsonl   --prompt prompts/receipt_review_v2.txt   --output outputs/baseline/qwen_train_sample_100_v2.jsonl   --overwrite
```

### Test sample

```bash
python scripts/run_qwen_baseline.py   --sample-jsonl outputs/samples/sroie_test_sample_100.jsonl   --prompt prompts/receipt_review_v2.txt   --output outputs/baseline/qwen_test_sample_100_v2.jsonl   --overwrite
```

## 2. Evaluate Extraction Results

### Train evaluation

```bash
python scripts/evaluate_baseline.py   --input outputs/baseline/qwen_train_sample_100_v2.jsonl   --output-dir outputs/evaluation   --name qwen_train_sample_100_v2   --vendor-fuzzy-threshold 0.85
```

### Test evaluation

```bash
python scripts/evaluate_baseline.py   --input outputs/baseline/qwen_test_sample_100_v2.jsonl   --output-dir outputs/evaluation   --name qwen_test_sample_100_v2   --vendor-fuzzy-threshold 0.85
```

Evaluation outputs:

```text
outputs/evaluation/*_metrics.json
outputs/evaluation/*_field_results.csv
outputs/evaluation/*_failure_cases.md
```

## 3. Run Review Agent

### Train review

```bash
python agent/review_agent.py   --input outputs/baseline/qwen_train_sample_100_v2.jsonl   --output outputs/review/qwen_train_sample_100_v2_reviewed.jsonl
```

### Test review

```bash
python agent/review_agent.py   --input outputs/baseline/qwen_test_sample_100_v2.jsonl   --output outputs/review/qwen_test_sample_100_v2_reviewed.jsonl
```

Review output includes:

- `schema_valid`
- `rule_results`
- `confidence_score`
- `confidence_score_0_10`
- `decision`
- `explanation`

## 4. Evaluate With Review Decisions

```bash
python scripts/evaluate_baseline.py   --input outputs/baseline/qwen_test_sample_100_v2.jsonl   --review-jsonl outputs/review/qwen_test_sample_100_v2_reviewed.jsonl   --output-dir outputs/evaluation   --name qwen_test_sample_100_v2_with_review   --vendor-fuzzy-threshold 0.85
```

## 5. ChatGPT vs Qwen Comparison

```bash
python scripts/compare_codex_qwen.py   --qwen outputs/baseline/qwen_train_sample_100_v2.jsonl   --chatgpt outputs/comparison/chatgpt_train_sample_10_predictions.jsonl   --output-md outputs/comparison/chatgpt_vs_qwen_train_sample_10.md   --output-json outputs/comparison/chatgpt_vs_qwen_train_sample_10_metrics.json   --output-csv outputs/comparison/chatgpt_vs_qwen_train_sample_10_cases.csv   --vendor-fuzzy-threshold 0.85
```

This comparison focuses on:

- `vendor_name`
- `invoice_date`
- `total`

## Baseline Results Summary

| Split | Parse success | Vendor fuzzy acc. | Date norm. acc. | Total norm. acc. | All-key fuzzy acc. | Macro F1 | Decisions |
|---|---:|---:|---:|---:|---:|---:|---|
| Train 100 | 100.0% | 97.0% | 99.0% | 98.0% | 94.0% | 0.980 | {'need_human_review': 10, 'approve': 90} |
| Test 100 | 100.0% | 95.0% | 97.0% | 98.0% | 90.0% | 0.967 | {'approve': 95, 'need_human_review': 5} |

## Report

The full baseline v1 report is available at:

```text
reports/baseline_v1_report.md
reports/baseline_v1_report.pdf
```

## Current Scope

This is baseline v1. It does not yet include:

- LangGraph workflow packaging
- PostgreSQL duplicate detection
- fine-tuning
- RL
- production deployment

These are planned after the extraction and review baseline is stable.
