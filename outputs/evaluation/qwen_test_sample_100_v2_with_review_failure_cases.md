# Failure / Review Cases

Total failure / review cases: 31

## Case 1: sroie_test_X51005745244

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51005745244.jpg`
- Error types: `total_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | URBAN IDEA SDN BHD | URBAN IDEA SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 14/02/2018 | 14/02/2018 | True | True | - |
| total | RM11.90 | 11.23 | False | False | GT norm=11.90, Pred norm=11.23 |

## Case 2: sroie_test_X51007846355

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007846355.jpg`
- Error types: `document_quality_issue`
- Agent decision: `need_human_review`
- Document quality issues: `blurred text`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | AEON CO. (M) BHD | AEON CO. (M) BHD | True | True | score=1.0, match=True |
| invoice_date | 17/06/2018 | 17/06/2018 | True | True | - |
| total | 8.95 | 8.95 | True | True | GT norm=8.95, Pred norm=8.95 |

## Case 3: sroie_test_X51006619700

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006619700.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | MR. D.I.Y. (KUCHAI) SDN BHD | MR. D.I.Y. (KUCHAI) SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 10-01-16 | 10-01-16 | True | True | - |
| total | RM 8.10 | 8.10 | False | True | GT norm=8.10, Pred norm=8.10 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 4: sroie_test_X51007846372

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007846372.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 14 JUN 2018 | 14 Jun 2018 18:27 | False | True | - |
| total | RM10.15 | 10.15 | False | True | GT norm=10.15, Pred norm=10.15 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 5: sroie_test_X51007846397

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007846397.jpg`
- Error types: `vendor_fuzzy_only_match;total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERANTIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | False | False | score=0.9667, match=True |
| invoice_date | 21 JUN 2018 | 21 Jun 2018 18:30 | False | True | - |
| total | RM7.70 | 7.70 | False | True | GT norm=7.70, Pred norm=7.70 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

Note: vendor failed strict normalization but passed fuzzy matching. This is likely a naming/OCR variation rather than a complete miss.

## Case 6: sroie_test_X51005442334

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51005442334.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 26 MAR 2018 | 26 Mar 2018 18:14 | False | True | - |
| total | $8.20 | 8.20 | False | True | GT norm=8.20, Pred norm=8.20 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 7: sroie_test_X51006349083

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006349083.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | CHA FOR TEA | CHA FOR TEA | True | True | score=1.0, match=True |
| invoice_date | 19/04/2018 | 19/04/2018 | True | True | - |
| total | RM46.25 | 46.25 | False | True | GT norm=46.25, Pred norm=46.25 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 8: sroie_test_X51006349085

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006349085.jpg`
- Error types: `vendor_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | PLATINUM RACKING SDN BHD | PLATINUM RACKING SDN BHD (PLAT MART) | False | False | score=0.8276, match=False |
| invoice_date | 22/04/2018 | 22/04/2018 | True | True | - |
| total | 23.00 | 23.00 | True | True | GT norm=23.00, Pred norm=23.00 |

## Case 9: sroie_test_X51006619328

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006619328.jpg`
- Error types: `document_quality_issue`
- Agent decision: `need_human_review`
- Document quality issues: `slight crease`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | YIN MA (M) SDN.BHD. | YIN MA (M) SDN.BHD. | True | True | score=1.0, match=True |
| invoice_date | 31 JAN 2016 | 31 Jan 2016 | False | True | - |
| total | 5.40 | 5.40 | True | True | GT norm=5.40, Pred norm=5.40 |

