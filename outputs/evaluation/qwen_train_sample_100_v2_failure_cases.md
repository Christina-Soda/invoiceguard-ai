# Failure / Review Cases

Total failure / review cases: 22

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

## Case 2: sroie_train_X51006913030

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006913030.jpg`
- Error types: `total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 10 MAY 2018 | 10 May 2018 12:32 | False | True | - |
| total | $10.30 | 10.30 | False | True | GT norm=10.30, Pred norm=10.30 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 3: sroie_train_X51006414713

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006414713.jpg`
- Error types: `document_quality_issue`
- Document quality issues: `blurred text`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | YHM AEON TEBRAU CITY | YHM Aeon Tebrau City | False | True | score=1.0, match=True |
| invoice_date | 17/04/2018 | 17/04/2018 | True | True | - |
| total | 81.80 | 81.80 | True | True | GT norm=81.80, Pred norm=81.80 |

## Case 4: sroie_train_X51006335552

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006335552.jpg`
- Error types: `document_quality_issue`
- Document quality issues: `blurred text;handwritten signature`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | YONG SOON FATT S/B | YONG SOON FATT S/B | True | True | score=1.0, match=True |
| invoice_date | 6/2/2017 | 6/2/2017 | True | True | - |
| total | 758.70 | 758.70 | True | True | GT norm=758.70, Pred norm=758.70 |

## Case 5: sroie_train_X51007339658

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51007339658.jpg`
- Error types: `document_quality_issue`
- Document quality issues: `handwritten text`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | AIK HUAT HARDWARE ENTERPRISE (SETIA ALAM) SDN BHD | AIK HUAT HARDWARE ENTERPRISE (SETIA ALAM) SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 04/09/2017 | 04/09/2017 | True | True | - |
| total | 28.00 | 28.00 | True | True | GT norm=28.00, Pred norm=28.00 |

## Case 6: sroie_train_X51006733494

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006733494.jpg`
- Error types: `vendor_fuzzy_only_match;total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | KEDAI UHAT DAN RUNCIT CHONG HWA | Kedai Ubat Dan Runcit CHONG HWA | False | False | score=0.9677, match=True |
| invoice_date | OCT 3, 2016 | Oct 3, 2016 | False | True | - |
| total | RM33.90 | 33.90 | False | True | GT norm=33.90, Pred norm=33.90 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

Note: vendor failed strict normalization but passed fuzzy matching. This is likely a naming/OCR variation rather than a complete miss.

## Case 7: sroie_train_X51007843145

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51007843145.jpg`
- Error types: `vendor_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | ESJAY FUEL ENTERPRISE | BHPetrol Permas Jaya 2 | False | False | score=0.2791, match=False |
| invoice_date | 30-06-2018 | 30-06-2018 | True | True | - |
| total | 50.00 | 50.00 | True | True | GT norm=50.00, Pred norm=50.00 |

## Case 8: sroie_train_X51005200938

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51005200938.jpg`
- Error types: `total_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | PERNIAGAAN ZHENG HUI | PERNIAGAAN ZHENG HUI | True | True | score=1.0, match=True |
| invoice_date | 12/02/2018 | 12/02/2018 | True | True | - |
| total | 112.45 | 112.46 | False | False | GT norm=112.45, Pred norm=112.46 |

## Case 9: sroie_train_X51007846307

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51007846307.jpg`
- Error types: `total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 12 JUN 2018 | 12 Jun 2018 16:14 | False | True | - |
| total | RM7.70 | 7.70 | False | True | GT norm=7.70, Pred norm=7.70 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 10: sroie_train_X51008123586

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51008123586.jpg`
- Error types: `vendor_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | MYNEWS RETAIL SB | myNEWS.com | False | False | score=0.4516, match=False |
| invoice_date | 29/06/2018 | 29/06/2018 | True | True | - |
| total | 7.70 | 7.70 | True | True | GT norm=7.70, Pred norm=7.70 |

## Case 11: sroie_train_X51006466062

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006466062.jpg`
- Error types: `vendor_fuzzy_only_match;total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | WESTERN EASTERN ST TIONERY SDN. BHD | WESTERN EASTERN STATIONERY SDN. BHD | False | False | score=0.9706, match=True |
| invoice_date | 16-04-2018 | 16-04-2018 | True | True | - |
| total | RM5.00 | 5.00 | False | True | GT norm=5.00, Pred norm=5.00 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

Note: vendor failed strict normalization but passed fuzzy matching. This is likely a naming/OCR variation rather than a complete miss.

## Case 12: sroie_train_X51007339156

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51007339156.jpg`
- Error types: `document_quality_issue`
- Document quality issues: `OCR issues with some text`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | SANYU STATIONERY SHOP | SANYU STATIONERY SHOP | True | True | score=1.0, match=True |
| invoice_date | 08/07/2017 | 08/07/2017 | True | True | - |
| total | 8.70 | 8.70 | True | True | GT norm=8.70, Pred norm=8.70 |

