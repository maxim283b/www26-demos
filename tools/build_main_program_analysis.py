#!/usr/bin/env python3
"""Build a reproducible title/abstract analysis of the WWW'26 main programme."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import pypdfium2 as pdfium


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

TRACKS = [
    ("Keynotes", ROOT / "tracks/keynotes"),
    ("Track 1 · Economics, Online Markets and Human Computation", ROOT / "tracks/research/economics-online-markets-human-computation"),
    ("Track 2 · Graph Algorithms and Modeling for the Web", ROOT / "tracks/research/graph-algorithms-modeling"),
    ("Track 3 · Responsible Web", ROOT / "tracks/research/responsible-web"),
    ("Track 4 · Search and Retrieval-Augmented AI", ROOT / "tracks/research/search-retrieval-augmented-ai"),
    ("Track 5 · Security and Privacy", ROOT / "tracks/research/security-privacy"),
    ("Track 6 · Semantics and Knowledge", ROOT / "tracks/research/semantics-knowledge"),
    ("Track 7 · Social Networks and Social Media", ROOT / "tracks/research/social-networks-social-media"),
    ("Track 8 · Systems and Infrastructure for Web, Mobile, and Web of Things", ROOT / "tracks/research/systems-infrastructure-web-mobile-iot"),
    ("Track 9 · User Modeling, Personalization and Recommendation", ROOT / "tracks/research/user-modeling-personalization-recommendation"),
    ("Track 10 · Web Mining and Content Analysis", ROOT / "tracks/research/web-mining-content-analysis"),
    ("Industry Track", ROOT / "tracks/industry"),
    ("Short Papers", ROOT / "tracks/short-papers"),
    ("Web4Good", ROOT / "tracks/web4good"),
]

TOPICS = {
    "LLM, агенты и генеративный ИИ": r"\b(llms?|large language models?|generative ai|agentic|multi.?agent|foundation models?|prompt\w*|in.?context|chain.of.thought|reasoning)\b",
    "Поиск, RAG и ответы на вопросы": r"\b(search\w*|retriev\w*|rag\b|question answer\w*|query|ranking|rerank\w*|information retrieval|web index\w*)\b",
    "Рекомендательные системы и персонализация": r"\b(recommen\w*|personali[sz]\w*|collaborative filter\w*|user model\w*|click.through|ctr\b)\b",
    "Графы и knowledge graphs": r"\b(graph\w*|network embedding\w*|knowledge graph\w*|link prediction|node classification|hypergraph\w*)\b",
    "Безопасность, приватность и атаки": r"\b(secur\w*|privacy|attack\w*|adversarial|malware|phishing|vulnerab\w*|authenticat\w*|watermark\w*|membership inference|threat\w*)\b",
    "Responsible AI, fairness и объяснимость": r"\b(fair\w*|bias\w*|responsib\w*|explain\w*|interpretab\w*|accountab\w*|transparen\w*|align\w*|harm\w*|toxicity|safe\w*|unlearning)\b",
    "Дезинформация и целостность контента": r"\b(misinformation|disinformation|fake news|deepfake\w*|rumou?r\w*|fact.check\w*|content moderation|harmful meme\w*)\b",
    "Мультимодальность и vision-language": r"\b(multimodal|multi.modal|vision.language|image\w*|video\w*|audio\w*|visual\w*|cross.modal)\b",
    "Социальные сети и поведение пользователей": r"\b(social media|social network\w*|communit\w*|polari[sz]\w*|user behavio\w*|online behavio\w*|engagement|influence|crowd\w*)\b",
    "Системы, эффективность и edge/cloud": r"\b(distributed systems?|infrastructure|edge computing|cloud\w*|latency|throughput|efficien\w*|scalab\w*|resource allocation|model serving|cach\w*|federated learning)\b",
    "Временные ряды, события и прогнозирование": r"\b(time series|forecast\w*|temporal|event sequence\w*|anomaly detection|streaming|dynamic network\w*)\b",
    "Web4Good, здоровье и устойчивость": r"\b(health\w*|clinical|medical|well.being|sustainab\w*|climate|education\w*|social good|humanitarian|accessib\w*|minority language\w*|low.resource)\b",
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def resolve_pdf(track_dir: Path, row: dict[str, str]) -> Path | None:
    pdf_dir = track_dir / "pdf"
    if row.get("filename"):
        candidate = pdf_dir / row["filename"]
        if candidate.exists():
            return candidate
    matches = sorted(pdf_dir.glob(f"{row['paper_id']}*.pdf"))
    return matches[0] if matches else None


def extract_abstract(pdf: Path | None) -> str:
    if not pdf:
        return ""
    try:
        document = pdfium.PdfDocument(str(pdf))
        chunks: list[str] = []
        for page_number in range(min(2, len(document))):
            page = document[page_number]
            text_page = page.get_textpage()
            chunks.append(text_page.get_text_range())
            text_page.close()
            page.close()
        document.close()
        raw = "\n".join(chunks)
    except Exception:
        return ""
    raw = raw.replace("\x00", " ")
    match = re.search(
        r"\babstract\b\s*[:.—-]?\s*(.+?)(?=\b(?:ccs concepts|keywords|additional key words|index terms|1\s+introduction|introduction)\b)",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return clean(match.group(1))[:6000] if match else ""


def load_corpus(refresh: bool) -> list[dict[str, str]]:
    cache = REPORTS / "www26-main-program-corpus.tsv"
    if cache.exists() and not refresh:
        with cache.open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh, delimiter="\t"))

    records: list[dict[str, str]] = []
    for track_name, track_dir in TRACKS:
        with (track_dir / "index.tsv").open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                pdf = resolve_pdf(track_dir, row)
                records.append(
                    {
                        "paper_id": row["paper_id"],
                        "track": track_name,
                        "title": clean(row.get("title", "")),
                        "doi": row.get("doi", ""),
                        "doi_url": row.get("doi_url", ""),
                        "pdf": str(pdf.relative_to(ROOT)) if pdf else "",
                        "abstract": extract_abstract(pdf),
                        "code_url": row.get("code_url", ""),
                    }
                )
    REPORTS.mkdir(exist_ok=True)
    with cache.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=records[0].keys(), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    return records


def topic_hits(records: list[dict[str, str]]) -> tuple[dict[str, list[dict[str, str]]], dict[str, Counter]]:
    hits: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_track: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        haystack = f"{record['title']} {record['abstract']}".lower()
        for topic, pattern in TOPICS.items():
            if re.search(pattern, haystack, flags=re.IGNORECASE):
                hits[topic].append(record)
                by_track[record["track"]][topic] += 1
    return hits, by_track


def representative(records: list[dict[str, str]], pattern: str, limit: int = 4) -> list[dict[str, str]]:
    rx = re.compile(pattern, re.IGNORECASE)
    ranked = sorted(
        records,
        key=lambda r: (len(rx.findall(r["title"])) * 6 + len(rx.findall(r["abstract"])), len(r["abstract"])),
        reverse=True,
    )
    chosen: list[dict[str, str]] = []
    seen_tracks: set[str] = set()
    for row in ranked:
        if row["track"] in seen_tracks and len(chosen) < 3:
            continue
        chosen.append(row)
        seen_tracks.add(row["track"])
        if len(chosen) == limit:
            break
    return chosen


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%".replace(".", ",")


def build_report(records: list[dict[str, str]]) -> str:
    hits, by_track = topic_hits(records)
    track_counts = Counter(r["track"] for r in records)
    abstracts = sum(bool(r["abstract"]) for r in records)
    pdfs = sum(bool(r["pdf"]) for r in records)
    code = sum(bool(r["code_url"]) for r in records)
    research_count = sum(v for k, v in track_counts.items() if k.startswith("Track "))

    lines = [
        "# WWW’26: карта основного proceedings и ориентиры для подачи на WWW’27",
        "",
        "## Короткий вывод",
        "",
        f"В корпусе **{len(records)} материалов**: {research_count} full papers десяти research-треков, "
        f"{track_counts['Industry Track']} industry papers, {track_counts['Short Papers']} short papers, "
        f"{track_counts['Web4Good']} Web4Good papers и {track_counts['Keynotes']} keynote papers. "
        "Главный сигнал WWW’26 — не просто массовое присутствие LLM, а переход к веб-системам, где "
        "генеративные модели соединяются с поиском, персонализацией, графами, мультимодальными данными "
        "и проверяемыми ограничениями безопасности/ответственности.",
        "",
        "Для основной секции WWW’27 наиболее убедительна работа, которая формулирует именно веб-задачу, "
        "а не только применяет новую модель: показывает реалистичный масштаб или поведение пользователей, "
        "сравнивается с сильными свежими baseline, содержит ablation/error analysis и даёт воспроизводимый артефакт.",
        "",
        "## Корпус и методика",
        "",
        f"Проверено PDF: **{pdfs}/{len(records)}**; автоматически выделен abstract: **{abstracts}/{len(records)}** "
        f"({pct(abstracts, len(records))}). Тематические метки рассчитаны по названиям и abstract как "
        "multi-label категории, поэтому суммы по темам не обязаны совпадать с числом статей. "
        f"Для {code} записей второй части proceedings в метаданных найдена ссылка на код.",
        "",
        "Это обзор ландшафта, а не замена экспертному чтению: автоматический подсчёт помогает увидеть "
        "плотность направлений, но не оценивает корректность экспериментов и силу novelty отдельной статьи.",
        "",
        "## Состав proceedings",
        "",
        "| Раздел | Материалов | Доля корпуса |",
        "| --- | ---: | ---: |",
    ]
    for name, _ in TRACKS:
        count = track_counts[name]
        lines.append(f"| {name} | {count} | {pct(count, len(records))} |")

    lines += [
        "",
        "## Сквозные темы",
        "",
        "| Тема | Статей | Доля корпуса | Где особенно заметна |",
        "| --- | ---: | ---: | --- |",
    ]
    for topic, papers in sorted(hits.items(), key=lambda item: len(item[1]), reverse=True):
        leaders = sorted(((counter[topic], track) for track, counter in by_track.items()), reverse=True)[:2]
        where = "; ".join(f"{track} ({count})" for count, track in leaders if count)
        lines.append(f"| {topic} | {len(papers)} | {pct(len(papers), len(records))} | {where} |")

    lines += ["", "### Что стоит за числами", ""]
    interpretations = {
        "LLM, агенты и генеративный ИИ": "LLM становятся компонентом pipeline: маршрутизатором, планировщиком, симулятором пользователя, средством разметки или рассуждения. Конкурировать одним prompting всё труднее; важны измеримый системный выигрыш, стоимость и устойчивость.",
        "Поиск, RAG и ответы на вопросы": "RAG рассматривается как система принятия решений: когда искать, что извлекать, как переписывать запрос и как проверять ответ. Сильная постановка должна отдельно оценивать retrieval и generation, включая latency и стоимость.",
        "Рекомендательные системы и персонализация": "Центр тяжести смещён к генеративным и conversational recommenders, long-term memory, cold-start и multi-behavior сценариям. Нужны реалистичные split, защита от leakage и метрики помимо offline relevance.",
        "Responsible AI, fairness и объяснимость": "Ответственность всё чаще встроена в алгоритм и evaluation, а не оставлена отдельным разделом. Для подачи полезны group-wise результаты, failure modes и явное описание затрагиваемых пользователей.",
        "Безопасность, приватность и атаки": "Работы оценивают не только точность защиты, но и адаптивного противника, transferability и эксплуатационную цену. Threat model должен быть сформулирован до экспериментов.",
        "Мультимодальность и vision-language": "Мультимодальность используется для веб-контента, misinformation, recommendation и knowledge extraction. Простого fusion недостаточно: ценятся missing-modality tests, cross-domain robustness и анализ вклада каждой модальности.",
        "Системы, эффективность и edge/cloud": "Эффективность становится частью научного вклада: routing, caching, serving, федеративные и edge-сценарии. Следует измерять wall-clock latency, память, throughput и стоимость, а не только FLOPs.",
    }
    for topic, text in interpretations.items():
        lines += [f"**{topic} — {len(hits.get(topic, []))} работ.** {text}", ""]

    lines += ["## Репрезентативные работы по крупнейшим направлениям", ""]
    for topic, papers in sorted(hits.items(), key=lambda item: len(item[1]), reverse=True)[:8]:
        lines.append(f"### {topic}")
        lines.append("")
        for row in representative(papers, TOPICS[topic]):
            title = row["title"].replace("|", "\\|")
            link = row["doi_url"] or row["pdf"].replace("\\", "/")
            lines.append(f"- [{title}]({link}) — {row['track']}")
        lines.append("")

    lines += [
        "## Возможности для WWW’27",
        "",
        "Ниже — не прогноз тем CFP, а области, где по карте WWW’26 виден хороший баланс актуальности и пространства для нового вклада.",
        "",
        "1. **Agentic Web с проверяемым поведением.** Агент, работающий с реальным веб-интерфейсом или несколькими источниками, плюс benchmark длинных сценариев, recovery после ошибок и оценка безопасности.",
        "2. **RAG как адаптивная веб-система.** Совместное решение «искать или отвечать», выбор источника/инструмента и budget-aware routing; отдельно измерять factuality, retrieval recall, latency и денежную стоимость.",
        "3. **Персонализация с долговременной памятью и контролем пользователя.** Не только рост relevance, но editable/forgettable memory, privacy, drift и долгосрочные эффекты.",
        "4. **Надёжность мультимодального веб-контента.** Детектирование и объяснение манипуляций при неполных модальностях, domain shift и мультиязычности; human study существенно усилит вклад.",
        "5. **Web-scale эффективность LLM.** Маршрутизация между моделями, caching и early exit с Pareto-анализом качество–latency–cost и нагрузочным экспериментом.",
        "6. **Графы + LLM без декоративного объединения.** Задача, где структура графа даёт причинно понятный выигрыш; обязательны structure-free baseline, ablation и тест на перенос.",
        "7. **Responsible recommendation/search.** Оптимизация полезности вместе с exposure fairness, safety или well-being, с анализом компромиссов, а не одной агрегированной метрикой.",
        "8. **Мультиязычный и low-resource Web.** Индексация, retrieval, модерация или knowledge extraction для языков длинного хвоста с честной оценкой coverage и участием носителей языка.",
        "",
        "## Как превратить проект из demo/workshop в main-track paper",
        "",
        "| Слой | Что должно быть в основной подаче |",
        "| --- | --- |",
        "| Исследовательский вопрос | Проверяемая гипотеза и ясное отличие от системы-демонстратора |",
        "| Novelty | Новый метод, постановка, данные или эмпирическое открытие; точное позиционирование относительно ближайших работ WWW’26 |",
        "| Baselines | Сильные методы 2025–2026, простой baseline и компонентные ablation |",
        "| Evaluation | Несколько datasets/доменов, доверительные интервалы или тесты значимости, error analysis |",
        "| Web relevance | Пользователи, веб-данные, веб-масштаб или сетевые взаимодействия должны быть центральными, а не фоном |",
        "| Systems evidence | Latency, throughput, память и стоимость — если заявляется практичность или масштабируемость |",
        "| Human dimension | User study или экспертная оценка, если качество нельзя надёжно свести к автоматическим метрикам |",
        "| Reproducibility | Код, конфигурации, seeds, лицензии данных и воспроизводимый pipeline |",
        "| Responsible research | Threats to validity, ethics, privacy, intended use и потенциальный вред |",
        "",
        "## Практический план подготовки",
        "",
        "1. Выбрать 15–25 ближайших работ из репрезентативных списков и таблицы корпуса, затем вручную заполнить матрицу: задача, данные, baseline, метрики, ограничение.",
        "2. Одним предложением сформулировать разрыв: что эти работы принципиально не измеряют или не умеют делать.",
        "3. До разработки зафиксировать evaluation protocol и минимальный набор ablation, чтобы вклад не зависел от одной удачной метрики.",
        "4. Сначала получить сильный результат на публичном benchmark, затем добавить собственный реалистичный веб-сценарий или production-like нагрузку.",
        "5. Подготовить anonymized repository и artifact checklist одновременно с экспериментами, а не перед дедлайном.",
        "",
        "## Воспроизводимость отчёта",
        "",
        "```powershell",
        "python tools/build_main_program_analysis.py --refresh",
        "```",
        "",
        "Машиночитаемый корпус с abstract находится в `reports/www26-main-program-corpus.tsv`. Его удобно фильтровать по треку, DOI и ключевым словам для следующего этапа ручного literature review.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Re-extract abstracts from PDFs")
    args = parser.parse_args()
    records = load_corpus(args.refresh)
    report = REPORTS / "www26-main-program-analysis.md"
    report.write_text(build_report(records), encoding="utf-8")
    print(f"Wrote {report.relative_to(ROOT)} for {len(records)} records")


if __name__ == "__main__":
    main()
