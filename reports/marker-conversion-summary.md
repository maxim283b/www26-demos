# Marker conversion summary

Все 432 статьи, отсутствовавшие в исходном монолитном proceedings, преобразованы в Markdown
локальным Marker pipeline (`--no-ocr --mode fast`). Для каждой статьи создана отдельная директория
с Markdown и извлечёнными изображениями; `manifest.jsonl` содержит название, DOI, размер результата
и статус проверки.

| Раздел | PDF | Markdown | Ошибки | С заголовком Abstract |
| --- | ---: | ---: | ---: | ---: |
| Research Track 9 · User Modeling, Personalization and Recommendation | 110 | 110 | 0 | 107 |
| Research Track 10 · Web Mining and Content Analysis | 66 | 66 | 0 | 65 |
| Industry Track | 57 | 57 | 0 | 56 |
| Short Papers | 122 | 122 | 0 | 117 |
| Web4Good | 77 | 77 | 0 | 74 |
| **Всего** | **432** | **432** | **0** | **419** |

Отсутствие отдельного Markdown-заголовка `Abstract` у 13 документов не означает пустой результат:
минимальный объём Markdown среди всех работ — 6 423 байта. Причина — нестандартная вёрстка первой
страницы или объединение abstract с соседним текстовым блоком. Выборочно проверены начало, середина
и конец каждого трека; заголовки, основной текст, формулы и ссылки присутствуют.

Повторная проверка без конвертации:

```powershell
python etl.py --input tracks/short-papers/pdf --output tracks/short-papers/md --no-ocr --mode fast
```
