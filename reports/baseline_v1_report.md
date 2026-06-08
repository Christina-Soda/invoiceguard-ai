# InvoiceGuard AI Baseline v1 Report

**Project:** Receipt Extraction and Review Agent  
**Model:** Qwen2.5-VL-7B-Instruct  
**GPU machine:** NVIDIA L40S  
**Dataset:** SROIE receipt dataset  
**Report date:** 2026-06-08

## 1. Goal

InvoiceGuard AI is a baseline Document AI / VLM pipeline for receipt review. Given a receipt image, the system extracts structured fields, evaluates them against ground truth, applies rule-based checks, computes a confidence score, and outputs one of three review decisions:

- `approve`
- `need_human_review`
- `reject`

This version focuses on a simple runnable baseline rather than a full LangGraph production agent.

## 2. Dataset and Inputs

The baseline uses SROIE receipt images. Each sample includes a receipt image and unified ground-truth fields from preprocessing. The main evaluated fields are:

- `vendor_name`
- `invoice_date`
- `total`

The model also extracts `vendor_address` and `currency`, but the primary metrics in this baseline report focus on vendor, date, and total.

## 3. System Workflow

```text
receipt image
  -> Qwen2.5-VL extraction
  -> structured JSON prediction
  -> field-level evaluation
  -> rule engine
  -> confidence scoring
  -> approve / need_human_review / reject
```

The main code files are:

- `scripts/run_qwen_baseline.py`
- `scripts/evaluate_baseline.py`
- `scripts/compare_codex_qwen.py`
- `agent/schemas.py`
- `agent/rule_engine.py`
- `agent/confidence.py`
- `agent/decision.py`
- `agent/review_agent.py`

## 4. GPU Environment

The Qwen2.5-VL baseline was run on an **NVIDIA L40S GPU**. This is important because Qwen2.5-VL-7B is too large for comfortable inference on smaller 16 GB GPUs in this project setup.

## 5. Prompt Engineering Summary

Three prompt versions were tested:

- `receipt_review_v1.txt`: initial simple extraction prompt.
- `receipt_review_v2.txt`: stable structured JSON extraction prompt.
- `receipt_review_v3.txt`: uncertainty-aware prompt with blurry text, ambiguous vendor, unclear amount, and human-review signals.

Prompt v2 is selected as the final baseline extraction prompt. Prompt v3 attempted to add uncertainty detection, but it reduced JSON stability and did not reliably produce useful document quality labels.

| Prompt | Sample | Parse success | Vendor normalized | Date normalized | Total normalized | All-key normalized |
|---|---:|---:|---:|---:|---:|---:|
| v2 | train 100 | 100.0% | 94.0% | 99.0% | 98.0% | 91.0% |
| v3 | train 100 | 99.0% | 93.0% | 98.0% | 98.0% | 91.0% |

Conclusion: v3 ideas are useful for rule design, but v2 is more reliable for extraction. Uncertainty handling is therefore moved to `rule_engine.py` and `confidence.py`.

## 6. Evaluation Definitions

The evaluation uses several matching strategies:

- `vendor_name`: exact, normalized, and fuzzy matching. Fuzzy threshold is 0.85.
- `invoice_date`: normalized date matching.
- `total`: normalized numeric amount matching.

Field-level precision, recall, and F1 use this fixed-field extraction definition:

- TP: ground truth exists, prediction exists, and they match.
- FP: prediction exists but does not match the ground truth.
- FN: ground truth exists but prediction is missing or incorrect.

If a ground-truth field exists and the model predicts a wrong value, the case counts as both FP and FN.

## 7. Train Sample Results - Qwen v2

| Metric | Value |
|---|---:|
| Total records | 100 |
| Parse success rate | 100.0% |
| Vendor exact accuracy | 80.0% |
| Vendor normalized accuracy | 94.0% |
| Vendor fuzzy accuracy | 97.0% |
| Date normalized accuracy | 99.0% |
| Total normalized accuracy | 98.0% |
| All key fields normalized accuracy | 91.0% |
| All key fields fuzzy accuracy | 94.0% |
| Vendor P/R/F1 | 0.970 / 0.970 / 0.970 |
| Date P/R/F1 | 0.990 / 0.990 / 0.990 |
| Total P/R/F1 | 0.980 / 0.980 / 0.980 |
| Macro P/R/F1 | 0.980 / 0.980 / 0.980 |
| Decision counts | {'need_human_review': 10, 'approve': 90} |


