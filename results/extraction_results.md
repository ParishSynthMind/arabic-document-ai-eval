## Accuracy by method (all documents)

Review columns: base = ai-document-extractor's checks; +checks = with the Arabic checks added (totals add up, uncertain IDs from images, amounts reviewed together).

| Method | Fields | Exact match | Normalised match | Sent to review (base) | Wrong, not flagged (base) | Sent to review (+checks) | Wrong, not flagged (+checks) | Avg cost per doc |
|---|---|---|---|---|---|---|---|---|
| pdf-raw | 116 | 98% | **99%** | 31 | 0 | 31 | **0** | $0.017 |
| pdf-fixed | 116 | 91% | **91%** | 3 | 9 | 3 | **9** | $0.012 |
| ocr-eng | 116 | 34% | **34%** | 58 | 21 | 67 | **14** | $0.011 |
| ocr-ara | 116 | 60% | **60%** | 45 | 6 | 52 | **4** | $0.012 |
| ocr-prep | 116 | 58% | **58%** | 51 | 4 | 52 | **4** | $0.012 |
| vision | 116 | 93% | **94%** | 1 | 6 | 14 | **0** | $0.019 |

## Normalised accuracy per document

| Document | Variant | pdf-raw | pdf-fixed | ocr-eng | ocr-ara | ocr-prep | vision |
|---|---|---|---|---|---|---|---|
| inv01_ar_western | Arabic only, Western digits, clean print | 9/9 | 8/9 | 6/9 | 8/9 | 9/9 | 9/9 |
| inv02_ar_indic | Arabic only, Arabic-Indic digits everywhere | 9/9 | 8/9 | 0/9 | 3/9 | 3/9 | 9/9 |
| inv03_bi_western | Bilingual Arabic/English labels, Western digits | 9/9 | 9/9 | 7/9 | 8/9 | 8/9 | 9/9 |
| inv04_bi_indic_monthname | Bilingual, Arabic-Indic digits, date written with an Arabic month name | 9/9 | 8/9 | 0/9 | 2/9 | 3/9 | 8/9 |
| inv05_ar_indic_separators | Arabic-Indic digits with Arabic thousands (٬) and decimal (٫) separators | 9/9 | 9/9 | 0/9 | 3/9 | 3/9 | 6/9 |
| inv06_ar_scanned | Arabic only, Western digits, scanned (tilted, blurred, speckled) | 9/9 | 9/9 | 6/9 | 8/9 | 6/9 | 9/9 |
| inv07_bi_indic_scanned | Bilingual, Arabic-Indic digits, scanned | 9/9 | 9/9 | 1/9 | 3/9 | 3/9 | 8/9 |
| inv08_ar_hijri | Hijri and Gregorian dates both printed; Saudi invoice, SAR, 15% VAT | 8/9 | 7/9 | 0/9 | 3/9 | 3/9 | 8/9 |
| inv09_ar_lowres | Small 9pt type rendered at low resolution (110 dpi) | 9/9 | 7/9 | 6/9 | 9/9 | 7/9 | 9/9 |
| inv10_ar_tashkeel_usd | Supplier name printed with vowel marks (tashkeel); priced in US dollars | 9/9 | 8/9 | 7/9 | 8/9 | 7/9 | 9/9 |
| rcp01_ar_western | Narrow till receipt, Arabic, Western digits, card payment | 6/6 | 6/6 | 2/6 | 4/6 | 6/6 | 6/6 |
| rcp02_ar_indic_scanned | Till receipt, Arabic-Indic digits, cash, faded scan | 6/6 | 6/6 | 0/6 | 2/6 | 2/6 | 6/6 |
| lic01_bi_western | Trade-licence style page, bilingual, Western digits | 7/7 | 7/7 | 4/7 | 7/7 | 7/7 | 7/7 |
| lic02_bi_indic_scanned | Trade-licence style page, Arabic-Indic digits, scanned | 7/7 | 5/7 | 1/7 | 2/7 | 0/7 | 6/7 |

## Normalised accuracy per field

| Field | pdf-raw | pdf-fixed | ocr-eng | ocr-ara | ocr-prep | vision |
|---|---|---|---|---|---|---|
| supplier_name | 100% | 70% | 0% | 80% | 80% | 100% |
| supplier_trn | 100% | 100% | 50% | 50% | 50% | 100% |
| invoice_number | 90% | 90% | 50% | 50% | 40% | 70% |
| invoice_date | 100% | 100% | 50% | 40% | 50% | 100% |
| customer_name | 100% | 60% | 30% | 80% | 100% | 100% |
| currency | 100% | 100% | 0% | 100% | 100% | 100% |
| subtotal | 100% | 100% | 50% | 50% | 30% | 90% |
| vat_amount | 100% | 100% | 42% | 42% | 42% | 92% |
| total_amount | 100% | 100% | 50% | 50% | 33% | 92% |
| merchant_name | 100% | 100% | 0% | 50% | 100% | 100% |
| receipt_number | 100% | 100% | 0% | 50% | 50% | 100% |
| receipt_date | 100% | 100% | 50% | 50% | 50% | 100% |
| payment_method | 100% | 100% | 0% | 100% | 100% | 100% |
| licence_number | 100% | 100% | 50% | 50% | 50% | 50% |
| trade_name_ar | 100% | 50% | 0% | 50% | 50% | 100% |
| trade_name_en | 100% | 100% | 100% | 100% | 50% | 100% |
| legal_form | 100% | 100% | 0% | 50% | 50% | 100% |
| main_activity | 100% | 50% | 0% | 100% | 50% | 100% |
| issue_date | 100% | 100% | 50% | 50% | 50% | 100% |
| expiry_date | 100% | 100% | 50% | 50% | 50% | 100% |
