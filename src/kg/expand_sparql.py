"""
Lab Session 4 - KB Expansion via SPARQL
Expansion depuis Wikidata — focus joueurs, clubs, blessures
Cible: 50 000 – 200 000 triplets
"""

import csv
import time
import requests
from pathlib import Path
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS

FOOTY = Namespace("http://example.org/football/")
WD    = Namespace("http://www.wikidata.org/entity/")
WDT   = Namespace("http://www.wikidata.org/prop/direct/")

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "FootballInjuryKGExpand/1.0 (educational)",
    "Accept":     "application/sparql-results+json",
}

MAPPING_FILE  = Path("data/entity_mapping.csv")
EXPANDED_FILE = Path("kg_artifacts/expanded.nt")
STATS_FILE    = Path("data/kb_statistics.txt")

# Propriétés Wikidata pertinentes pour les footballeurs
FOOTBALL_PROPS = [
    "P54",    # member of sports team (club)
    "P27",    # country of citizenship
    "P569",   # date of birth
    "P19",    # place of birth
    "P641",   # sport (football)
    "P1532",  # country for sport (national team)
    "P413",   # position played (gardien, attaquant…)
    "P118",   # league
    "P166",   # award received (Ballon d'Or etc.)
    "P1344",  # participant of (compétitions)
    "P286",   # head coach
    "P17",    # country (pour les clubs)
    "P159",   # headquarters location
    "P571",   # inception (fondation club)
    "P576",   # dissolved
    "P856",   # site officiel (à filtrer)
]

# Propriétés à exclure (binaires, admin, peu utiles pour KGE)
SKIP_PROPS = {"P18", "P856", "P973", "P935", "P1566", "P625", "P18", "P94"}


def sparql_query(query: str, retries=3) -> list:
    for attempt in range(retries):
        try:
            r = requests.get(
                WIKIDATA_SPARQL,
                params={"query": query, "format": "json"},
                headers=HEADERS, timeout=30,
            )
            if r.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"    Rate limit — wait {wait}s"); time.sleep(wait); continue
            r.raise_for_status()
            return r.json()["results"]["bindings"]
        except Exception as e:
            print(f"    [SPARQL error attempt {attempt+1}] {e}"); time.sleep(5)
    return []


def one_hop(qid: str) -> list:
    props = " ".join(f"wdt:{p}" for p in FOOTBALL_PROPS if p not in SKIP_PROPS)
    q = f"SELECT ?p ?o WHERE {{ wd:{qid} ?p ?o . VALUES ?p {{ {props} }} }} LIMIT 300"
    rows = sparql_query(q)
    return [(f"http://www.wikidata.org/entity/{qid}", r["p"]["value"], r["o"]["value"])
            for r in rows if "p" in r and "o" in r]


def expand_footballers_by_club(club_qid: str, limit=500) -> list:
    """Récupère tous les joueurs membres d'un club donné."""
    q = f"""
    SELECT ?player ?p ?o WHERE {{
      ?player wdt:P54 wd:{club_qid} .
      ?player ?p ?o .
      VALUES ?p {{ wdt:P27 wdt:P569 wdt:P413 wdt:P641 wdt:P1532 wdt:P166 wdt:P1344 }}
    }} LIMIT {limit}
    """
    rows = sparql_query(q)
    return [(r["player"]["value"], r["p"]["value"], r["o"]["value"])
            for r in rows if all(k in r for k in ["player","p","o"])]


def expand_by_property(prop: str, limit=8000) -> list:
    """Tous les triplets avec une propriété donnée."""
    q = f"SELECT ?s ?o WHERE {{ ?s wdt:{prop} ?o }} LIMIT {limit}"
    rows = sparql_query(q)
    prop_uri = f"http://www.wikidata.org/prop/direct/{prop}"
    return [(r["s"]["value"], prop_uri, r["o"]["value"])
            for r in rows if "s" in r and "o" in r]


def two_hop_injuries(qid: str) -> list:
    """2-hop depuis un joueur : ses clubs → propriétés des clubs."""
    q = f"""
    SELECT ?club ?p ?o WHERE {{
      wd:{qid} wdt:P54 ?club .
      ?club ?p ?o .
      FILTER(?p IN (wdt:P17, wdt:P118, wdt:P571, wdt:P159, wdt:P641))
    }} LIMIT 500
    """
    rows = sparql_query(q)
    return [(r["club"]["value"], r["p"]["value"], r["o"]["value"])
            for r in rows if all(k in r for k in ["club","p","o"])]


def is_useful(s, p, o) -> bool:
    for skip in SKIP_PROPS:
        if f"/{skip}" in p:
            return False
    return True


def run_expansion():
    g = Graph(); g.bind("wd", WD); g.bind("wdt", WDT)
    all_triples: set[tuple] = set()

    # Charger les QID alignés
    qids = []
    with open(MAPPING_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uri = row.get("external_uri", "")
            if "wikidata.org/entity/Q" in uri:
                qids.append(uri.split("/")[-1])

    print(f"Expanding from {len(qids)} aligned entities…")

    # ── 1-hop ─────────────────────────────────────────────────────────────────
    for i, qid in enumerate(qids):
        print(f"  [{i+1}/{len(qids)}] 1-hop {qid}")
        for t in one_hop(qid):
            if is_useful(*t): all_triples.add(t)
        time.sleep(0.5)
        if len(all_triples) > 120_000: break

    print(f"  After 1-hop: {len(all_triples):,}")

    # ── Expansion par propriété foot ───────────────────────────────────────────
    for prop in ["P54", "P413", "P1532", "P118", "P641"]:
        if len(all_triples) >= 170_000: break
        print(f"  Predicate expansion wdt:{prop}…")
        for t in expand_by_property(prop, 8000):
            if is_useful(*t): all_triples.add(t)
        time.sleep(1)

    print(f"  After predicate expansion: {len(all_triples):,}")

    # ── 2-hop clubs ────────────────────────────────────────────────────────────
    for qid in qids[:40]:
        if len(all_triples) >= 190_000: break
        for t in two_hop_injuries(qid):
            if is_useful(*t): all_triples.add(t)
        time.sleep(0.4)

    print(f"  After 2-hop: {len(all_triples):,}")

    # ── Build RDF ──────────────────────────────────────────────────────────────
    for s, p, o in all_triples:
        try:
            o_ref = URIRef(o) if o.startswith("http") else Literal(o)
            g.add((URIRef(s), URIRef(p), o_ref))
        except Exception:
            continue

    EXPANDED_FILE.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(EXPANDED_FILE), format="nt")

    stats = (f"KB Statistics\n=============\n"
             f"Triples:   {len(g):,}\nEntities:  {len(set(g.subjects())):,}\n"
             f"Relations: {len(set(g.predicates())):,}\nFile: {EXPANDED_FILE}\n")
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATS_FILE.write_text(stats)
    print(f"\n✅ Expanded KB → {EXPANDED_FILE}\n{stats}")


if __name__ == "__main__":
    run_expansion()
