# WWW’26: карта основного proceedings и ориентиры для подачи на WWW’27

## Короткий вывод

В корпусе **936 материалов**: 676 full papers десяти research-треков, 57 industry papers, 122 short papers, 77 Web4Good papers и 4 keynote papers. Главный сигнал WWW’26 — не просто массовое присутствие LLM, а переход к веб-системам, где генеративные модели соединяются с поиском, персонализацией, графами, мультимодальными данными и проверяемыми ограничениями безопасности/ответственности.

Для основной секции WWW’27 наиболее убедительна работа, которая формулирует именно веб-задачу, а не только применяет новую модель: показывает реалистичный масштаб или поведение пользователей, сравнивается с сильными свежими baseline, содержит ablation/error analysis и даёт воспроизводимый артефакт.

## Корпус и методика

Проверено PDF: **936/936**; автоматически выделен abstract: **935/936** (99,9%). Тематические метки рассчитаны по названиям и abstract как multi-label категории, поэтому суммы по темам не обязаны совпадать с числом статей. Для 10 записей второй части proceedings в метаданных найдена ссылка на код.

Это обзор ландшафта, а не замена экспертному чтению: автоматический подсчёт помогает увидеть плотность направлений, но не оценивает корректность экспериментов и силу novelty отдельной статьи.

## Состав proceedings

| Раздел | Материалов | Доля корпуса |
| --- | ---: | ---: |
| Keynotes | 4 | 0,4% |
| Track 1 · Economics, Online Markets and Human Computation | 28 | 3,0% |
| Track 2 · Graph Algorithms and Modeling for the Web | 102 | 10,9% |
| Track 3 · Responsible Web | 27 | 2,9% |
| Track 4 · Search and Retrieval-Augmented AI | 61 | 6,5% |
| Track 5 · Security and Privacy | 85 | 9,1% |
| Track 6 · Semantics and Knowledge | 83 | 8,9% |
| Track 7 · Social Networks and Social Media | 42 | 4,5% |
| Track 8 · Systems and Infrastructure for Web, Mobile, and Web of Things | 72 | 7,7% |
| Track 9 · User Modeling, Personalization and Recommendation | 110 | 11,8% |
| Track 10 · Web Mining and Content Analysis | 66 | 7,1% |
| Industry Track | 57 | 6,1% |
| Short Papers | 122 | 13,0% |
| Web4Good | 77 | 8,2% |

## Сквозные темы

| Тема | Статей | Доля корпуса | Где особенно заметна |
| --- | ---: | ---: | --- |
| LLM, агенты и генеративный ИИ | 424 | 45,3% | Track 6 · Semantics and Knowledge (55); Short Papers (52) |
| Responsible AI, fairness и объяснимость | 422 | 45,1% | Short Papers (55); Track 9 · User Modeling, Personalization and Recommendation (51) |
| Системы, эффективность и edge/cloud | 378 | 40,4% | Track 8 · Systems and Infrastructure for Web, Mobile, and Web of Things (53); Short Papers (45) |
| Графы и knowledge graphs | 280 | 29,9% | Track 2 · Graph Algorithms and Modeling for the Web (93); Track 6 · Semantics and Knowledge (42) |
| Поиск, RAG и ответы на вопросы | 264 | 28,2% | Track 4 · Search and Retrieval-Augmented AI (57); Short Papers (49) |
| Рекомендательные системы и персонализация | 221 | 23,6% | Track 9 · User Modeling, Personalization and Recommendation (107); Short Papers (28) |
| Безопасность, приватность и атаки | 211 | 22,5% | Track 5 · Security and Privacy (76); Web4Good (27) |
| Социальные сети и поведение пользователей | 186 | 19,9% | Track 7 · Social Networks and Social Media (28); Web4Good (24) |
| Мультимодальность и vision-language | 177 | 18,9% | Short Papers (26); Track 10 · Web Mining and Content Analysis (21) |
| Временные ряды, события и прогнозирование | 156 | 16,7% | Track 10 · Web Mining and Content Analysis (24); Track 2 · Graph Algorithms and Modeling for the Web (21) |
| Web4Good, здоровье и устойчивость | 90 | 9,6% | Web4Good (36); Short Papers (15) |
| Дезинформация и целостность контента | 48 | 5,1% | Short Papers (10); Web4Good (9) |

