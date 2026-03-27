"""
Lab Session 4 - Entity Linking & Predicate Alignment for the MCU project.

The project uses deterministic DBpedia alignments so the repository remains
fully reproducible offline.
"""

from __future__ import annotations

import csv
from pathlib import Path

from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef

from src.domain.mcu_data import dbpedia_resource_for

MCU = Namespace("http://example.org/mcu/")
PROP = Namespace("http://example.org/mcu/property/")
DBO = Namespace("http://dbpedia.org/ontology/")
DBR = Namespace("http://dbpedia.org/resource/")

KG_FILE = Path("kg_artifacts/initial_kg.ttl")
ALIGNMENT_FILE = Path("kg_artifacts/alignment.ttl")
MAPPING_FILE = Path("data/entity_mapping.csv")


def run_alignment():
    graph = Graph()
    graph.parse(str(KG_FILE), format="turtle")

    alignment_graph = Graph()
    for prefix, namespace in [
        ("mcu", MCU),
        ("prop", PROP),
        ("dbo", DBO),
        ("dbr", DBR),
        ("owl", OWL),
        ("rdfs", RDFS),
    ]:
        alignment_graph.bind(prefix, namespace)

    entity_rows = []
    entities = {}
    for node in set(graph.subjects()):
        if isinstance(node, URIRef) and str(node).startswith(str(MCU)):
            labels = list(graph.objects(node, RDFS.label))
            if labels:
                entities[str(node)] = str(labels[0])

    print(f"Aligning {len(entities)} local entities to DBpedia when possible...")
    for uri, label in sorted(entities.items(), key=lambda item: item[1]):
        external_uri = dbpedia_resource_for(label)
        if external_uri:
            alignment_graph.add((URIRef(uri), OWL.sameAs, URIRef(external_uri)))
            confidence = 0.99
        else:
            alignment_graph.add((URIRef(uri), RDF.type, OWL.NamedIndividual))
            alignment_graph.add(
                (URIRef(uri), RDFS.comment, Literal(f"No external alignment available for {label}", lang="en"))
            )
            external_uri = "NOT_FOUND"
            confidence = 0.0

        entity_rows.append(
            {
                "private_entity": label,
                "external_uri": external_uri,
                "confidence": confidence,
            }
        )

    predicate_alignments = {
        "directedBy": "director",
        "hasGenre": "genre",
        "producedBy": "company",
        "hasCountry": "country",
        "releaseDate": "releaseDate",
        "starring": "starring",
    }
    for local_name, external_name in predicate_alignments.items():
        local_uri = PROP[local_name if local_name != "starring" else "hasCastMember"]
        alignment_graph.add((local_uri, OWL.equivalentProperty, DBO[external_name]))

    MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MAPPING_FILE, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=["private_entity", "external_uri", "confidence"])
        writer.writeheader()
        writer.writerows(entity_rows)

    ALIGNMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    alignment_graph.serialize(destination=str(ALIGNMENT_FILE), format="turtle")
    print(f"OK Mapping -> {MAPPING_FILE}")
    print(f"OK Alignment -> {ALIGNMENT_FILE}")


if __name__ == "__main__":
    run_alignment()
