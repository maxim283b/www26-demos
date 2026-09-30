#!/usr/bin/env python3
"""Generate the Russian corpus report from the reproducible TSV index."""

from __future__ import annotations

import csv
from pathlib import Path


SUMMARIES = {
    "des0065": "превращает неструктурированные документы в многомерное пространственно-временное хранилище; LLM-извлечение дополнено памятью документа, коррекцией геокодинга, валидацией и аналитическим dashboard, а на benchmark показан прирост F1 3,60–4,37 п.п.",
    "des0084": "демонстрирует jailbreak через пространственное распределение вредоносного текста в веб-интерфейсе (95% успешных атак на GPT-4) и добавляет постфильтр SpatialD; сильная сторона — одновременно новый класс атаки, воспроизводимый стенд и защита.",
    "des0206": "ищет паттерны в незнакомых неразмеченных данных через чередование широкого обзора кластеров и точечной проверки кандидатов; ценность — превращение предварительных LLM-категорий в проверяемую таксономию без ground truth.",
    "des0336": "моделирует распространение общественного мнения как каскад когнитивных убеждений и краткосрочных эмоций в LLM-мультиагентной симуляции; проверка на 15 реальных PR-кризисах делает demo убедительнее чисто синтетической симуляции.",
    "des0461": "объединяет RAG, MCP и цифрового человека в легкой веб-системе обучения с Q&A, аналитикой, виртуальным классом и контролем внимания; акцент сделан на доступной работе при слабом оборудовании и социальном эффекте.",
    "des0502": "задает агентам персоны и память через собственный markup, Engram-сеть ассоциативной памяти и протокольное обнаружение инструментов; пять месяцев эксплуатации в 15+ компаниях, 50K+ загрузок и 3K+ GitHub stars дают редкую для demo production-валидацию.",
    "des0759": "делает научную идеацию прозрачным четырехэтапным процессом — курирование знаний, генерация, отбор и экспертный синтез; пользователь видит логи и промежуточные состояния и может перенастраивать агентов, а идеи остаются привязанными к источникам.",
    "des0910": "симулирует peer review по тексту и рисункам статьи, заземляет замечания в корпусе OpenReview и преобразует их в трассируемый список правок; выигрыш — feedback встроен в процесс редактирования и сразу превращается в действия.",
    "des0916": "преобразует неточные текстовые пожелания в план здания: мультиагенты декомпозируют запрос, пользователь правит промежуточный 3D-макет, а ControlNet генерирует виды; интерактивность закрывает проблему неконтролируемых one-shot планировщиков.",
    "des0918": "комбинирует небольшой browser proof-of-work с визуальной задачей, удобной человеку, но трудной современным vision-моделям; два независимых барьера повышают цену массовой автоматизации без заметного ухудшения UX.",
    "des0920": "связывает обучаемую SEIR-модель со spatio-temporal GNN и автоматически строит недельные dengue-прогнозы для 37 районов и 752 деревень; веб-карта превращает более точный прогноз в инструмент раннего муниципального вмешательства.",
    "des0921": "прогнозирует длительность и нагрузку задач межевания по пространственным и табличным данным через GCN, attention, MLP и periodic encoding; наглядная карта и заявленное сокращение времени и труда до 88% связывают модель с рабочим процессом ведомства.",
    "des0925": "MLPlatAgent переводит естественное описание ML-задачи в code-free визуальный workflow с intent-планированием, иерархическим поиском инструментов и function calls; демонстрация двух сценариев и сравнение с агентными baseline показывают практическую выполнимость.",
    "des0940": "дает парное сравнение отчетов deep-research агентов и их промежуточных шагов, включая span-level замечания; эксперимент с 17 аннотаторами показывает, что тонкая человеческая разметка выявляет различия, которые теряются в статических benchmark.",
    "des0949": "автоматически генерирует и проверяет synthetic QA по приватным документам, обучает легкий visual retriever и итеративно связывает его с MLLM; доменная адаптация и снижение галлюцинаций достигаются без ручной разметки.",
    "des0950": "встраивает развлекательных и полезных агентов в многопользовательский групповой чат через Agent Builder, Dialogue Manager и plugins; 350 дней реального deployment и рост объема сообщений на 28,8% подтверждают жизнеспособность UX.",
    "des0951": "ищет подтверждающие научные ссылки прямо в LaTeX-редакторе, маршрутизирует запросы только в доверенные репозитории и валидирует поддержку на уровне абзаца; локальная обработка и отказ от LLM-генерации самих ссылок снижают риски приватности и hallucination.",
    "des0953": "расширяет PyKEEN для появления новых сущностей и отношений без полного переобучения, добавляет informed initialization и метрики забывания/усвоения; notebook, dashboard и поддержка любых unimodal KGE превращают метод в повторно используемый framework.",
    "des0958": "браузерное расширение превращает свежие travel-блоги в многодневный маршрут, а sliders дают контроль над историческими, природными, культурными и развлекательными предпочтениями; pipeline работает на живом Web-контенте и оставляет пользователя в цикле.",
    "des959": "встраивает мультиагентное рецензирование и редактирование прямо в Overleaf-подобный workflow через Chrome extension, Kubernetes orchestration и MCP tools; локальные patches, параллельные агенты и diff-based updates делают изменения контролируемыми.",
    "des960": "ведет пользователя по циклу detect–explain–adapt для data drift в диалоге и без привязки к конкретной модели; ценность demo — не только сигнал о сдвиге, но и персонализированное объяснение процесса для пользователя разного уровня.",
    "des965": "реализует явный metacognitive loop для ансамбля LLM: мониторинг неопределенности и конфликтов запускает управляющие действия; работа выделяется попыткой превратить абстрактную self-awareness схему в исполняемую систему.",
    "des968": "открывает ролевую платформу из 19 281 китайского исторического персонажа, объединяя разрозненные биографии, тексты, родственные связи и события; масштаб данных, open source и среднее улучшение role-playing метрик на 10,2% создают сильную демонстрационную историю.",
    "des974": "унифицирует юридические benchmark и LLM-backends в модульном toolkit с конфигурацией, web UI, ускорением и возобновляемыми прогонами; главное — воспроизводимость и расширяемость вместо еще одного закрытого legal benchmark.",
    "des978": "сочетает быстрый edge-screening аномалий, более точную cloud-проверку и LLM-агентов, которые объясняют диагноз и развивают дерево классов; web UI показывает полный путь от временного ряда к интерпретируемому maintenance-решению.",
    "des982": "оценивает качество peer review по структурным признакам, LLM-rubric и supervised prediction и открывает результат через UI и API; несколько измерений поддерживают self-assessment, triage редактора и массовый аудит.",
    "des987": "оценивает robustness модели причинными метриками fairness и stability, показывает компромисс с accuracy и принимает пользовательские данные; model-agnostic стенд с четырьмя доменами делает выбор модели проверяемым, а не декларативным.",
    "des994": "визуализирует скрытые сигналы поведения и alignment LLM, чтобы пользователь мог рефлексировать над situational awareness и conformity; цель — превратить пассивное потребление ответа в осознанное и калиброванное взаимодействие.",
    "des997": "в браузере связывает трафик SUMO и энергосеть PyPSA для Manhattan и дает запускать каскадные отключения, V2G-ответ и собственные сценарии; реальные городские данные и hands-on управление делают сложную co-simulation доступной без специального ПО.",
    "des998": "оценивает энергопотребление сайта в реальном времени по device-independent признакам структуры страницы и предлагает действия разработчику; заявленная точность на 9,7% выше performance-score подходов, что отделяет energy efficiency от обычной web performance.",
    "des1003": "дает системный hotkey поверх любого desktop-приложения: выделенный текст автоматически маршрутизируется в перевод, объяснение или summary, а профиль пользователя персонализирует ответы; исчезают постоянные copy/paste и переключения между окнами.",
    "des1006": "офлайн превращает мультимодальные данные товара в структурированную карточку и рекламный текст, а во время стрима отвечает на выбранные вопросы с event-memory; метрики question recognition 0,913 и response quality 0,876 связывают workflow с измеримым качеством.",
    "des1012": "стандартизует LLM query reformulation через единый API, retrieval-agnostic backends, versioned prompts и готовые BEIR/MS MARCO benchmarks; ценность — честное сравнение и воспроизводимость методов, ранее разбросанных по разным реализациям.",
    "des1017": "профилирует статические и изменяющиеся knowledge graphs из RDF или SPARQL на уровне данных и schema, включая cohesion, connectivity и inheritance depth; web UI делает временную динамику KG наблюдаемой и сравнимой.",
    "des1019": "оборачивает несколько tabular foundation models единым API для preprocessing, inference, fine-tuning и benchmark; интерактивный demo добавляет не только speed/quality, но и fairness и calibration для ответственного выбора модели.",
    "des1025": "строит замкнутый цикл perturbation–review–evaluation для AI peer review и, в отличие от текстовых тестов, искажает также таблицы и формулы; interface позволяет воспроизводимо обнаруживать нестабильное поведение reviewer-моделей.",
    "des1028": "Schema-Grounded Semantic Structurer переводит естественные требования строительной отрасли в валидный IDS XML; LLM служит семантическим мостом, а schema grounding удерживает результат в формальном промышленном стандарте.",
    "des1030": "дает пользователю определять доверенные scopes веб-источников и отслеживает смысловые изменения страниц для выборочной переиндексации; browser extension объединяет relevance, provenance и freshness в управляемый RAG.",
    "des1031": "объединяет слабые текстовые, табличные и image-derived сигналы в вероятностные labels и согласует решения через entity graph; demo проверяет claims о новых объектах недвижимости и объясняет их на карте, графе и демографических overlays.",
    "des1034": "ускоряет VLA-контроллер без переобучения через instruction-prefix KV cache, mixed precision и single-step rollout; посетитель в реальном времени переключает оптимизации и видит SimplerEnv episodes, то есть speed/behavior trade-off демонстрируется непосредственно.",
}


