# Failure Cases

Total failure / review cases: 1

## Case 1: sroie_train_X51006913030

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006913030.jpg`
- Error types: `total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True |
| invoice_date | 10 MAY 2018 | 10 May 2018 12:32 | False | True |
| total | $10.30 | 10.30 | False | True |

Note: total value is numerically correct after normalization, but the raw prediction includes formatting/currency differences.

