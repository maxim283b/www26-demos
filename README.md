# WWW'26 Proceedings Analysis

Структурированный корпус и анализ материалов The Web Conference 2026 для подготовки подачи на WWW'27.

## Корпус

| Раздел | Состояние |
| --- | --- |
| [Demo Track](tracks/demos/README.md) | 40 PDF, 40 Marker Markdown |
| [Keynotes](tracks/keynotes/README.md) | 4 PDF |
| [Research Track](tracks/research/README.md) | 676 PDF: все 10 исследовательских треков; Marker Markdown для треков 9–10 |
| [Industry Track](tracks/industry/README.md) | 57 PDF и Marker Markdown |
| [Short Papers](tracks/short-papers/README.md) | 122 PDF и Marker Markdown |
| [Web4Good](tracks/web4good/README.md) | 77 PDF и Marker Markdown |

Исходный файл `3774904.pdf` не хранится в Git: это монолитный том размером около 1,4 ГБ. Скрипт
[`tools/split_main_proceedings.py`](tools/split_main_proceedings.py) воспроизводимо делит его по
встроенным DOI-закладкам и формирует `index.tsv` для каждого трека.

## Research Track 2026

Полный корпус содержит **936 материалов основного proceedings**: 4 keynote papers, 676 статей
десяти research-треков, 57 Industry, 122 Short Papers и 77 Web4Good. Ещё 40 Demo papers хранятся
отдельно. Исходный том дал 504 материала; для отсутствовавших 432 работ сформированы `index.tsv`,
найдены 218 проверенных открытых авторских копий, а остальные 214 статей получены из официального
ACM eReader со страниц, помеченных `FREE ACCESS` и CC BY 4.0. Эти 432 PDF (4 157 страниц)
преобразованы Marker в отдельные Markdown-директории.

Главный результат анализа —
[`reports/www26-main-program-analysis.md`](reports/www26-main-program-analysis.md): карта тем всего
proceedings и практические ориентиры для main-track подачи на WWW’27. Машиночитаемые abstracts и
метаданные 936 материалов находятся в
[`reports/www26-main-program-corpus.tsv`](reports/www26-main-program-corpus.tsv). Сборка второй
части отдельно описана в [`reports/collection-manifest.md`](reports/collection-manifest.md).

1. [Economics, Online Markets and Human Computation](tracks/research/economics-online-markets-human-computation/)
2. [Graph Algorithms and Modeling for the Web](tracks/research/graph-algorithms-modeling/)
3. [Responsible Web](tracks/research/responsible-web/)
4. [Search and Retrieval-Augmented AI](tracks/research/search-retrieval-augmented-ai/)
5. [Security and Privacy](tracks/research/security-privacy/)
6. [Semantics and Knowledge](tracks/research/semantics-knowledge/)
7. [Social Networks and Social Media](tracks/research/social-networks-social-media/)
8. [Systems and Infrastructure for Web, Mobile, and Web of Things](tracks/research/systems-infrastructure-web-mobile-iot/)
9. [User Modeling, Personalization and Recommendation](tracks/research/user-modeling-personalization-recommendation/)
10. [Web Mining and Content Analysis](tracks/research/web-mining-content-analysis/)

## Воспроизведение

```powershell
python tools/split_main_proceedings.py C:\path\to\3774904.pdf
python tools/build_missing_catalog.py C:\path\to\3774904.pdf
python tools/enrich_open_sources.py
python tools/enrich_openalex.py
python tools/discover_arxiv_by_title.py
python tools/add_code_links.py
python tools/download_open_papers.py --retry-failed
python tools/import_acm_downloads.py
python tools/build_open_papers_collection.py
python tools/build_main_program_analysis.py --refresh
python etl.py --input tracks/research/responsible-web/pdf --output tracks/research/responsible-web/md --no-ocr --mode fast
```

Для записей без открытой копии `doi_url` остаётся канонической ссылкой на публикацию ACM.
