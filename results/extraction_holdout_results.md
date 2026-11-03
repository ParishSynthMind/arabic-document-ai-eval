## Accuracy by method (all documents)

Review columns: base = ai-document-extractor's checks; +checks = with the Arabic checks added (totals add up, uncertain IDs from images, amounts reviewed together).

| Method | Fields | Exact match | Normalised match | Sent to review (base) | Wrong, not flagged (base) | Sent to review (+checks) | Wrong, not flagged (+checks) | Avg cost per doc |
|---|---|---|---|---|---|---|---|---|
| pdf-raw | 34 | 97% | **97%** | 11 | 1 | 11 | **1** | $0.017 |
| vision | 34 | 82% | **82%** | 6 | 0 | 10 | **0** | $0.026 |

## Normalised accuracy per document

| Document | Variant | pdf-raw | vision |
|---|---|---|---|
| hold01_ar_indic_sep_scanned | HOLDOUT. Arabic-Indic separators, scanned, five-figure amounts | 9/9 | 4/9 |
| hold02_bi_indic_ids | HOLDOUT. Bilingual, Arabic-Indic digits, IDs with letters and slashes | 8/9 | 9/9 |
| hold03_ar_indic_sep_clean | HOLDOUT. Arabic-Indic separators, clean, six-figure total | 9/9 | 9/9 |
| hold04_lic_indic_scanned | HOLDOUT. Licence page, Arabic-Indic digits, scanned | 7/7 | 6/7 |

## Normalised accuracy per field

| Field | pdf-raw | vision |
|---|---|---|
| supplier_name | 67% | 100% |
| supplier_trn | 100% | 67% |
| invoice_number | 100% | 67% |
| invoice_date | 100% | 100% |
| customer_name | 100% | 100% |
| currency | 100% | 100% |
| subtotal | 100% | 67% |
| vat_amount | 100% | 67% |
| total_amount | 100% | 67% |
| licence_number | 100% | 0% |
| trade_name_ar | 100% | 100% |
| trade_name_en | 100% | 100% |
| legal_form | 100% | 100% |
| main_activity | 100% | 100% |
| issue_date | 100% | 100% |
| expiry_date | 100% | 100% |
