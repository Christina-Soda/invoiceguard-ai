# ChatGPT vs Qwen2.5-VL Receipt Extraction Comparison

This comparison uses the same receipt images and compares three key fields: `vendor_name`, `invoice_date`, and `total`.

## Summary

- Compared records: `10`
- Vendor fuzzy threshold: `0.85`
- Case outcomes: `{'tie': 10}`
- Parse counts: `{'qwen_parse_True': 10, 'chatgpt_parse_True': 10}`

## Field-level Precision / Recall / F1

| Model | Field | Precision | Recall | F1 | TP | FP | FN |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen | vendor_name | 1.000 | 1.000 | 1.000 | 10 | 0 | 0 |
| qwen | invoice_date | 1.000 | 1.000 | 1.000 | 10 | 0 | 0 |
| qwen | total | 1.000 | 1.000 | 1.000 | 10 | 0 | 0 |
| chatgpt | vendor_name | 1.000 | 1.000 | 1.000 | 10 | 0 | 0 |
| chatgpt | invoice_date | 1.000 | 1.000 | 1.000 | 10 | 0 | 0 |
| chatgpt | total | 1.000 | 1.000 | 1.000 | 10 | 0 | 0 |
| qwen | macro_avg | 1.000 | 1.000 | 1.000 | - | - | - |
| chatgpt | macro_avg | 1.000 | 1.000 | 1.000 | - | - | - |

## Case-by-case Comparison

### Case 1: sroie_train_X51006388065

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006388065.jpg`
- Outcome: `tie`
- Qwen correct fields: `3/3`
- ChatGPT correct fields: `3/3`
- Qwen quality issues: `blurry text`
- ChatGPT quality issues: `poor_contrast;stained_text`

| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |
|---|---|---|---:|---|---:|
| vendor_name | 99 SPEED MART S/B | 99 SPEED MART S/B | True | 99 SPEED MART S/B | True |
| invoice_date | 21-05-17 | 21-05-17 | True | 21-05-17 | True |
| total | 20.80 | 20.80 | True | 20.80 | True |

Vendor fuzzy scores: Qwen=`1.0`, ChatGPT=`1.0`

### Case 2: sroie_train_X51006441474

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006441474.jpg`
- Outcome: `tie`
- Qwen correct fields: `3/3`
- ChatGPT correct fields: `3/3`
- Qwen quality issues: ``
- ChatGPT quality issues: ``

| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |
|---|---|---|---:|---|---:|
| vendor_name | TF VALUE-MART SDN BHD | TF Value-Mart Sdn Bhd | True | TF Value-Mart Sdn Bhd | True |
| invoice_date | 19/05/18 | 19/05/18 | True | 19/05/18 | True |
| total | 52.80 | 52.80 | True | 52.80 | True |

Vendor fuzzy scores: Qwen=`1.0`, ChatGPT=`1.0`

### Case 3: sroie_train_X51008164997

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51008164997.jpg`
- Outcome: `tie`
- Qwen correct fields: `3/3`
- ChatGPT correct fields: `3/3`
- Qwen quality issues: ``
- ChatGPT quality issues: `poor_contrast;blurry_text`

| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |
|---|---|---|---:|---|---:|
| vendor_name | ONE ONE THREE SEAFOOD RESTAURANT SDN BHD | ONE ONE THREE SEAFOOD RESTAURANT SDN BHD | True | ONE ONE THREE SEAFOOD RESTAURANT SDN BHD | True |
| invoice_date | 15-06-2018 | 15-06-2018 | True | 15-06-2018 | True |
| total | 148.50 | 148.50 | True | 148.50 | True |

Vendor fuzzy scores: Qwen=`1.0`, ChatGPT=`1.0`

### Case 4: sroie_train_X51005453802

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51005453802.jpg`
- Outcome: `tie`
- Qwen correct fields: `3/3`
- ChatGPT correct fields: `3/3`
- Qwen quality issues: ``
- ChatGPT quality issues: ``

| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |
|---|---|---|---:|---|---:|
| vendor_name | LIAN HING STATIONERY SDN BHD | LIAN HING STATIONERY SDN BHD | True | LIAN HING STATIONERY SDN BHD | True |
| invoice_date | 30/03/2018 | 30/03/2018 | True | 30/03/2018 | True |
| total | 159.00 | 159.00 | True | 159.00 | True |

Vendor fuzzy scores: Qwen=`1.0`, ChatGPT=`1.0`