# Official/author repositories used as a fallback when the exact four-page
# proceedings PDF is not publicly downloadable.  These are deliberately kept
# separate from full text: README/code evidence must not be presented as if it
# came from the paper.
REPOSITORIES = {
    "des0461": "https://github.com/WinstonCHEN1/RISE",
    "des0958": "https://github.com/Roamify-Research/Extension",
    "des960": "https://github.com/Jo-wang/CIRES-DriftNavi",
    "des968": "https://github.com/BAI-LAB/BaiJia",
    "des974": "https://github.com/DavidMiao1127/LegalKit",
    "des978": "https://github.com/SongyuanSui/EdgeCloud-AD",
    "des994": "https://github.com/wad3birch/Intra_AI",
    "des997": "https://github.com/XGraph-Team/SumoXPypsa",
    "des998": "https://github.com/sohaibayub/GreenWebInspector",
    "des1003": "https://github.com/USTCKevinF/Swen",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    rows = read_tsv(root / "index.tsv")
    if set(SUMMARIES) != {row["paper_id"] for row in rows}:
        raise RuntimeError("summary ids do not match index.tsv")

    pdf_count = sum((root / "pdf" / row["filename"]).exists() for row in rows)
    repo_only_count = sum(
        row["paper_id"] in REPOSITORIES
        and not (root / "pdf" / row["filename"]).exists()
        for row in rows
    )
    abstract_only_count = len(rows) - pdf_count - repo_only_count

    lines = [
        "# The Web Conference 2027 — ретроспектива Demo Track 2026",
        "",
        "Аналитический корпус прошлогоднего Demo Track для подготовки заявки на "
        "[The Web Conference 2027](https://www2027.thewebconf.org/). Формат списка повторяет "
        "идею репозитория `aaai26-demos`: коротко — что решали, что сделали и чем работа "
        "выделяется. Последняя часть — практические выводы именно для WebConf'27.",
        "",
        "## Корпус и методика",
        "",
        "- Источник состава: официальный список из **40 принятых demo papers WebConf'26**.",
        f"- Для **{pdf_count} работ** найдены легальные OA/author PDFs и выполнена конвертация "
        f"**Marker 2.0.0 → Markdown**; результат проверен по manifest (`{pdf_count}/{pdf_count} ok`).",
        f"- Для **{repo_only_count} работ** без доступного proceedings PDF найден официальный "
        "или авторский GitHub. Их анализ дополнительно опирается на код и README; такие строки "
        "помечены `GitHub/code+README`, а не `full text`.",
        f"- Для оставшихся **{abstract_only_count} работ** ACM PDF недоступен без browser "
        "challenge/подписки и официальный repository не найден; анализ ограничен публичным "
        "abstract и помечен `abstract`.",
        "- Формулировки «выделяется» ниже — аналитические выводы по принятому корпусу, а не "
        "цитаты или раскрытые мотивы рецензентов.",
        "",
        "## Все принятые demo papers WebConf'26",
        "",
    ]

    for number, row in enumerate(rows, 1):
        paper_id = row["paper_id"]
        pdf = root / "pdf" / row["filename"]
        if pdf.exists():
            title_url = f"pdf/{row['filename']}"
            repo = REPOSITORIES.get(paper_id)
            repo_link = f" · [GitHub]({repo})" if repo else ""
            evidence = f"[full text · MD](md/{paper_id}/{paper_id}.md){repo_link}"
        elif paper_id in REPOSITORIES:
            title_url = REPOSITORIES[paper_id]
            evidence = f"GitHub/code+README · [DOI]({row['doi_url']})"
        else:
            title_url = row["doi_url"]
            evidence = "abstract"
        lines.append(
            f"{number}. **[{row['title']}]({title_url})** (`{paper_id}`) — "
            f"{SUMMARIES[paper_id]} *{evidence}*."
        )

    lines.extend(
        [
            "",
            "## Что характерно для принятого корпуса",
            "",
            "Индикаторы ниже не являются взаимоисключающими категориями; это keyword-анализ "
            "заголовков и abstract/full text:",
            "",
            "- **26/40** работ используют LLM или агентов как существенную часть системы; сам "
            "факт использования LLM уже не является вкладом — принимаемые работы показывают "
            "новый workflow, control layer, данные или измеримую практическую пользу.",
            "- **34/40** явно предлагают интерактивную platform/interface/dashboard/browser "
            "experience. Для demo track интерфейс — часть научного аргумента, а не упаковка.",
            "- **23/40** явно содержат evaluation, benchmark, robustness, fairness, calibration "
            "или другую измеримую проверку. «Работает на сцене» обычно подкреплено числами.",
            "- Не менее **15/40** abstract прямо указывают open source, public API, live demo или "
            "другой открытый artifact; реальная доля выше, поскольку не все abstract перечисляют ссылки.",
            "",
            "Повторяющийся паттерн сильной заявки: **конкретная боль → работающая end-to-end "
            "система → понятный hands-on сценарий → измеримая проверка → контролируемость и "
            "воспроизводимый artifact**. Особенно заметны human-in-the-loop управление, "
            "provenance/freshness, интерпретируемость и опыт реального deployment.",
            "",
            "## Как переложить это на заявку WebConf'27",
            "",
            "Официальный call требует уже **implemented and tested system**, прямого hands-on "
            "взаимодействия и описания развертывания на площадке. Отбор идет по originality, "
            "significance, quality и clarity. Практически это означает:",
            "",
            "1. Сформулировать один демонстрируемый пользовательский путь на 2–4 минуты: input, "
            "момент взаимодействия, наблюдаемый результат и сравнение/контроль.",
            "2. Отделить системный вклад от базовой модели: orchestration, retrieval, memory, "
            "interface, validation, privacy, latency или domain adaptation должны быть явными.",
            "3. Дать хотя бы одну численную проверку и один качественный case study; для deployed "
            "систем особенно убедительны latency, reliability и реальные usage metrics.",
            "4. Приложить короткое видео, repository и, если возможно, стабильный web demo; call "
            "прямо поощряет external material.",
            "5. Описать venue setup и fallback: hardware, network, accounts/data, время reset, "
            "offline recording на случай сбоя и то, что именно делает посетитель.",
            "6. Заложить отдельный раздел про ethical use of data / informed consent — он обязателен.",
            "",
            "### Рекомендуемая структура четырех страниц",
            "",
            "- **Стр. 1:** проблема, аудитория, gap, 2–3 contributions и один screenshot/teaser.",
            "- **Стр. 2:** архитектура и то, что технически ново относительно baseline/related systems.",
            "- **Стр. 3:** пошаговый demo script, интеракции посетителя и план deployment на venue.",
            "- **Стр. 4:** evaluation/case study, ограничения, ethics, ссылки на video/code/demo и references.",
            "",
            "## Формальные требования WebConf'27",
            "",
            "- Deadline: **16 ноября 2026, end-of-day AoE**; notification — 4 января 2027, "
            "camera-ready — 31 января 2027.",
            "- Один PDF, английский язык, ACM `sigconf` double-column, максимум **4 страницы "
            "включая references**.",
            "- Подача через OpenReview в Demo track; заявка **не анонимная**, review single-blind.",
            "- Обязательны очная demo-презентация и onsite poster; no-show может привести к withdrawal.",
            "- Принятая работа требует отдельной conference registration. Если ни один автор не "
            "покрыт ACM Open, call указывает субсидированный APC 2027: $500 для ACM/SIG member "
            "или $750 для non-member.",
            "",
            "Официальные страницы: [Call for Demonstrations](https://www2027.thewebconf.org/demos/) · "
            "[Important Dates](https://www2027.thewebconf.org/important-dates/) · "
            "[Accepted Demos 2026](https://www2026.thewebconf.org/accepted/demo.html).",
            "",
            "## Структура репозитория и воспроизведение",
            "",
            "```text",
            "www27-demos/",
            f"├── pdf/                 # {pdf_count} доступных OA/author PDFs",
            "├── md/<paper_id>/       # Marker Markdown + извлеченные изображения",
            "├── metadata/            # cached Crossref/OpenAlex/Unpaywall/etc.",
            "├── index.tsv            # 40 официальных работ, DOI, PDF provenance/status",
            "├── abstracts.tsv        # 40 abstract + provenance",
            "├── etl.py               # incremental Marker pipeline",
            "└── tools/               # collection, download and report scripts",
            "```",
            "",
            "```powershell",
            "python -m venv .venv",
            ".\\.venv\\Scripts\\python.exe -m pip install -e .",
            ".\\.venv\\Scripts\\python.exe .\\tools\\collect_papers.py --metadata-only",
            ".\\.venv\\Scripts\\python.exe .\\tools\\extract_abstracts.py",
            ".\\.venv\\Scripts\\python.exe .\\etl.py --mode fast --no-ocr",
            ".\\.venv\\Scripts\\python.exe .\\tools\\build_report.py",
            "```",
            "",
            "`--no-ocr` выбран намеренно: доступные статьи — born-digital PDF с текстовым слоем; "
            "OCR здесь только замедляет прогон и может ухудшить формулы. Pipeline инкрементальный и "
            "повторно обрабатывает только отсутствующие/неудачные результаты.",
            "",
            "## Ограничения",
            "",
            f"- Полный корпус содержит 40 работ, но локально сохранены только те {pdf_count} PDF, которые "
            "авторы или репозитории открыли без обхода access controls. ACM Cloudflare/OpenReview "
            "challenges намеренно не обходились.",
            "- GitHub-строки позволяют проверить архитектуру и воспроизвести систему, но не "
            "заменяют доказательства, таблицы и ограничения из полного текста статьи.",
            "- Для `abstract`-строк нельзя надежно проверить детали, не вошедшие в публичную "
            "аннотацию; соответствующие тезисы поэтому уже и осторожнее full-text тезисов.",
            "- Автоматический keyword-count — описательная статистика корпуса, не причинное "
            "объяснение решений Program Committee.",
            "",
        ]
    )

    (root / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {len(rows)} paper summaries to {root / 'README.md'}")


if __name__ == "__main__":
    main()