Key observations:

- Parse success is 100% on the train sample.
- Fuzzy vendor accuracy is higher than normalized vendor accuracy because many vendor mismatches are punctuation, spelling, or legal-name variants.
- Total normalized accuracy is high, but exact total accuracy is lower due to currency-format differences such as `RM 5.00` vs `5.00`.
- The review agent approved 90 receipts and sent 10 receipts to human review.

## 8. Held-out Test Sample Results - Qwen v2

| Metric | Value |
|---|---:|
| Total records | 100 |
| Parse success rate | 100.0% |
| Vendor exact accuracy | 79.0% |
| Vendor normalized accuracy | 89.0% |
| Vendor fuzzy accuracy | 95.0% |
| Date normalized accuracy | 97.0% |
| Total normalized accuracy | 98.0% |
| All key fields normalized accuracy | 84.0% |
| All key fields fuzzy accuracy | 90.0% |
| Vendor P/R/F1 | 0.950 / 0.950 / 0.950 |
| Date P/R/F1 | 0.970 / 0.970 / 0.970 |
| Total P/R/F1 | 0.980 / 0.980 / 0.980 |
| Macro P/R/F1 | 0.967 / 0.967 / 0.967 |
| Decision counts | {'approve': 95, 'need_human_review': 5} |


Key observations:

- Parse success remains 100% on the held-out test sample.
- All-key-field fuzzy accuracy is 90.0%, compared with 94.0% on the train sample.
- Macro F1 is 0.967 on the held-out test sample.
- The review agent approved 95 receipts and sent 5 receipts to human review.

## 9. Rule Engine

The baseline rule engine checks:

1. parse success
2. required critical fields
3. field-level confidence
4. numeric total validity
5. total math consistency when subtotal/tax/discount are available
6. date validity
7. optional vendor fuzzy check
8. document quality issues
9. high amount risk

For SROIE receipts, the critical required fields are:

- `vendor_name`
- `invoice_date`
- `total`

`invoice_number` is not required because many receipts do not contain it.

## 10. Confidence Scoring and Decision Logic

The confidence score combines:

- parse score
- VLM self confidence
- schema score
- rule score
- required-field completeness
- field-level confidence

The system outputs both `confidence_score` in 0-1 and `confidence_score_0_10` in 0-10.

Decision thresholds:

| Score range | Decision |
|---:|---|
| 0-2 | reject |
| 3-7 | need_human_review |
| 8-10 | approve |

Rule overrides:

- parse failure -> reject
- critical rule failure -> reject
- high severity warning/failure -> need_human_review
- any warning -> need_human_review

Average confidence scores:

| Split | Average confidence 0-10 | Decision counts |
|---|---:|---|
| Train 100 | 9.790 | {'need_human_review': 10, 'approve': 90} |
| Test 100 | 9.733 | {'approve': 95, 'need_human_review': 5} |

## 11. ChatGPT vs Qwen Comparison

A small 10-image sample was extracted by ChatGPT and compared with Qwen. The comparison fields are `vendor_name`, `invoice_date`, and `total`.

| Model | Vendor F1 | Date F1 | Total F1 | Macro F1 |
|---|---:|---:|---:|---:|
| Qwen2.5-VL | 1.000 | 1.000 | 1.000 | 1.000 |
| ChatGPT | 1.000 | 1.000 | 1.000 | 1.000 |

Case outcome counts: `{'tie': 10}`.

This comparison is a small qualitative reference, not a full benchmark. It shows that Qwen can match ChatGPT on easy clean examples, but more diverse samples are needed for a stronger comparison.

## 12. Examples and Failure Cases

### Example 1 - Correct extraction and approve

- `doc_id`: `sroie_test_X51005711444`
- Image: `.../SROIE2019/test/img/X51005711444.jpg`
- Ground truth vendor: `RESTORAN WAN SHENG`
- Qwen vendor: `RESTORAN WAN SHENG`
- Ground truth date: `21-03-2018`
- Qwen date: `21-03-2018`
- Ground truth total: `4.80`
- Qwen total: `4.80`
- Decision: `approve`
- Reason: all key fields match after normalization.