## Case 13: sroie_train_X51006414703

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006414703.jpg`
- Error types: `total_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | AEON CO. (M) BHD | AEON CO., (M) BHD | False | True | score=1.0, match=True |
| invoice_date | 22/04/2018 | 22/04/2018 | True | True | - |
| total | 98.35 | 88.35 | False | False | GT norm=98.35, Pred norm=88.35 |

## Case 14: sroie_train_X51006867436

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006867436.jpg`
- Error types: `document_quality_issue`
- Document quality issues: `blurred text`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | GUARDIAN HEALTH AND BEAUTY SDN BHD | Guardian Health And Beauty Sdn Bhd | False | True | score=1.0, match=True |
| invoice_date | 24/05/18 | 24/05/18 | True | True | - |
| total | 4.50 | 4.50 | True | True | GT norm=4.50, Pred norm=4.50 |

## Case 15: sroie_train_X51007339152

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51007339152.jpg`
- Error types: `document_quality_issue`
- Document quality issues: `tear`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | SANYU STATIONERY SHOP | SANYU STATIONERY SHOP | True | True | score=1.0, match=True |
| invoice_date | 06/07/2017 | 06/07/2017 | True | True | - |
| total | 4.50 | 4.50 | True | True | GT norm=4.50, Pred norm=4.50 |

## Case 16: sroie_train_X51005745187

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51005745187.jpg`
- Error types: `date_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | SLF CASH & CARRY | SLF CASH & CARRY | True | True | score=1.0, match=True |
| invoice_date | 03/02/2018 | 03/03/2018 | False | False | - |
| total | 21.20 | 21.20 | True | True | GT norm=21.20, Pred norm=21.20 |

## Case 17: sroie_train_X51005757290

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51005757290.jpg`
- Error types: `document_quality_issue`
- Document quality issues: `text_overlap`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | MR. D.I.Y. (M) SDN BHD | MR. D.I.Y. (M) SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 17-03-18 | 17-03-18 | True | True | - |
| total | 42.90 | 42.90 | True | True | GT norm=42.90, Pred norm=42.90 |

## Case 18: sroie_train_X51007339133

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51007339133.jpg`
- Error types: `document_quality_issue`
- Document quality issues: `folds`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | SANYU STATIONERY SHOP | SANYU STATIONERY SHOP | True | True | score=1.0, match=True |
| invoice_date | 27/10/2017 | 27/10/2017 | True | True | - |
| total | 8.70 | 8.70 | True | True | GT norm=8.70, Pred norm=8.70 |

## Case 19: sroie_train_X51006556730

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006556730.jpg`
- Error types: `total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | MAKASSAR FRESH MARKET S/B | MAKASSAR FRESH MARKET S/B. | False | True | score=1.0, match=True |
| invoice_date | 05-AUG-2017 | 05-Aug-2017 | False | True | - |
| total | RM40.00 | 40.00 | False | True | GT norm=40.00, Pred norm=40.00 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 20: sroie_train_X51006557117

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006557117.jpg`
- Error types: `document_quality_issue`
- Document quality issues: `blurred text`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | GARDENIA BAKERIES (KL) SDN BHD | GARDENIA BAKERIES (KL) SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 30/10/2017 | 30/10/2017 | True | True | - |
| total | 62.60 | 62.60 | True | True | GT norm=62.60, Pred norm=62.60 |

## Case 21: sroie_train_X51006619862

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006619862.jpg`
- Error types: `total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | MR. D.I.Y. (KUCHAI) SDN BHD | MR. D.I.Y. (KUCHAI) SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 07-06-16 | 07-06-16 | True | True | - |
| total | RM 13.30 | 13.30 | False | True | GT norm=13.30, Pred norm=13.30 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 22: sroie_train_X51005568827

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51005568827.jpg`
- Error types: `vendor_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | BANH MI CAFE SDN BHD | Banh Mi Cafe | False | False | score=0.75, match=False |
| invoice_date | 29-10-2017 | 29-10-2017 | True | True | - |
| total | 23.25 | 23.25 | True | True | GT norm=23.25, Pred norm=23.25 |

