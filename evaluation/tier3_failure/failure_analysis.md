# Tier 3 Failure Analysis

This file records failure cases discovered during evaluation.

| Sample ID | Failure Type | Expected Decision | Predicted Decision | Failed Field | Predicted Value | Ground Truth | Rule Triggered | Failure Reason | Improvement Direction |
|---|---|---|---|---|---|---|---|---|---|
| fail_001 | duplicate_invoice | reject | TBD | invoice_number | TBD | TBD | duplicate_check | TBD | Seed duplicate invoice records before evaluation |
| fail_002 | unknown_vendor | reject | TBD | vendor_name | TBD | TBD | vendor_check | TBD | Improve vendor lookup and fuzzy matching |
| fail_003 | math_error | reject | TBD | total | TBD | TBD | math_check | TBD | Tighten total/subtotal/tax consistency rule |
| fail_004 | future_date | needs_human_review | TBD | invoice_date | TBD | TBD | date_check | TBD | Improve date parsing and future-date rule |
| fail_005 | low_quality | needs_human_review | TBD | multiple | TBD | TBD | quality_check | TBD | Add image quality scoring before VLM extraction |

## Notes

- `Expected Decision` is manually assigned.
- `Predicted Decision` is produced by the pipeline.
- `Failure Reason` should explain why the system failed or why the sample is difficult.
- `Improvement Direction` should describe what to change in preprocessing, VLM prompting, rule engine, grounding, or human-review routing.