## Case 10: sroie_test_X51006387931

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006387931.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | AMANO MALAYSIA SDN BHD | AMANO MALAYSIA SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 30/04/2017 | 30/04/2017 | True | True | - |
| total | RM3.00 | 3.00 | False | True | GT norm=3.00, Pred norm=3.00 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 11: sroie_test_X51007103649

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007103649.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | MR. D.I.Y. (M) SDN BHD | MR. D.I.Y. (M) SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 21-04-18 | 21-04-18 | True | True | - |
| total | RM 48.90 | 48.90 | False | True | GT norm=48.90, Pred norm=48.90 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 12: sroie_test_X51006913032

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006913032.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 10 MAY 2018 | 10 May 2018 18:19 | False | True | - |
| total | $12.20 | 12.20 | False | True | GT norm=12.20, Pred norm=12.20 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 13: sroie_test_X51005230616

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51005230616.jpg`
- Error types: `vendor_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | GERBANG ALAF RESTAURANTS SDN BHD | Gerbang Alaf Restaurants Sdn Bhd (65351-M) formerly known as Golden Arches Restaurants Sdn Bhd Licensee of McDonald's | False | False | score=0.4354, match=False |
| invoice_date | 18/01/2018 | 18/01/2018 | True | True | - |
| total | 38.90 | 38.90 | True | True | GT norm=38.90, Pred norm=38.90 |

## Case 14: sroie_test_X51007846310

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007846310.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | MOONLIGHT CAKE HOUSE SDN BHD | MOONLIGHT CAKE HOUSE SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 11/06/2018 | 11/06/2018 | True | True | - |
| total | RM28.20 | 28.20 | False | True | GT norm=28.20, Pred norm=28.20 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 15: sroie_test_X51007846268

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007846268.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 02 JUN 2018 | 02 Jun 2018 18:23 | False | True | - |
| total | RM10.35 | 10.35 | False | True | GT norm=10.35, Pred norm=10.35 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 16: sroie_test_X51008042787

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51008042787.jpg`
- Error types: `vendor_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | VEG FISH FARM THAI RESTAURANT S/B | FISH FARM THAI RESTAURANT Veg Fish Farm Thai Restaurant S/B | False | False | score=0.74, match=False |
| invoice_date | 01/05/2018 | 01/05/2018 | True | True | - |
| total | 412.90 | 412.90 | True | True | GT norm=412.90, Pred norm=412.90 |

## Case 17: sroie_test_X51006647933

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006647933.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | RESTORAN HOETIM | RESTORAN HOETIM | True | True | score=1.0, match=True |
| invoice_date | 28/05/2018 | 28/05/2018 | True | True | - |
| total | RM83.00 | 83.00 | False | True | GT norm=83.00, Pred norm=83.00 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 18: sroie_test_X51005746207

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51005746207.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | SUPER SEVEN CASH & CARRY SDN BHD | SUPER SEVEN CASH & CARRY SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 21-03-2018 | 21-03-2018 | True | True | - |
| total | RM18.30 | 18.30 | False | True | GT norm=18.30, Pred norm=18.30 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 19: sroie_test_X51007846400

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007846400.jpg`
- Error types: `vendor_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | KOREAN DINE SDN BHD | NAM SAN SEOUL KOREAN BBQ | False | False | score=0.3721, match=False |
| invoice_date | 19/06/2018 | 19/06/2018 | True | True | - |
| total | 152.90 | 152.90 | True | True | GT norm=152.90, Pred norm=152.90 |

## Case 20: sroie_test_X51007846282

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007846282.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | MOONLIGHT CAKE HOUSE SDN BHD | MOONLIGHT CAKE HOUSE SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 02/06/2018 | 02/06/2018 | True | True | - |
| total | RM16.20 | 16.20 | False | True | GT norm=16.20, Pred norm=16.20 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 21: sroie_test_X51006913018

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006913018.jpg`
- Error types: `document_quality_issue`
- Agent decision: `need_human_review`
- Document quality issues: `text_overlap`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | AEON CO. (M) BHD | AEON CO. (M) BHD | True | True | score=1.0, match=True |
| invoice_date | 11/05/2018 | 11/05/2018 | True | True | - |
| total | 458.55 | 458.55 | True | True | GT norm=458.55, Pred norm=458.55 |

## Case 22: sroie_test_X51005675914

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51005675914.jpg`
- Error types: `date_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | BEYOND BROTHERS HARDWARE | BEYOND BROTHERS HARDWARE | True | True | score=1.0, match=True |
| invoice_date | 10/11/2017 | 10/1/2017 | False | False | - |
| total | 67.85 | 67.85 | True | True | GT norm=67.85, Pred norm=67.85 |

## Case 23: sroie_test_X51006619338

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006619338.jpg`
- Error types: `document_quality_issue`
- Agent decision: `need_human_review`
- Document quality issues: `faint text`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | 99 SPEED MART S/B | 99 SPEED MART S/B | True | True | score=1.0, match=True |
| invoice_date | 31-01-16 | 31-01-16 | True | True | - |
| total | 262.20 | 262.20 | True | True | GT norm=262.20, Pred norm=262.20 |

