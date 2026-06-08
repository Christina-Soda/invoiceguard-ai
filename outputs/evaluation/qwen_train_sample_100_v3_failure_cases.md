# Failure Cases

Total failure / review cases: 13

## Case 1: sroie_train_X51006913030

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006913030.jpg`
- Error types: `total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True |
| invoice_date | 10 MAY 2018 | 10 May 2018 | False | True |
| total | $10.30 | 10.30 | False | True |

Note: total value is numerically correct after normalization, but the raw prediction includes formatting/currency differences.

## Case 2: sroie_train_X51006733494

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006733494.jpg`
- Error types: `vendor_mismatch;total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | KEDAI UHAT DAN RUNCIT CHONG HWA | Kedai Ubat Dan Runcit CHONG HWA | False | False |
| invoice_date | OCT 3, 2016 | Oct 3, 2016 | False | True |
| total | RM33.90 | 33.90 | False | True |

Note: total value is numerically correct after normalization, but the raw prediction includes formatting/currency differences.

## Case 3: sroie_train_X51007843145

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51007843145.jpg`
- Error types: `vendor_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | ESJAY FUEL ENTERPRISE | BHPetrol Permas Jaya 2 | False | False |
| invoice_date | 30-06-2018 | 30-06-2018 | True | True |
| total | 50.00 | 50.00 | True | True |

## Case 4: sroie_train_X51005200938

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51005200938.jpg`
- Error types: `total_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | PERNIAGAAN ZHENG HUI | PERNIAGAAN ZHENG HUI | True | True |
| invoice_date | 12/02/2018 | 12/02/2018 | True | True |
| total | 112.45 | 112.46 | False | False |

## Case 5: sroie_train_X51007846307

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51007846307.jpg`
- Error types: `total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True |
| invoice_date | 12 JUN 2018 | 12 Jun 2018 | False | True |
| total | RM7.70 | 7.70 | False | True |

Note: total value is numerically correct after normalization, but the raw prediction includes formatting/currency differences.

## Case 6: sroie_train_X51008123586

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51008123586.jpg`
- Error types: `vendor_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | MYNEWS RETAIL SB | myNEWS.com | False | False |
| invoice_date | 29/06/2018 | 29/06/2018 | True | True |
| total | 7.70 | 7.70 | True | True |

## Case 7: sroie_train_X51006466062

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006466062.jpg`
- Error types: `vendor_mismatch;total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | WESTERN EASTERN ST TIONERY SDN. BHD | WESTERN 'EASTERN' STATIONERY SDN. BHD | False | False |
| invoice_date | 16-04-2018 | 16-04-2018 | True | True |
| total | RM5.00 | 5.00 | False | True |

Note: total value is numerically correct after normalization, but the raw prediction includes formatting/currency differences.

## Case 8: sroie_train_X51008123450

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51008123450.jpg`
- Error types: `parse_failed;vendor_mismatch;date_mismatch;total_mismatch`
- Parse success: `False`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | SANJUNG REALITI SDN. BHD. | None | False | False |
| invoice_date | 27/06/18 | None | False | False |
| total | 1.50 | None | False | False |

## Case 9: sroie_train_X51005745187

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51005745187.jpg`
- Error types: `date_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | SLF CASH & CARRY | SLF CASH & CARRY | True | True |
| invoice_date | 03/02/2018 | 03/03/2018 | False | False |
| total | 21.20 | 21.20 | True | True |

## Case 10: sroie_train_X51006556730

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006556730.jpg`
- Error types: `total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | MAKASSAR FRESH MARKET S/B | MAKASSAR FRESH MARKET S/B. | False | True |
| invoice_date | 05-AUG-2017 | 05-Aug-2017 | False | True |
| total | RM40.00 | 40.00 | False | True |

Note: total value is numerically correct after normalization, but the raw prediction includes formatting/currency differences.

## Case 11: sroie_train_X51006619862

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006619862.jpg`
- Error types: `total_format_only_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | MR. D.I.Y. (KUCHAI) SDN BHD | MR. D.I.Y. (KUCHAI) SDN BHD | True | True |
| invoice_date | 07-06-16 | 07-06-16 | True | True |
| total | RM 13.30 | 13.30 | False | True |

Note: total value is numerically correct after normalization, but the raw prediction includes formatting/currency differences.

## Case 12: sroie_train_X51005361883

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51005361883.jpg`
- Error types: `vendor_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | TEO HENG STATIONERY & BOOKS | TED HENG STATIONERY & BOOKS | False | False |
| invoice_date | 18/01/2018 | 18/01/2018 | True | True |
| total | 4.90 | 4.90 | True | True |

## Case 13: sroie_train_X51006387813

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/train/img/X51006387813.jpg`
- Error types: `vendor_mismatch`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact Match | Normalized Match |
|---|---|---|---:|---:|
| vendor_name | TOKYO KITCHEN (CITTA MALL) TOKYO KITCHEN SDN BHD | TOKYO KITCHEN (CITTA MALL) | False | False |
| invoice_date | 23-04-2017 | 23-04-2017 | True | True |
| total | 113.80 | 113.80 | True | True |

