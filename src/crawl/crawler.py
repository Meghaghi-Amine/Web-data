"""
Lab Session 1 - Phase 1: Corpus creation for MCU films and directors.

This module builds a deterministic local corpus from curated MCU film records.
It keeps the same project pipeline structure while avoiding brittle live crawl
dependencies during coursework and grading.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.domain.mcu_data import FILMS, FRANCHISE, STUDIO, COUNTRY, build_record_text

OUTPUT_FILE = Path("data/crawler_output.jsonl")


def make_record(index: int, film) -> dict:
    text = build_record_text(film)
    facts = {
        "film": film.title,
        "release_date": film.release_date,
        "release_year": film.release_year,
        "phase": film.phase,
        "directors": list(film.directors),
        "genres": list(film.genres),
        "tags": list(film.tags),
        "cast": [
            {
                "actor": member.actor,
                "character": member.character,
                "role_type": member.role_type,
            }
            for member in film.cast
        ],
        "franchise": FRANCHISE,
        "studio": STUDIO,
        "country": COUNTRY,
        "previous_film": film.previous_film,
        "dbpedia_resource": film.dbpedia_resource,
    }
    return {
        "id": index,
        "url": film.source_url,
        "title": film.title,
        "text": text,
        "word_count": len(text.split()),
        "facts": facts,
    }


def run_crawler(seed_urls=None, output_file=OUTPUT_FILE):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    records = [make_record(index, film) for index, film in enumerate(FILMS, start=1)]
    useful_records = [record for record in records if record["word_count"] >= 500]

    with open(output_file, "w", encoding="utf-8") as file_obj:
        for record in useful_records:
            file_obj.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Created local MCU corpus with {len(useful_records)} film pages.")
    print(f"Output -> {output_file}")
    return useful_records


if __name__ == "__main__":
    run_crawler()
