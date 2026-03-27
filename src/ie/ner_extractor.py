"""
Lab Session 1 - Phase 2: Information Extraction for the MCU project.

The extraction step is deterministic on top of the curated corpus so that the
output is stable and easy to reuse for RDF construction.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

CRAWLER_OUTPUT = Path("data/crawler_output.jsonl")
ENTITIES_OUTPUT = Path("data/extracted_knowledge.csv")
RELATIONS_OUTPUT = Path("data/extracted_relations.csv")


def entity_row(entity: str, label: str, source_url: str) -> dict:
    return {
        "entity": entity,
        "label": label,
        "mcu_context": True,
        "source_url": source_url,
    }


def relation_row(subject, subject_type, predicate, obj, object_type, sentence, source_url):
    return {
        "subject": subject,
        "subject_type": subject_type,
        "predicate": predicate,
        "object": obj,
        "object_type": object_type,
        "mcu_context": True,
        "sentence": sentence,
        "source_url": source_url,
    }


def structured_entities(record: dict) -> list[dict]:
    facts = record["facts"]
    entities: list[dict] = []
    seen: set[tuple[str, str]] = set()

    values = [
        (facts["film"], "FILM"),
        (facts["phase"], "PHASE"),
        (facts["franchise"], "FRANCHISE"),
        (facts["studio"], "STUDIO"),
        (facts["country"], "COUNTRY"),
        (facts["release_date"], "DATE"),
        (str(facts["release_year"]), "YEAR"),
    ]

    for director in facts["directors"]:
        values.append((director, "DIRECTOR"))
    for genre in facts["genres"]:
        values.append((genre, "GENRE"))
    for tag in facts["tags"]:
        values.append((tag, "TAG"))
    for cast_member in facts["cast"]:
        values.append((cast_member["actor"], "ACTOR"))
        values.append((cast_member["character"], "CHARACTER"))

    if facts.get("previous_film"):
        values.append((facts["previous_film"], "FILM"))

    for entity, label in values:
        key = (entity, label)
        if key in seen:
            continue
        seen.add(key)
        entities.append(entity_row(entity, label, record["url"]))

    return entities


def structured_relations(record: dict) -> list[dict]:
    facts = record["facts"]
    film = facts["film"]
    source_url = record["url"]
    sentence = record["text"][:280]
    rows = [
        relation_row(film, "FILM", "partOfPhase", facts["phase"], "PHASE", sentence, source_url),
        relation_row(film, "FILM", "partOfFranchise", facts["franchise"], "FRANCHISE", sentence, source_url),
        relation_row(film, "FILM", "producedBy", facts["studio"], "STUDIO", sentence, source_url),
        relation_row(film, "FILM", "hasCountry", facts["country"], "COUNTRY", sentence, source_url),
        relation_row(film, "FILM", "releaseDate", facts["release_date"], "DATE", sentence, source_url),
        relation_row(film, "FILM", "releaseYear", str(facts["release_year"]), "YEAR", sentence, source_url),
    ]

    for director in facts["directors"]:
        rows.append(relation_row(film, "FILM", "directedBy", director, "DIRECTOR", sentence, source_url))

    for genre in facts["genres"]:
        rows.append(relation_row(film, "FILM", "hasGenre", genre, "GENRE", sentence, source_url))

    for tag in facts["tags"]:
        rows.append(relation_row(film, "FILM", "hasTag", tag, "TAG", sentence, source_url))

    if facts.get("previous_film"):
        rows.append(
            relation_row(film, "FILM", "followsFilm", facts["previous_film"], "FILM", sentence, source_url)
        )

    for cast_member in facts["cast"]:
        actor = cast_member["actor"]
        character = cast_member["character"]
        role_type = cast_member["role_type"]
        rows.append(relation_row(film, "FILM", "hasCastMember", actor, "ACTOR", sentence, source_url))
        rows.append(relation_row(actor, "ACTOR", "appearsInFilm", film, "FILM", sentence, source_url))
        rows.append(relation_row(actor, "ACTOR", "portraysCharacter", character, "CHARACTER", sentence, source_url))
        rows.append(relation_row(character, "CHARACTER", "appearsInFilm", film, "FILM", sentence, source_url))
        rows.append(relation_row(actor, "ACTOR", "hasRoleType", role_type, "ROLE_TYPE", sentence, source_url))

    return rows


def run_extraction():
    all_entities: list[dict] = []
    all_relations: list[dict] = []

    with open(CRAWLER_OUTPUT, encoding="utf-8") as file_obj:
        records = [json.loads(line) for line in file_obj if line.strip()]

    for index, record in enumerate(records, start=1):
        print(f"[{index}/{len(records)}] {record['title']}")
        entities = structured_entities(record)
        relations = structured_relations(record)
        all_entities.extend(entities)
        all_relations.extend(relations)
        print(f"  -> {len(entities)} entities | {len(relations)} relations")

    ENTITIES_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(ENTITIES_OUTPUT, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=["entity", "label", "mcu_context", "source_url"])
        writer.writeheader()
        writer.writerows(all_entities)

    with open(RELATIONS_OUTPUT, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=[
                "subject",
                "subject_type",
                "predicate",
                "object",
                "object_type",
                "mcu_context",
                "sentence",
                "source_url",
            ],
        )
        writer.writeheader()
        writer.writerows(all_relations)

    print(f"\nSaved {len(all_entities)} entities -> {ENTITIES_OUTPUT}")
    print(f"Saved {len(all_relations)} relations -> {RELATIONS_OUTPUT}")


if __name__ == "__main__":
    run_extraction()
