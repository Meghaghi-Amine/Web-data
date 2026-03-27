"""
Lab Session 4 - KB Construction for the MCU domain.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef, XSD

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MCU = Namespace("http://example.org/mcu/")
PROP = Namespace("http://example.org/mcu/property/")
DBO = Namespace("http://dbpedia.org/ontology/")

ENTITIES_CSV = Path("data/extracted_knowledge.csv")
RELATIONS_CSV = Path("data/extracted_relations.csv")
ONTOLOGY_FILE = Path("kg_artifacts/ontology.ttl")
KG_FILE = Path("kg_artifacts/initial_kg.ttl")


def to_uri(text: str) -> URIRef:
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", text.strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return MCU[slug]


def pred_uri(predicate: str) -> URIRef:
    known = {
        "directedBy": PROP["directedBy"],
        "hasCastMember": PROP["hasCastMember"],
        "appearsInFilm": PROP["appearsInFilm"],
        "portraysCharacter": PROP["portraysCharacter"],
        "hasGenre": PROP["hasGenre"],
        "partOfPhase": PROP["partOfPhase"],
        "partOfFranchise": PROP["partOfFranchise"],
        "producedBy": PROP["producedBy"],
        "hasCountry": PROP["hasCountry"],
        "releaseDate": PROP["releaseDate"],
        "releaseYear": PROP["releaseYear"],
        "followsFilm": PROP["followsFilm"],
        "hasTag": PROP["hasTag"],
        "hasRoleType": PROP["hasRoleType"],
    }
    return known.get(predicate, PROP[predicate])


def build_ontology() -> Graph:
    graph = Graph()
    graph.bind("mcu", MCU)
    graph.bind("prop", PROP)
    graph.bind("dbo", DBO)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)

    classes = {
        "Film": "An MCU feature film.",
        "Director": "A film director working on an MCU film.",
        "Actor": "A cast member in an MCU film.",
        "Character": "A fictional character appearing in an MCU film.",
        "Genre": "A film genre.",
        "Phase": "A release phase of the MCU.",
        "Franchise": "A film franchise.",
        "Studio": "A production studio.",
        "Country": "A production country.",
        "Tag": "A thematic tag used for analysis and expansion.",
        "RoleType": "A cast role category such as lead or villain.",
        "ReleaseYear": "A release year represented as an entity.",
        "SagaFilm": "A film inferred to belong to a saga-oriented category.",
        "PhaseThreeFilm": "A film inferred to be part of Phase 3.",
    }
    for name, comment in classes.items():
        uri = MCU[name]
        graph.add((uri, RDF.type, OWL.Class))
        graph.add((uri, RDFS.label, Literal(name, lang="en")))
        graph.add((uri, RDFS.comment, Literal(comment, lang="en")))

    obj_props = [
        ("directedBy", "Film", "Director", "Links a film to its director."),
        ("hasCastMember", "Film", "Actor", "Links a film to a cast member."),
        ("appearsInFilm", "Character", "Film", "Links a character or actor appearance to a film."),
        ("portraysCharacter", "Actor", "Character", "Links an actor to a portrayed character."),
        ("hasGenre", "Film", "Genre", "Links a film to a genre."),
        ("partOfPhase", "Film", "Phase", "Links a film to an MCU phase."),
        ("partOfFranchise", "Film", "Franchise", "Links a film to a franchise."),
        ("producedBy", "Film", "Studio", "Links a film to its studio."),
        ("hasCountry", "Film", "Country", "Links a film to a country."),
        ("followsFilm", "Film", "Film", "Links a film to a previous release in the selected corpus."),
        ("hasTag", "Film", "Tag", "Links a film to a thematic tag."),
        ("hasRoleType", "Actor", "RoleType", "Links an actor appearance to a role type."),
        ("sharesDirectorWith", "Film", "Film", "Derived relation for common directors."),
        ("sharesCastMemberWith", "Film", "Film", "Derived relation for common cast."),
        ("sharesGenreWith", "Film", "Film", "Derived relation for common genre."),
        ("samePhaseAs", "Film", "Film", "Derived relation for phase membership."),
    ]
    for name, domain, range_, comment in obj_props:
        uri = PROP[name]
        graph.add((uri, RDF.type, OWL.ObjectProperty))
        graph.add((uri, RDFS.label, Literal(name, lang="en")))
        graph.add((uri, RDFS.comment, Literal(comment, lang="en")))
        graph.add((uri, RDFS.domain, MCU[domain]))
        graph.add((uri, RDFS.range, MCU[range_]))

    datatype_props = [
        ("releaseDate", "Film", XSD.date, "Release date of the film."),
        ("releaseYear", "Film", XSD.gYear, "Release year of the film."),
    ]
    for name, domain, dtype, comment in datatype_props:
        uri = PROP[name]
        graph.add((uri, RDF.type, OWL.DatatypeProperty))
        graph.add((uri, RDFS.label, Literal(name, lang="en")))
        graph.add((uri, RDFS.comment, Literal(comment, lang="en")))
        graph.add((uri, RDFS.domain, MCU[domain]))
        graph.add((uri, RDFS.range, dtype))

    for role_type in ("lead", "supporting", "villain"):
        uri = to_uri(role_type)
        graph.add((uri, RDF.type, MCU["RoleType"]))
        graph.add((uri, RDFS.label, Literal(role_type, lang="en")))

    return graph


LABEL_TO_CLASS = {
    "FILM": MCU["Film"],
    "DIRECTOR": MCU["Director"],
    "ACTOR": MCU["Actor"],
    "CHARACTER": MCU["Character"],
    "GENRE": MCU["Genre"],
    "PHASE": MCU["Phase"],
    "FRANCHISE": MCU["Franchise"],
    "STUDIO": MCU["Studio"],
    "COUNTRY": MCU["Country"],
    "TAG": MCU["Tag"],
    "ROLE_TYPE": MCU["RoleType"],
    "YEAR": MCU["ReleaseYear"],
}


def build_kg(ontology: Graph) -> Graph:
    graph = ontology

    with open(ENTITIES_CSV, encoding="utf-8") as file_obj:
        for row in csv.DictReader(file_obj):
            entity = row["entity"].strip()
            label = row["label"].strip()
            cls = LABEL_TO_CLASS.get(label)
            if cls is None:
                continue
            uri = to_uri(entity)
            graph.add((uri, RDF.type, cls))
            graph.add((uri, RDFS.label, Literal(entity, lang="en")))

    with open(RELATIONS_CSV, encoding="utf-8") as file_obj:
        for row in csv.DictReader(file_obj):
            subject = row["subject"].strip()
            predicate = row["predicate"].strip()
            obj = row["object"].strip()
            object_type = row.get("object_type", "").strip()

            subject_uri = to_uri(subject)
            predicate_uri = pred_uri(predicate)

            if predicate == "releaseDate":
                graph.add((subject_uri, predicate_uri, Literal(obj, datatype=XSD.date)))
                continue
            if predicate == "releaseYear":
                graph.add((subject_uri, predicate_uri, Literal(obj, datatype=XSD.gYear)))
                continue

            object_uri = to_uri(obj)
            graph.add((subject_uri, predicate_uri, object_uri))

            if object_type in LABEL_TO_CLASS:
                graph.add((object_uri, RDF.type, LABEL_TO_CLASS[object_type]))
                graph.add((object_uri, RDFS.label, Literal(obj, lang="en")))

    return graph


def main():
    ONTOLOGY_FILE.parent.mkdir(parents=True, exist_ok=True)
    print("Building ontology...")
    ontology = build_ontology()
    ontology.serialize(destination=str(ONTOLOGY_FILE), format="turtle")
    print(f"  OK {ONTOLOGY_FILE}")

    print("Building knowledge graph...")
    kg = build_kg(ontology)
    kg.serialize(destination=str(KG_FILE), format="turtle")

    print(f"  OK {KG_FILE}")
    print(
        f"  Stats: {len(kg)} triples | {len(set(kg.subjects()))} entities | "
        f"{len(set(kg.predicates()))} predicates"
    )


if __name__ == "__main__":
    main()