### Case 5: sroie_train_X51008114266

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51008114266.jpg`
- Outcome: `tie`
- Qwen correct fields: `3/3`
- ChatGPT correct fields: `3/3`
- Qwen quality issues: ``
- ChatGPT quality issues: `poor_contrast;stained_text`

| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |
|---|---|---|---:|---|---:|
| vendor_name | 99 SPEED MART S/B | 99 SPEED MART S/B | True | 99 SPEED MART S/B | True |
| invoice_date | 13-05-18 | 13-05-18 | True | 13-05-18 | True |
| total | 22.90 | 22.90 | True | 22.90 | True |

Vendor fuzzy scores: Qwen=`1.0`, ChatGPT=`1.0`

### Case 6: sroie_train_X51005268262

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51005268262.jpg`
- Outcome: `tie`
- Qwen correct fields: `3/3`
- ChatGPT correct fields: `3/3`
- Qwen quality issues: ``
- ChatGPT quality issues: ``

| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |
|---|---|---|---:|---|---:|
| vendor_name | HOME MASTER HARDWARE & ELECTRICAL | HOME MASTER HARDWARE & ELECTRICAL | True | HOME MASTER HARDWARE & ELECTRICAL | True |
| invoice_date | 22/12/2017 | 22/12/2017 | True | 22/12/2017 | True |
| total | 15.90 | 15.90 | True | 15.90 | True |

Vendor fuzzy scores: Qwen=`1.0`, ChatGPT=`1.0`

### Case 7: sroie_train_X51008099083

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51008099083.jpg`
- Outcome: `tie`
- Qwen correct fields: `3/3`
- ChatGPT correct fields: `3/3`
- Qwen quality issues: ``
- ChatGPT quality issues: `poor_contrast;blurry_text`

| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |
|---|---|---|---:|---|---:|
| vendor_name | RESTORAN WAN SHENG | RESTORAN WAN SHENG | True | RESTORAN WAN SHENG | True |
| invoice_date | 04-06-2018 | 04-06-2018 | True | 04-06-2018 | True |
| total | 6.70 | 6.70 | True | 6.70 | True |

Vendor fuzzy scores: Qwen=`1.0`, ChatGPT=`1.0`

### Case 8: sroie_train_X51008142063

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51008142063.jpg`
- Outcome: `tie`
- Qwen correct fields: `3/3`
- ChatGPT correct fields: `3/3`
- Qwen quality issues: ``
- ChatGPT quality issues: ``

| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |
|---|---|---|---:|---|---:|
| vendor_name | KEDAI PAPAN YEW CHUAN | KEDAI PAPAN YEW CHUAN | True | KEDAI PAPAN YEW CHUAN | True |
| invoice_date | 30/04/2018 | 30/04/2018 | True | 30/04/2018 | True |
| total | 404.39 | 404.39 | True | 404.39 | True |

Vendor fuzzy scores: Qwen=`1.0`, ChatGPT=`1.0`

### Case 9: sroie_train_X51007103702

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51007103702.jpg`
- Outcome: `tie`
- Qwen correct fields: `3/3`
- ChatGPT correct fields: `3/3`
- Qwen quality issues: ``
- ChatGPT quality issues: ``

| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |
|---|---|---|---:|---|---:|
| vendor_name | MR. D.I.Y. (M) SDN BHD | MR. D.I.Y. (M) SDN BHD | True | MR. D.I.Y. (M) SDN BHD | True |
| invoice_date | 30-04-18 | 30-04-18 | True | 30-04-18 | True |
| total | 5.00 | 5.00 | True | 5.00 | True |

Vendor fuzzy scores: Qwen=`1.0`, ChatGPT=`1.0`

### Case 10: sroie_train_X51005685357

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51005685357.jpg`
- Outcome: `tie`
- Qwen correct fields: `3/3`
- ChatGPT correct fields: `3/3`
- Qwen quality issues: ``
- ChatGPT quality issues: `poor_contrast`

| Field | Ground Truth | Qwen | Qwen Match | ChatGPT | ChatGPT Match |
|---|---|---|---:|---|---:|
| vendor_name | FARMASI MALURI S/B | Farmasi Maluri S/B | True | Farmasi Maluri S/B | True |
| invoice_date | 02/03/18 | 02/03/18 | True | 02/03/18 | True |
| total | 79.35 | 79.35 | True | 79.35 | True |

Vendor fuzzy scores: Qwen=`1.0`, ChatGPT=`1.0`

