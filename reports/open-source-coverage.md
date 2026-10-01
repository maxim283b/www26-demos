# Open-source coverage for the missing WWW'26 volume part

Проверено 432 работы, перечисленные в оглавлении `3774904.pdf`, но отсутствующие среди физических
страниц переданной части сборника. Для каждой работы сохранён официальный DOI. Открытые версии
искались по DOI через Semantic Scholar и OpenAlex, затем все записи проверялись по точному названию
в arXiv; оставшиеся пробелы дополнительно искались в институциональных репозиториях, на сайтах
авторов и в GitHub. После этого оставшиеся работы загружены через официальный ACM eReader со
страниц, помеченных `FREE ACCESS` и CC BY 4.0. Каждый файл локально прошёл проверку PDF-сигнатуры
и числа страниц.

| Раздел | Работ | Найдено | Загружено | GitHub |
| --- | ---: | ---: | ---: | ---: |
| Track 9: User Modeling, Personalization and Recommendation | 110 | 110 | 110 | 6 |
| Track 10: Web Mining and Content Analysis | 66 | 66 | 66 | 1 |
| Industry Track | 57 | 57 | 57 | 0 |
| Short Papers | 122 | 122 | 122 | 3 |
| Web4Good | 77 | 77 | 77 | 0 |
| **Всего** | **432** | **432** | **432** | **10** |

Полные результаты находятся в `index.tsv` каждого раздела: `open_url` указывает на препринт или
репозиторий, `code_url` — на проверенный код, а `doi_url` всегда содержит каноническую страницу
ACM. Результаты загрузки записаны в `reports/download-manifest.tsv`; состав
единого PDF — в `reports/collection-manifest.md`.

## Проверенные первые работы трека 9

| Работа | Открытая статья | Код |
| --- | --- | --- |
| ThinkRec | [arXiv 2505.15091](https://arxiv.org/abs/2505.15091) | [Yu-Qi-hang/ThinkRec](https://github.com/Yu-Qi-hang/ThinkRec) |
| Adaptive Graph Reweighting for Collaborative Filtering | пока только [DOI](https://doi.org/10.1145/3774904.3792081) | — |
| Quantum-enhanced Representation Learning and Matching Learning for Recommendation | [University of Milan PDF](https://air.unimi.it/bitstream/2434/1255279/2/Proc_WWW2026_quantumAnchen.pdf) | — |
| SEAR | пока только репозиторий | [guanwei49/SEAR](https://github.com/guanwei49/SEAR) |
| Guiding Generative Recommender Systems with Structured Human Priors | [arXiv 2511.10492](https://arxiv.org/abs/2511.10492) | — |
| Iterative Semantic Reasoning from Individual to Group Interests | [arXiv 2603.13934](https://arxiv.org/abs/2603.13934) | [htired/ISRF](https://github.com/htired/ISRF) |
| Generative Data Transformation: From Mixed to Unified Data | [arXiv 2602.22743](https://arxiv.org/abs/2602.22743) | [USTC-StarTeam/Taesar](https://github.com/USTC-StarTeam/Taesar) |
| From Entity Reliability to Clean Feedback | [arXiv 2508.10851](https://arxiv.org/abs/2508.10851) | — |

Состояние ссылок зафиксировано 1 октября 2026 года. Ссылки на агрегаторы без полного текста и
страницы ResearchGate с кнопкой `Request full-text` не считаются открытыми копиями.
