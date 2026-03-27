"""
Lab Session 1 - Phase 2: Information Extraction.

This stage now supports deterministic extraction from the structured football
injury corpus generated in step 1, while keeping a spaCy fallback for generic
text if needed.
"""

import csv
import json
from pathlib import Path

try:
    import spacy
except ImportError:
    spacy = None

CRAWLER_OUTPUT = Path("data/crawler_output.jsonl")
ENTITIES_OUTPUT = Path("data/extracted_knowledge.csv")
RELATIONS_OUTPUT = Path("data/extracted_relations.csv")

KEEP_LABELS = {"PERSON", "ORG", "GPE", "DATE", "EVENT", "LOC", "CARDINAL", "TIME"}
STRUCTURED_LABELS = {
    "PERSON",
    "ORG",
    "GPE",
    "DATE",
    "COMPETITION",
    "SEASON",
    "INJURY",
    "INJURY_TYPE",
    "BODY_PART",
    "NUMBER",
}

nlp = None
if spacy is not None:
    try:
        print("Loading spaCy model...")
        nlp = spacy.load("en_core_web_trf")
    except OSError:
        nlp = None


def sentence_has_injury_context(text: str) -> bool:
    text_lower = text.lower()
    return any(
        keyword in text_lower
        for keyword in {
            "injury",
            "rupture",
            "fracture",
            "strain",
            "sprain",
            "meniscus",
            "hamstring",
            "achilles",
            "recovery",
            "rehabilitation",
        }
    )


def structured_entities(rec: dict) -> list[dict]:
    facts = rec["facts"]
    values = [
        (facts["player"], "PERSON"),
        (facts["club"], "ORG"),
        (facts["country"], "GPE"),
        (facts["competition"], "COMPETITION"),
        (facts["season"], "SEASON"),
        (facts["injury_instance"], "INJURY"),
        (facts["injury_type"], "INJURY_TYPE"),
        (facts["injury_label"], "INJURY_TYPE"),
        (facts["body_part"], "BODY_PART"),
        (facts["injury_date"], "DATE"),
        (str(facts["recovery_days"]), "NUMBER"),
        (str(facts["games_absent"]), "NUMBER"),
    ]
    seen = set()
    entities = []
    for entity, label in values:
        key = (entity, label)
        if key in seen:
            continue
        seen.add(key)
        entities.append(
            {
                "entity": entity,
                "label": label,
                "injury_context": True,
                "source_url": rec["url"],
            }
        )
    return entities


def structured_relations(rec: dict) -> list[dict]:
    facts = rec["facts"]
    injury = facts["injury_instance"]
    sentence = rec["text"][:250]
    return [
        relation_row(facts["player"], "PERSON", "playsFor", facts["club"], "ORG", sentence, rec["url"]),
        relation_row(facts["player"], "PERSON", "represents", facts["country"], "GPE", sentence, rec["url"]),
        relation_row(facts["player"], "PERSON", "suffersInjury", injury, "INJURY", sentence, rec["url"]),
        relation_row(injury, "INJURY", "injuryType", facts["injury_type"], "INJURY_TYPE", sentence, rec["url"]),
        relation_row(injury, "INJURY", "affectsBodyPart", facts["body_part"], "BODY_PART", sentence, rec["url"]),
        relation_row(injury, "INJURY", "occuredDuring", facts["competition"], "COMPETITION", sentence, rec["url"]),
        relation_row(injury, "INJURY", "injuryDate", facts["injury_date"], "DATE", sentence, rec["url"]),
        relation_row(injury, "INJURY", "recoveryDays", str(facts["recovery_days"]), "NUMBER", sentence, rec["url"]),
        relation_row(injury, "INJURY", "gamesAbsent", str(facts["games_absent"]), "NUMBER", sentence, rec["url"]),
    ]


def relation_row(subject, subject_type, predicate, obj, object_type, sentence, source_url):
    return {
        "subject": subject,
        "subject_type": subject_type,
        "predicate": predicate,
        "object": obj,
        "object_type": object_type,
        "injury_context": True,
        "sentence": sentence,
        "source_url": source_url,
    }


def extract_entities_spacy(text: str, source_url: str) -> list[dict]:
    if nlp is None:
        return []
    doc = nlp(text[:100_000])
    entities = []
    seen = set()
    for ent in doc.ents:
        if ent.label_ not in KEEP_LABELS:
            continue
        key = (ent.text.strip(), ent.label_)
        if key in seen:
            continue
        seen.add(key)
        entities.append(
            {
                "entity": ent.text.strip(),
                "label": ent.label_,
                "injury_context": sentence_has_injury_context(text),
                "source_url": source_url,
            }
        )
    return entities


def extract_relations_spacy(text: str, source_url: str) -> list[dict]:
    return []


def run_extraction():
    all_entities = []
    all_relations = []

    with open(CRAWLER_OUTPUT, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    for i, rec in enumerate(records):
        print(f"[{i+1}/{len(records)}] {rec['title']}")
        if "facts" in rec:
            ents = structured_entities(rec)
            rels = structured_relations(rec)
        else:
            ents = extract_entities_spacy(rec["text"], rec["url"])
            rels = extract_relations_spacy(rec["text"], rec["url"])
        all_entities.extend(ents)
        all_relations.extend(rels)
        print(f"  -> {len(ents)} entities | {len(rels)} relations")

    ENTITIES_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(ENTITIES_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["entity", "label", "injury_context", "source_url"])
        writer.writeheader()
        writer.writerows(all_entities)

    with open(RELATIONS_OUTPUT, "w", newline="", encoding="utf-8") as f:
        fields = ["subject", "subject_type", "predicate", "object", "object_type", "injury_context", "sentence", "source_url"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_relations)

    print(f"\nSaved {len(all_entities)} entities -> {ENTITIES_OUTPUT}")
    print(f"Saved {len(all_relations)} relations -> {RELATIONS_OUTPUT}")


if __name__ == "__main__":
    run_extraction()