### Что стоит за числами

**LLM, агенты и генеративный ИИ — 424 работ.** LLM становятся компонентом pipeline: маршрутизатором, планировщиком, симулятором пользователя, средством разметки или рассуждения. Конкурировать одним prompting всё труднее; важны измеримый системный выигрыш, стоимость и устойчивость.

**Поиск, RAG и ответы на вопросы — 264 работ.** RAG рассматривается как система принятия решений: когда искать, что извлекать, как переписывать запрос и как проверять ответ. Сильная постановка должна отдельно оценивать retrieval и generation, включая latency и стоимость.

**Рекомендательные системы и персонализация — 221 работ.** Центр тяжести смещён к генеративным и conversational recommenders, long-term memory, cold-start и multi-behavior сценариям. Нужны реалистичные split, защита от leakage и метрики помимо offline relevance.

**Responsible AI, fairness и объяснимость — 422 работ.** Ответственность всё чаще встроена в алгоритм и evaluation, а не оставлена отдельным разделом. Для подачи полезны group-wise результаты, failure modes и явное описание затрагиваемых пользователей.

**Безопасность, приватность и атаки — 211 работ.** Работы оценивают не только точность защиты, но и адаптивного противника, transferability и эксплуатационную цену. Threat model должен быть сформулирован до экспериментов.

**Мультимодальность и vision-language — 177 работ.** Мультимодальность используется для веб-контента, misinformation, recommendation и knowledge extraction. Простого fusion недостаточно: ценятся missing-modality tests, cross-domain robustness и анализ вклада каждой модальности.

**Системы, эффективность и edge/cloud — 378 работ.** Эффективность становится частью научного вклада: routing, caching, serving, федеративные и edge-сценарии. Следует измерять wall-clock latency, память, throughput и стоимость, а не только FLOPs.

## Репрезентативные работы по крупнейшим направлениям

### LLM, агенты и генеративный ИИ