## Case 24: sroie_test_X51007846321

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007846321.jpg`
- Error types: `date_mismatch;document_quality_issue`
- Agent decision: `need_human_review`
- Document quality issues: `blurred text`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | CHEF HENRY RIBS HOUSE | CHEF HENRY RIBS HOUSE | True | True | score=1.0, match=True |
| invoice_date | 05/06/2018 | 05/06/2015 | False | False | - |
| total | 103.85 | 103.85 | True | True | GT norm=103.85, Pred norm=103.85 |

## Case 25: sroie_test_X51005433543

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51005433543.jpg`
- Error types: `total_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 13 MAR 2018 | 13 Mar 2018 | False | True | - |
| total | $8.20 | 5.20 | False | False | GT norm=8.20, Pred norm=5.20 |

## Case 26: sroie_test_X51007231341

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007231341.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 03 MAY 2018 | 03 May 2018 18:27 | False | True | - |
| total | $8.20 | 8.20 | False | True | GT norm=8.20, Pred norm=8.20 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 27: sroie_test_X51006619784

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006619784.jpg`
- Error types: `vendor_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | SECURITY & OA TRADING | BIZ LINK SECURITY & OA TRADING | False | False | score=0.8085, match=False |
| invoice_date | 7/6/2016 | 7/6/2016 | True | True | - |
| total | 399.00 | 399.00 | True | True | GT norm=399.00, Pred norm=399.00 |

## Case 28: sroie_test_X51007846288

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51007846288.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 06 JUN 2018 | 06 Jun 2018 | False | True | - |
| total | RM7.25 | 7.25 | False | True | GT norm=7.25, Pred norm=7.25 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 29: sroie_test_X51005442375

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51005442375.jpg`
- Error types: `date_mismatch;total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 25 MAR 2018 | 29 Mar 2018 | False | False | - |
| total | $8.50 | 8.50 | False | True | GT norm=8.50, Pred norm=8.50 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 30: sroie_test_X51006414715

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006414715.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | SECRET RECIPE RESTAURANT | SECRET RECIPE RESTAURANT | True | True | score=1.0, match=True |
| invoice_date | 4/22/2018 | 4/22/2018 | True | True | - |
| total | RM41.81 | 41.81 | False | True | GT norm=41.81, Pred norm=41.81 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

## Case 31: sroie_test_X51006414593

- Image: `/work/bigweather/xinyanxie/invoiceguard-ai/data/raw/sroie/SROIE2019/test/img/X51006414593.jpg`
- Error types: `total_format_only_mismatch`
- Agent decision: `approve`
- Parse success: `True`

| Field | Ground Truth | Prediction | Exact | Normalized | Fuzzy / Notes |
|---|---|---|---:|---:|---:|
| vendor_name | UNIHAKKA INTERNATIONAL SDN BHD | UNIHAKKA INTERNATIONAL SDN BHD | True | True | score=1.0, match=True |
| invoice_date | 14 APR 2018 | 14 Apr 2018 | False | True | - |
| total | $8.90 | 8.90 | False | True | GT norm=8.90, Pred norm=8.90 |

Note: total is numerically correct after normalization, but raw prediction has formatting/currency differences.

