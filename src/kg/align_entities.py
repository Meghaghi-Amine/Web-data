"""
Lab Session 4 - Entity Linking & Predicate Alignment
Lie les entités du KG blessures foot à Wikidata/DBpedia
"""

import csv
import time
import re
import requests
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL

FOOTY = Namespace("http://example.org/football/")
PROP  = Namespace("http://example.org/football/property/")
WD    = Namespace("http://www.wikidata.org/entity/")
WDT   = Namespace("http://www.wikidata.org/prop/direct/")

ENTITIES_CSV   = Path("data/extracted_knowledge.csv")
KG_FILE        = Path("kg_artifacts/initial_kg.ttl")
ALIGNMENT_FILE = Path("kg_artifacts/alignment.ttl")
MAPPING_FILE   = Path("data/entity_mapping.csv")

WIKIDATA_API    = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "FootballInjuryKGAlign/1.0 (educational)"}


def search_wikidata(label: str) -> tuple:
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": label,
        "limit": 5,
    }
    try:
        r = requests.get(WIKIDATA_API, params=params, timeout=10, headers=HEADERS)
        results = r.json().get("search", [])
    except Exception:
        return None, 0.0
    if not results:
        return None, 0.0
    best = results[0]
    qid  = best.get("id", "")
    conf = 0.99 if best.get("label","").lower() == label.lower() else 0.75
    return f"http://www.wikidata.org/entity/{qid}" if qid else None, conf


def align_predicate(pred_text: str) -> list:
    query = f"""
    SELECT ?property ?propertyLabel WHERE {{
      ?property a wikibase:Property .
      ?property rdfs:label ?propertyLabel .
      FILTER(CONTAINS(LCASE(?propertyLabel), "{pred_text.lower()}"))
      FILTER(LANG(?propertyLabel) = "en")
    }} LIMIT 5
    """
    try:
        r = requests.get(
            WIKIDATA_SPARQL,
            params={"query": query, "format": "json"},
            headers={**HEADERS, "Accept": "application/json"},
            timeout=15,
        )
        return [{"uri": b["property"]["value"], "label": b["propertyLabel"]["value"]}
                for b in r.json()["results"]["bindings"]]
    except Exception:
        return []


def run_alignment():
    g = Graph()
    g.parse(str(KG_FILE), format="turtle")

    align_g = Graph()
    for prefix, ns in [("footy",FOOTY),("prop",PROP),("wd",WD),("wdt",WDT),("owl",OWL),("rdfs",RDFS)]:
        align_g.bind(prefix, ns)

    # Entités à aligner
    entities = {}
    for s, p, o in g:
        for node in [s, o]:
            if isinstance(node, URIRef) and str(node).startswith(str(FOOTY)):
                labels = list(g.objects(node, RDFS.label))
                if labels:
                    entities[str(node)] = str(labels[0])

    print(f"Aligning {len(entities)} entities…")
    mappings = []

    for uri, label in list(entities.items())[:200]:
        print(f"  {label}")
        wd_uri, conf = search_wikidata(label)
        if wd_uri:
            align_g.add((URIRef(uri), OWL.sameAs, URIRef(wd_uri)))
            mappings.append({"private_entity": label, "external_uri": wd_uri, "confidence": conf})
            print(f"    ✓ → {wd_uri} (conf={conf})")
        else:
            # Entité non trouvée → définition locale
            align_g.add((URIRef(uri), RDF.type, OWL.NamedIndividual))
            align_g.add((URIRef(uri), RDFS.comment,
                         Literal(f"Private entity not found in Wikidata: {label}", lang="en")))
            mappings.append({"private_entity": label, "external_uri": "NOT_FOUND", "confidence": 0.0})
        time.sleep(0.4)

    # Alignement prédicats spécifiques au domaine blessures
    predicates_to_align = [
        ("suffersInjury", "injury"),
        ("playsFor",      "member of sports team"),
        ("represents",    "country for sport"),
        ("occuredDuring", "competition"),
    ]
    print("\nAligning predicates…")
    for prop_name, search_term in predicates_to_align:
        candidates = align_predicate(search_term)
        if candidates:
            best = candidates[0]
            print(f"  {prop_name} → {best['label']} ({best['uri']})")
            align_g.add((PROP[prop_name], OWL.equivalentProperty, URIRef(best["uri"])))
        time.sleep(0.3)

    MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MAPPING_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["private_entity","external_uri","confidence"])
        w.writeheader(); w.writerows(mappings)

    ALIGNMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    align_g.serialize(destination=str(ALIGNMENT_FILE), format="turtle")
    print(f"\n✅ Mapping → {MAPPING_FILE}")
    print(f"✅ Alignment → {ALIGNMENT_FILE}")


if __name__ == "__main__":
    run_alignment()
