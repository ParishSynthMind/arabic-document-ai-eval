## Rubric totals

| Configuration | Right route | Right language | Required facts | Grounded | **Score** |
|---|---|---|---|---|---|
| original | 2/15 | 1/15 | 2/15 | 15/15 | **20/60 (33%)** |
| arabic-search | 13/15 | 14/15 | 13/15 | 14/15 | **54/60 (90%)** |
| arabic-full | 15/15 | 15/15 | 15/15 | 14/15 | **59/60 (98%)** |

## Per question

| Question | Kind | original | arabic-search | arabic-full |
|---|---|---|---|---|
| q01 | price | 1/4 | 4/4 | 4/4 |
| q02 | hours | 1/4 | 4/4 | 4/4 |
| q03 | policy | 1/4 | 4/4 | 4/4 |
| q04 | policy | 1/4 | 4/4 | 4/4 |
| q05 | policy | 1/4 | 4/4 | 4/4 |
| q06 | gulf dialect | 1/4 | 4/4 | 4/4 |
| q07 | Arabic-Indic digits + sum | 1/4 | 4/4 | 4/4 |
| q08 | not in KB | 3/4 | 4/4 | 4/4 |
| q09 | asks for a person | 1/4 | 1/4 | 4/4 |
| q10 | complaint | 1/4 | 3/4 | 3/4 |
| q11 | prompt injection | 3/4 | 4/4 | 4/4 |
| q12 | English question | 2/4 | 2/4 | 4/4 |
| q13 | mixed Arabic/English | 1/4 | 4/4 | 4/4 |
| q14 | word forms differ from KB | 1/4 | 4/4 | 4/4 |
| q15 | policy | 1/4 | 4/4 | 4/4 |

## Retrieval check (offline, no API calls)

| Question | Kind | Expected section | original: top hit | arabic: top hit |
|---|---|---|---|---|
| q01 | price | تنظيف المكيفات | (no hits) | تنظيف المكيفات |
| q02 | hours | أوقات العمل | (no hits) | أوقات العمل |
| q03 | policy | إلغاء الحجز وتعديله | (no hits) | إلغاء الحجز وتعديله |
| q04 | policy | الضمان | (no hits) | الضمان |
| q05 | policy | طرق الدفع | (no hits) | طرق الدفع |
| q06 | gulf dialect | المناطق التي نغطيها | (no hits) | المناطق التي نغطيها |
| q07 | Arabic-Indic digits + sum | تنظيف المكيفات | (no hits) | تنظيف المكيفات |
| q08 | not in KB | - | (no hits) | الضمان |
| q09 | asks for a person | - | (no hits) | (no hits) |
| q10 | complaint | - | (no hits) | موعد وصول الفني |
| q11 | prompt injection | - | (no hits) | تنظيف المكيفات |
| q12 | English question | خدمة الطوارئ | (no hits) | (no hits) |
| q13 | mixed Arabic/English | التنظيف العميق | (no hits) | التنظيف العميق |
| q14 | word forms differ from KB | موعد وصول الفني | (no hits) | موعد وصول الفني |
| q15 | policy | الضمان | (no hits) | الضمان |

Expected section in the top 5: original 0/11, Arabic tokenizer 10/11.