- [From Prediction to Understanding: Leveraging Reasoning in Large Language Model-based Recommendations](https://doi.org/10.1145/3774904.3792283) — Track 9 · User Modeling, Personalization and Recommendation
- [Acting Flatterers via LLMs Sycophancy: Combating Clickbait with LLMs Opposing-Stance Reasoning](https://doi.org/10.1145/3774904.3792506) — Track 5 · Security and Privacy
- [Beyond Single-Granularity Prompts: A Multi-Scale Chain-of-Thought Prompt Learning for Graph](https://doi.org/10.1145/3774904.3792115) — Track 2 · Graph Algorithms and Modeling for the Web
- [Incentivizing Agentic Reasoning Capability with Outcome Supervision for Knowledge Base Question Answering](https://doi.org/10.1145/3774904.3792662) — Track 6 · Semantics and Knowledge

### Responsible AI, fairness и объяснимость

- [BiasEdit: A Training-Free Bias-Detect-and-Edit Framework for Learning Fair Visual Classifiers](https://doi.org/10.1145/3774904.3792411) — Track 3 · Responsible Web
- [FairGU: Fairness-aware Graph Unlearning in Social Networks](https://doi.org/10.1145/3774904.3793004) — Web4Good
- [FairFS: Addressing Deep Feature Selection Biases for Recommender System](https://doi.org/10.1145/3774904.3792167) — Track 9 · User Modeling, Personalization and Recommendation
- [FairGE: Fairness-Aware Graph Encoding in Incomplete Social Networks](https://doi.org/10.1145/3774904.3792169) — Track 7 · Social Networks and Social Media

### Системы, эффективность и edge/cloud

- [Task-Aware Cloud-End Offloading for Vision-Language Model Serving via Dynamic Modality-Specific Adapter Scheduling](https://doi.org/10.1145/3774904.3792127) — Track 8 · Systems and Infrastructure for Web, Mobile, and Web of Things
- [Privacy-Friendly Adaptation of Vision Transformers for Communication and Latency-Efficient Private Inference](https://doi.org/10.1145/3774904.3792211) — Track 5 · Security and Privacy
- [E 2SGNN: Reconciling Expression and Efficiency in Spiking Graph Neural Network](https://doi.org/10.1145/3774904.3792271) — Track 2 · Graph Algorithms and Modeling for the Web
- [BeeQoS: A Cloud-Native QoS System for Adaptive and Scalable Multi-Priority Bandwidth Guarantees](https://doi.org/10.1145/3774904.3792487) — Track 8 · Systems and Infrastructure for Web, Mobile, and Web of Things

### Графы и knowledge graphs

- [GraphCogent: Mitigating LLMs’ Working Memory Constraints via Multi-Agent Collaboration in Complex Graph Understanding](https://doi.org/10.1145/3774904.3792314) — Track 6 · Semantics and Knowledge
- [Toward Graph-Tokenizing Large Language Models with Reconstructive Graph Instruction Tuning](https://doi.org/10.1145/3774904.3792077) — Track 2 · Graph Algorithms and Modeling for the Web
- [Graph Discrete Prompt Optimization for Knowledge Graph Question Answering](https://doi.org/10.1145/3774904.3792857) — Short Papers
- [Heterophily-Agnostic Hypergraph Neural Networks with Riemannian Local Exchanger](https://doi.org/10.1145/3774904.3792435) — Track 2 · Graph Algorithms and Modeling for the Web

### Поиск, RAG и ответы на вопросы

- [Rethinking the Hidden Risk of Reranking: Achieving Risk-aware Reranking with Information Gain for RAG with LLMs](https://doi.org/10.1145/3774904.3792085) — Track 4 · Search and Retrieval-Augmented AI
- [Let It Try First: Uncertainty-Guided Retrieval Switching for Retrieval-Augmented Question Answering](https://doi.org/10.1145/3774904.3792870) — Short Papers
- [MixRAG : Mixture-of-Experts Retrieval-Augmented Generation for Textual Graph Understanding and Question Answering](https://doi.org/10.1145/3774904.3792680) — Track 6 · Semantics and Knowledge
- [S-Path-RAG: Semantic-Aware Shortest-Path Retrieval Augmented Generation for Multi-Hop Knowledge Graph Question Answering](https://doi.org/10.1145/3774904.3792459) — Track 6 · Semantics and Knowledge

### Рекомендательные системы и персонализация

- [Think Then Recommend: An LLM-Powered Multi-Agent Framework for Personalized Conversational Recommender System in E-Commerce](https://doi.org/10.1145/3774904.3793050) — Web4Good
- [Multi-Agent Collaborative Filtering: Orchestrating Users and Items for Agentic Recommendations](https://doi.org/10.1145/3774904.3792931) — Short Papers
- [AliBoostV2: CTR-Growth Balanced Boosting Framework in Billion-Scale Recommendation Platform](https://doi.org/10.1145/3774904.3792800) — Industry Track
- [Not All Information Brings Benefits: Personalization-Driven Agent Debate for Conversational Recommendation](https://doi.org/10.1145/3774904.3792152) — Track 9 · User Modeling, Personalization and Recommendation

### Безопасность, приватность и атаки

- [Fast or Secure? Push the Limit of Privacy Leakage Threat via Charging Side-Channel Attacks](https://doi.org/10.1145/3774904.3792629) — Track 5 · Security and Privacy
- [Unveiling the Underground Phishing Ecosystem: A 12-Year Longitudinal Study of Deep and Dark Web Forums](https://doi.org/10.1145/3774904.3792737) — Track 6 · Semantics and Knowledge
- [SEP-Attack: A Simple and Effective Paradigm for Transfer-Based Textual Adversarial Attack](https://doi.org/10.1145/3774904.3793042) — Web4Good
- [GIANT: Structure-Agnostic Practical Adversarial Attacks for Graph-based Network Intrusion Detection Systems](https://doi.org/10.1145/3774904.3792601) — Track 5 · Security and Privacy

### Социальные сети и поведение пользователей

- [How Social Media Peer Comments Influence Privacy Decisions in Photo Sharing: Context and Individual Differences Cause Comments to Backfire](https://doi.org/10.1145/3774904.3792468) — Track 7 · Social Networks and Social Media
- [Improving the Accuracy of Community Detection on Signed Networks via Community Refinement and Contrastive Learning](https://doi.org/10.1145/3774904.3792859) — Short Papers
- [SLFM: Semi-Supervised Local Community Detection Based on Hyperbolic Flow Matching](https://doi.org/10.1145/3774904.3792548) — Track 2 · Graph Algorithms and Modeling for the Web
- [Community Fact-Checks Do Not Break Follower Loyalty](https://doi.org/10.1145/3774904.3792984) — Web4Good

## Возможности для WWW’27

Ниже — не прогноз тем CFP, а области, где по карте WWW’26 виден хороший баланс актуальности и пространства для нового вклада.

1. **Agentic Web с проверяемым поведением.** Агент, работающий с реальным веб-интерфейсом или несколькими источниками, плюс benchmark длинных сценариев, recovery после ошибок и оценка безопасности.
2. **RAG как адаптивная веб-система.** Совместное решение «искать или отвечать», выбор источника/инструмента и budget-aware routing; отдельно измерять factuality, retrieval recall, latency и денежную стоимость.
3. **Персонализация с долговременной памятью и контролем пользователя.** Не только рост relevance, но editable/forgettable memory, privacy, drift и долгосрочные эффекты.
4. **Надёжность мультимодального веб-контента.** Детектирование и объяснение манипуляций при неполных модальностях, domain shift и мультиязычности; human study существенно усилит вклад.
5. **Web-scale эффективность LLM.** Маршрутизация между моделями, caching и early exit с Pareto-анализом качество–latency–cost и нагрузочным экспериментом.
6. **Графы + LLM без декоративного объединения.** Задача, где структура графа даёт причинно понятный выигрыш; обязательны structure-free baseline, ablation и тест на перенос.
7. **Responsible recommendation/search.** Оптимизация полезности вместе с exposure fairness, safety или well-being, с анализом компромиссов, а не одной агрегированной метрикой.
8. **Мультиязычный и low-resource Web.** Индексация, retrieval, модерация или knowledge extraction для языков длинного хвоста с честной оценкой coverage и участием носителей языка.

## Как превратить проект из demo/workshop в main-track paper

| Слой | Что должно быть в основной подаче |
| --- | --- |
| Исследовательский вопрос | Проверяемая гипотеза и ясное отличие от системы-демонстратора |
| Novelty | Новый метод, постановка, данные или эмпирическое открытие; точное позиционирование относительно ближайших работ WWW’26 |
| Baselines | Сильные методы 2025–2026, простой baseline и компонентные ablation |
| Evaluation | Несколько datasets/доменов, доверительные интервалы или тесты значимости, error analysis |
| Web relevance | Пользователи, веб-данные, веб-масштаб или сетевые взаимодействия должны быть центральными, а не фоном |
| Systems evidence | Latency, throughput, память и стоимость — если заявляется практичность или масштабируемость |
| Human dimension | User study или экспертная оценка, если качество нельзя надёжно свести к автоматическим метрикам |
| Reproducibility | Код, конфигурации, seeds, лицензии данных и воспроизводимый pipeline |
| Responsible research | Threats to validity, ethics, privacy, intended use и потенциальный вред |

## Практический план подготовки

1. Выбрать 15–25 ближайших работ из репрезентативных списков и таблицы корпуса, затем вручную заполнить матрицу: задача, данные, baseline, метрики, ограничение.
2. Одним предложением сформулировать разрыв: что эти работы принципиально не измеряют или не умеют делать.
3. До разработки зафиксировать evaluation protocol и минимальный набор ablation, чтобы вклад не зависел от одной удачной метрики.
4. Сначала получить сильный результат на публичном benchmark, затем добавить собственный реалистичный веб-сценарий или production-like нагрузку.
5. Подготовить anonymized repository и artifact checklist одновременно с экспериментами, а не перед дедлайном.

## Воспроизводимость отчёта

```powershell
python tools/build_main_program_analysis.py --refresh
```

Машиночитаемый корпус с abstract находится в `reports/www26-main-program-corpus.tsv`. Его удобно фильтровать по треку, DOI и ключевым словам для следующего этапа ручного literature review.
