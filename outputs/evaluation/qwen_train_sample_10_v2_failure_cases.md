# Failure / Review Cases

Total failure / review cases: 1

## Case 1: sroie_train_X51006388065

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006388065.jpg`
- Error types: `document_quality_issue`
- Document quality issues: `blurry text`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | 99 SPEED MART S/B | 99 SPEED MART S/B | True | True | score=1.0, match=True |
| invoice_date | 21-05-17 | 21-05-17 | True | True | - |
| total | 20.80 | 20.80 | True | True | GT norm=20.80, Pred norm=20.80 |

