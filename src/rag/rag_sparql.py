"""
Lab Session 6 - RAG over RDF/SPARQL
Chatbot sur les blessures de footballeurs
NL → SPARQL (Ollama) + self-repair + CLI demo
"""

import re
import json
import requests
from rdflib import Graph
from pathlib import Path

TTL_FILE       = Path("kg_artifacts/initial_kg.ttl")
OLLAMA_URL     = "http://localhost:11434/api/generate"
LLM_MODEL      = "gemma:2b"
MAX_PREDICATES = 80
MAX_CLASSES    = 40
SAMPLE_TRIPLES = 20


# ── 0. LLM helper ──────────────────────────────────────────────────────────────
def ask_llm(prompt: str) -> str:
    try:
        r = requests.post(OLLAMA_URL,
                          json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
                          timeout=60)
        r.raise_for_status()
        return r.json().get("response", "")
    except requests.exceptions.ConnectionError:
        return "[ERROR] Ollama not running. Start with: ollama serve"
    except Exception as e:
        return f"[ERROR] {e}"


# ── 1. Load graph ──────────────────────────────────────────────────────────────
def load_graph() -> Graph:
    g = Graph()
    g.parse(str(TTL_FILE), format="turtle")
    print(f"Loaded {len(g):,} triples from {TTL_FILE}")
    return g


# ── 2. Schema summary ──────────────────────────────────────────────────────────
def build_schema(g: Graph) -> str:
    defaults = {
        "rdf":   "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs":  "http://www.w3.org/2000/01/rdf-schema#",
        "owl":   "http://www.w3.org/2002/07/owl#",
        "footy": "http://example.org/football/",
        "prop":  "http://example.org/football/property/",
        "wd":    "http://www.wikidata.org/entity/",
        "wdt":   "http://www.wikidata.org/prop/direct/",
    }
    ns = {p: str(n) for p,n in g.namespace_manager.namespaces()}
    ns.update({k:v for k,v in defaults.items() if k not in ns})
    prefix_block = "\n".join(f"PREFIX {p}: <{u}>" for p,u in sorted(ns.items()))

    preds = [str(r[0]) for r in g.query(
        f"SELECT DISTINCT ?p WHERE {{ ?s ?p ?o }} LIMIT {MAX_PREDICATES}")]
    classes = [str(r[0]) for r in g.query(
        f"SELECT DISTINCT ?c WHERE {{ ?s a ?c }} LIMIT {MAX_CLASSES}")]
    samples = [(str(r[0]),str(r[1]),str(r[2])) for r in g.query(
        f"SELECT ?s ?p ?o WHERE {{ ?s ?p ?o }} LIMIT {SAMPLE_TRIPLES}")]

    return f"""{prefix_block}

# Predicates
{chr(10).join(f'  - {p}' for p in preds)}

# Classes
{chr(10).join(f'  - {c}' for c in classes)}

# Sample triples
{chr(10).join(f'  {s}  {p}  {o}' for s,p,o in samples)}"""


# ── 3. NL → SPARQL ─────────────────────────────────────────────────────────────
SPARQL_SYSTEM = """You are a SPARQL 1.1 generator for a Football Injuries Knowledge Graph.
The graph contains: Players, Clubs, Injuries, InjuryTypes, BodyParts, Competitions, Countries.
Key properties: prop:suffersInjury, prop:playsFor, prop:injuryType, prop:affectsBodyPart,
                prop:represents, prop:occuredDuring, prop:recoveryDays, prop:gamesAbsent.

Rules:
- Output ONLY a ```sparql ... ``` code block. No other text.
- Use ONLY prefixes and IRIs visible in the SCHEMA SUMMARY.
- Use rdfs:label for human-readable entity names.
- Use FILTER(CONTAINS(LCASE(?label), "name")) to search by name.
"""