### Example 2 - Correct fields but human review due to document quality

- `doc_id`: `sroie_test_X51007846355`
- Image: `.../SROIE2019/test/img/X51007846355.jpg`
- Ground truth vendor: `AEON CO. (M) BHD`
- Qwen vendor: `AEON CO. (M) BHD`
- Ground truth date: `17/06/2018`
- Qwen date: `17/06/2018`
- Ground truth total: `8.95`
- Qwen total: `8.95`
- Error type: `document_quality_issue`
- Decision: `need_human_review`
- Reason: extracted values are correct, but the rule engine routes quality-issue samples to human review.

### Example 3 - Total mismatch that current decision logic still approved

- `doc_id`: `sroie_test_X51005745244`
- Image: `.../SROIE2019/test/img/X51005745244.jpg`
- Ground truth vendor: `URBAN IDEA SDN BHD`
- Qwen vendor: `URBAN IDEA SDN BHD`
- Ground truth date: `14/02/2018`
- Qwen date: `14/02/2018`
- Ground truth total: `RM11.90`
- Qwen total: `11.23`
- Error type: `total_mismatch`
- Decision: `approve`
- Limitation: this shows that the current review agent only uses model output and internal rules. It does not know the ground truth during production. Future versions should make total-risk rules more conservative.

### Example 4 - Vendor fuzzy match handles spelling variation

- `doc_id`: `sroie_test_X51006329183`
- Image: `.../SROIE2019/test/img/X51006329183.jpg`
- Ground truth vendor: `SEMBOYAN TEGAS SDN BHD`
- Qwen vendor: `SEMOYAN TEGAS SDN BHD`
- Vendor fuzzy score: `0.9767`
- Date and total: correct
- Error type: `vendor_fuzzy_only_match`
- Decision: `approve`
- Reason: exact vendor spelling differs, but fuzzy matching correctly treats this as a near-equivalent vendor extraction.

### Example 5 - Legal/display vendor ambiguity

- `doc_id`: `sroie_test_X51005230616`
- Image: `.../SROIE2019/test/img/X51005230616.jpg`
- Ground truth vendor: `GERBANG ALAF RESTAURANTS SDN BHD`
- Qwen vendor: `Gerbang Alaf Restaurants Sdn Bhd (65351-M) formerly known as Golden Arches Restaurants Sdn Bhd Licensee of McDonald's`
- Vendor fuzzy score: `0.4354`
- Date and total: correct
- Error type: `vendor_mismatch`
- Decision: `approve`
- Limitation: the model extracted a longer legal/company description rather than the target entity string. Future work should improve vendor canonicalization.

### Example 6 - Prompt v3 JSON parse failure

- `doc_id`: `sroie_train_X51008123450`
- Image: `.../SROIE2019/train/img/X51008123450.jpg`
- Ground truth vendor: `SANJUNG REALITI SDN. BHD.`
- Ground truth date: `27/06/18`
- Ground truth total: `1.50`
- Prompt version: v3
- Error type: `parse_failed;vendor_mismatch;date_mismatch;total_mismatch`
- Reason: v3 added uncertainty instructions but produced an invalid/incomplete JSON output for this sample.
- Lesson: keep v2 as the stable extraction prompt and move uncertainty handling into rules and confidence scoring.

## 13. Current Limitations

1. The review agent does not see ground truth at inference time, so some wrong extractions can still be approved if the model is confident and no internal rule fails.
2. ChatGPT comparison currently uses only 10 samples. This is useful for qualitative comparison but not enough for a full benchmark.
3. Document quality labels are not yet reliable enough to serve as a complete risk detector.
4. Duplicate detection and vendor database checks are placeholders.
5. The pipeline is not yet packaged as a LangGraph workflow.

## 14. Next Steps

1. Make total mismatch risk handling more conservative.
2. Add stronger vendor canonicalization for legal name vs display name differences.
3. Expand ChatGPT vs Qwen comparison beyond 10 examples.
4. Add OCR-assisted features or image quality checks before VLM extraction.
5. Add PostgreSQL duplicate detection.
6. Package the pipeline into a LangGraph state-machine workflow after the baseline stabilizes.