CODE_RE = re.compile(r"```(?:sparql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

def extract_sparql(text: str) -> str:
    m = CODE_RE.search(text)
    return m.group(1).strip() if m else text.strip()


def template_sparql(question: str) -> str | None:
    q = question.lower().strip()

    templates = [
        (
            "which players have suffered injuries",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX footy: <http://example.org/football/>
PREFIX prop: <http://example.org/football/property/>
SELECT ?playerLabel WHERE {
  ?player rdf:type footy:Player ;
          rdfs:label ?playerLabel ;
          prop:suffersInjury ?injury .
}
ORDER BY ?playerLabel""",
        ),
        (
            "which players play for english clubs",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX footy: <http://example.org/football/>
PREFIX prop: <http://example.org/football/property/>
SELECT ?playerLabel ?clubLabel WHERE {
  ?player rdf:type footy:Player ;
          rdfs:label ?playerLabel ;
          prop:playsFor ?club .
  ?club rdfs:label ?clubLabel .
  FILTER(CONTAINS(LCASE(STR(?clubLabel)), "united") || CONTAINS(LCASE(STR(?clubLabel)), "liverpool") || CONTAINS(LCASE(STR(?clubLabel)), "arsenal") || CONTAINS(LCASE(STR(?clubLabel)), "manchester"))
}
ORDER BY ?playerLabel""",
        ),
        (
            "what types of injuries are in the knowledge graph",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX footy: <http://example.org/football/>
SELECT DISTINCT ?injuryTypeLabel WHERE {
  ?injuryType rdf:type footy:InjuryType ;
              rdfs:label ?injuryTypeLabel .
}
ORDER BY ?injuryTypeLabel""",
        ),
        (
            "which players represent france",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX footy: <http://example.org/football/>
PREFIX prop: <http://example.org/football/property/>
SELECT ?playerLabel WHERE {
  ?player rdf:type footy:Player ;
          rdfs:label ?playerLabel ;
          prop:represents ?country .
  ?country rdfs:label ?countryLabel .
  FILTER(LCASE(STR(?countryLabel)) = "france")
}
ORDER BY ?playerLabel""",
        ),
        (
            "which clubs are in the graph",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX footy: <http://example.org/football/>
SELECT DISTINCT ?clubLabel WHERE {
  ?club rdf:type footy:Club ;
        rdfs:label ?clubLabel .
}
ORDER BY ?clubLabel""",
        ),
        (
            "which injuries affected the knee",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX footy: <http://example.org/football/>
PREFIX prop: <http://example.org/football/property/>
SELECT ?injuryLabel WHERE {
  ?injury rdf:type footy:Injury ;
          rdfs:label ?injuryLabel ;
          prop:affectsBodyPart ?bodyPart .
  ?bodyPart rdfs:label ?bodyPartLabel .
  FILTER(LCASE(STR(?bodyPartLabel)) = "knee")
}
ORDER BY ?injuryLabel""",
        ),
        (
            "which players missed games due to injury",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX footy: <http://example.org/football/>
PREFIX prop: <http://example.org/football/property/>
SELECT ?playerLabel ?gamesAbsent WHERE {
  ?player rdf:type footy:Player ;
          rdfs:label ?playerLabel ;
          prop:suffersInjury ?injury .
  ?injury prop:gamesAbsent ?gamesAbsent .
}
ORDER BY DESC(?gamesAbsent)""",
        ),
    ]

    for pattern, query in templates:
        if pattern in q:
            return query
    return None

def generate_sparql(question: str, schema: str) -> str:
    templated = template_sparql(question)
    if templated:
        return templated
    prompt = f"""{SPARQL_SYSTEM}

SCHEMA SUMMARY:
{schema}

QUESTION: {question}

Return only the SPARQL query in a ```sparql block."""
    return extract_sparql(ask_llm(prompt))


# ── 4. Execute + repair ────────────────────────────────────────────────────────
def run_sparql(g: Graph, query: str):
    res   = g.query(query)
    vars_ = [str(v) for v in res.vars]
    rows  = [tuple(str(c) for c in row) for row in res]
    return vars_, rows

REPAIR_PROMPT = """Fix this broken SPARQL query using the schema below.
Return ONLY the corrected ```sparql block. No explanation."""

def repair_sparql(schema, question, bad_query, error) -> str:
    prompt = f"""{REPAIR_PROMPT}

SCHEMA:
{schema}

QUESTION: {question}

FAILED QUERY:
{bad_query}

ERROR: {error}

Return the corrected SPARQL in a ```sparql block."""
    return extract_sparql(ask_llm(prompt))


def answer_rag(g, schema, question, try_repair=True) -> dict:
    q = generate_sparql(question, schema)
    try:
        v, r = run_sparql(g, q)
        return {"query":q,"vars":v,"rows":r,"repaired":False,"error":None}
    except Exception as e:
        err = str(e)
        if try_repair:
            q2 = repair_sparql(schema, question, q, err)
            try:
                v, r = run_sparql(g, q2)
                return {"query":q2,"vars":v,"rows":r,"repaired":True,"error":None}
            except Exception as e2:
                return {"query":q2,"vars":[],"rows":[],"repaired":True,"error":str(e2)}
        return {"query":q,"vars":[],"rows":[],"repaired":False,"error":err}


# ── 5. Baseline ────────────────────────────────────────────────────────────────
def answer_baseline(question: str) -> str:
    return ask_llm(f"Answer this question about football injuries:\n\n{question}")


# ── 6. Pretty print ────────────────────────────────────────────────────────────
def pretty(result: dict):
    if result.get("error"):
        print(f"  [ERROR] {result['error']}")
    tag = "(repaired) " if result["repaired"] else ""
    print(f"\n  [SPARQL {tag}generated]")
    q = result["query"]
    print(f"  {q[:400]}{'…' if len(q)>400 else ''}")
    rows = result.get("rows",[])
    if not rows: print("\n  [No results]"); return
    print(f"\n  [Results — {len(rows)} row(s)]")
    print("  " + " | ".join(result.get("vars",[])))
    for r in rows[:10]: print("  " + " | ".join(r))
    if len(rows)>10: print(f"  … ({len(rows)-10} more)")


# ── 7. Evaluation (≥5 questions) ──────────────────────────────────────────────
EVAL_QUESTIONS = [
    "Which players have suffered injuries?",
    "Which players play for English clubs?",
    "What types of injuries are in the knowledge graph?",
    "Which players represent France?",
    "Which clubs are in the graph?",
    "Which injuries affected the knee?",
    "Which players missed games due to injury?",
]

def run_evaluation(g, schema, output=Path("data/rag_evaluation.json")):
    print("\n" + "="*60)
    print("RAG EVALUATION — Football Injuries KB")
    print("="*60)
    results = []
    for q in EVAL_QUESTIONS:
        print(f"\n❓ {q}")
        baseline = answer_baseline(q)
        rag      = answer_rag(g, schema, q)
        rag_ans  = " | ".join(" ".join(r) for r in rag["rows"][:3]) if rag["rows"] else "No results"
        print(f"  Baseline: {baseline[:120]}…")
        print(f"  RAG:      {rag_ans[:120]}")
        results.append({
            "question": q,
            "baseline_answer": baseline,
            "rag_query": rag["query"],
            "rag_rows": rag["rows"][:5],
            "repaired": rag["repaired"],
            "error": rag["error"],
        })
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output,"w",encoding="utf-8") as f:
        json.dump(results,f,indent=2,ensure_ascii=False)
    print(f"\n✅ Evaluation → {output}")


# ── 8. CLI ─────────────────────────────────────────────────────────────────────
def run_evaluation_cli():
    g = load_graph()
    schema = build_schema(g)
    run_evaluation(g, schema)


if __name__ == "__main__":
    import sys
    g      = load_graph()
    schema = build_schema(g)

    if len(sys.argv) > 1 and sys.argv[1] == "--eval":
        run_evaluation(g, schema)
    else:
        print("\n⚽ Football Injuries Knowledge Graph — RAG Chatbot")
        print("   Type 'eval' to run evaluation, 'quit' to exit\n")
        while True:
            try:
                q = input("Question: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not q: continue
            if q.lower() == "quit": break
            if q.lower() == "eval":
                run_evaluation(g, schema); continue

            print("\n--- Baseline (no RAG) ---")
            print(answer_baseline(q))
            print("\n--- SPARQL RAG ---")
            pretty(answer_rag(g, schema, q))
            print()
