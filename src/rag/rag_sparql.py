"""
Lab Session 6 - RAG over RDF/SPARQL
Chatbot for the MCU films knowledge graph.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import requests
from rdflib import Graph

TTL_FILE = Path("kg_artifacts/initial_kg.ttl")
OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "gemma:2b"
MAX_PREDICATES = 80
MAX_CLASSES = 40
SAMPLE_TRIPLES = 20


def ask_llm(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        return "[ERROR] Ollama not running. Start with: ollama serve"
    except Exception as exc:
        return f"[ERROR] {exc}"


def load_graph() -> Graph:
    graph = Graph()
    graph.parse(str(TTL_FILE), format="turtle")
    print(f"Loaded {len(graph):,} triples from {TTL_FILE}")
    return graph


def build_schema(graph: Graph) -> str:
    defaults = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "mcu": "http://example.org/mcu/",
        "prop": "http://example.org/mcu/property/",
    }
    namespaces = {prefix: str(namespace) for prefix, namespace in graph.namespace_manager.namespaces()}
    namespaces.update({key: value for key, value in defaults.items() if key not in namespaces})
    prefix_block = "\n".join(f"PREFIX {prefix}: <{uri}>" for prefix, uri in sorted(namespaces.items()))

    predicates = [str(row[0]) for row in graph.query(f"SELECT DISTINCT ?p WHERE {{ ?s ?p ?o }} LIMIT {MAX_PREDICATES}")]
    classes = [str(row[0]) for row in graph.query(f"SELECT DISTINCT ?c WHERE {{ ?s a ?c }} LIMIT {MAX_CLASSES}")]
    samples = [
        (str(row[0]), str(row[1]), str(row[2]))
        for row in graph.query(f"SELECT ?s ?p ?o WHERE {{ ?s ?p ?o }} LIMIT {SAMPLE_TRIPLES}")
    ]

    return f"""{prefix_block}

# Predicates
{chr(10).join(f'  - {predicate}' for predicate in predicates)}

# Classes
{chr(10).join(f'  - {cls}' for cls in classes)}

# Sample triples
{chr(10).join(f'  {subject}  {predicate}  {obj}' for subject, predicate, obj in samples)}"""


SPARQL_SYSTEM = """You are a SPARQL 1.1 generator for a Marvel Cinematic Universe knowledge graph.
The graph contains: Films, Directors, Actors, Characters, Genres, Phases, Franchise, Studio, Country.
Key properties: prop:directedBy, prop:hasCastMember, prop:portraysCharacter, prop:appearsInFilm,
prop:hasGenre, prop:partOfPhase, prop:partOfFranchise, prop:producedBy, prop:releaseYear.

Rules:
- Output ONLY a ```sparql ... ``` code block.
- Use ONLY prefixes and IRIs visible in the schema summary.
- Use rdfs:label for human-readable names.
- Prefer robust filters with LCASE when searching by names.
"""

CODE_RE = re.compile(r"```(?:sparql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_sparql(text: str) -> str:
    match = CODE_RE.search(text)
    return match.group(1).strip() if match else text.strip()


def template_sparql(question: str) -> str | None:
    q = question.lower().strip()
    templates = [
        (
            "who directed iron man",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX mcu: <http://example.org/mcu/>
PREFIX prop: <http://example.org/mcu/property/>
SELECT ?directorLabel WHERE {
  ?film rdf:type mcu:Film ;
        rdfs:label ?filmLabel ;
        prop:directedBy ?director .
  ?director rdfs:label ?directorLabel .
  FILTER(LCASE(STR(?filmLabel)) = "iron man")
}""",
        ),
        (
            "which films are in phase 3",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX mcu: <http://example.org/mcu/>
PREFIX prop: <http://example.org/mcu/property/>
SELECT ?filmLabel WHERE {
  ?film rdf:type mcu:Film ;
        rdfs:label ?filmLabel ;
        prop:partOfPhase ?phase .
  ?phase rdfs:label ?phaseLabel .
  FILTER(LCASE(STR(?phaseLabel)) = "phase 3")
}
ORDER BY ?filmLabel""",
        ),
        (
            "which actors appear in avengers: endgame",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX mcu: <http://example.org/mcu/>
PREFIX prop: <http://example.org/mcu/property/>
SELECT ?actorLabel WHERE {
  ?film rdf:type mcu:Film ;
        rdfs:label ?filmLabel ;
        prop:hasCastMember ?actor .
  ?actor rdfs:label ?actorLabel .
  FILTER(LCASE(STR(?filmLabel)) = "avengers: endgame")
}
ORDER BY ?actorLabel""",
        ),
        (
            "which films were directed by the russo brothers",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX mcu: <http://example.org/mcu/>
PREFIX prop: <http://example.org/mcu/property/>
SELECT DISTINCT ?filmLabel WHERE {
  ?film rdf:type mcu:Film ;
        rdfs:label ?filmLabel ;
        prop:directedBy ?director .
  ?director rdfs:label ?directorLabel .
  FILTER(LCASE(STR(?directorLabel)) = "anthony russo" || LCASE(STR(?directorLabel)) = "joe russo")
}
ORDER BY ?filmLabel""",
        ),
        (
            "which characters does robert downey jr. portray",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX mcu: <http://example.org/mcu/>
PREFIX prop: <http://example.org/mcu/property/>
SELECT DISTINCT ?characterLabel WHERE {
  ?actor rdf:type mcu:Actor ;
         rdfs:label ?actorLabel ;
         prop:portraysCharacter ?character .
  ?character rdfs:label ?characterLabel .
  FILTER(LCASE(STR(?actorLabel)) = "robert downey jr.")
}
ORDER BY ?characterLabel""",
        ),
        (
            "which films have the superhero film genre",
            """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX mcu: <http://example.org/mcu/>
PREFIX prop: <http://example.org/mcu/property/>
SELECT ?filmLabel WHERE {
  ?film rdf:type mcu:Film ;
        rdfs:label ?filmLabel ;
        prop:hasGenre ?genre .
  ?genre rdfs:label ?genreLabel .
  FILTER(LCASE(STR(?genreLabel)) = "superhero film")
}
ORDER BY ?filmLabel""",
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


def run_sparql(graph: Graph, query: str):
    result = graph.query(query)
    vars_ = [str(var) for var in result.vars]
    rows = [tuple(str(cell) for cell in row) for row in result]
    return vars_, rows


def repair_sparql(schema, question, bad_query, error) -> str:
    prompt = f"""Fix this broken SPARQL query using the schema below.
Return ONLY the corrected ```sparql block.

SCHEMA:
{schema}

QUESTION: {question}

FAILED QUERY:
{bad_query}

ERROR: {error}
"""
    return extract_sparql(ask_llm(prompt))


def answer_rag(graph, schema, question, try_repair=True) -> dict:
    query = generate_sparql(question, schema)
    try:
        vars_, rows = run_sparql(graph, query)
        return {"query": query, "vars": vars_, "rows": rows, "repaired": False, "error": None}
    except Exception as exc:
        if not try_repair:
            return {"query": query, "vars": [], "rows": [], "repaired": False, "error": str(exc)}
        repaired = repair_sparql(schema, question, query, str(exc))
        try:
            vars_, rows = run_sparql(graph, repaired)
            return {"query": repaired, "vars": vars_, "rows": rows, "repaired": True, "error": None}
        except Exception as second_exc:
            return {"query": repaired, "vars": [], "rows": [], "repaired": True, "error": str(second_exc)}


def answer_baseline(question: str) -> str:
    return ask_llm(f"Answer this question about Marvel Cinematic Universe films:\n\n{question}")


def pretty(result: dict):
    if result.get("error"):
        print(f"  [ERROR] {result['error']}")
    print(f"\n  [SPARQL {'repaired ' if result['repaired'] else ''}generated]")
    print(f"  {result['query'][:400]}{'...' if len(result['query']) > 400 else ''}")
    rows = result.get("rows", [])
    if not rows:
        print("\n  [No results]")
        return
    print(f"\n  [Results - {len(rows)} row(s)]")
    print("  " + " | ".join(result.get("vars", [])))
    for row in rows[:10]:
        print("  " + " | ".join(row))


EVAL_QUESTIONS = [
    "Who directed Iron Man?",
    "Which films are in Phase 3?",
    "Which actors appear in Avengers: Endgame?",
    "Which films were directed by the Russo brothers?",
    "Which characters does Robert Downey Jr. portray?",
    "Which films have the superhero film genre?",
]


def run_evaluation(graph, schema, output=Path("data/rag_evaluation.json")):
    print("\n" + "=" * 60)
    print("RAG EVALUATION - MCU FILMS KB")
    print("=" * 60)
    results = []
    for question in EVAL_QUESTIONS:
        print(f"\nQ {question}")
        baseline = answer_baseline(question)
        rag = answer_rag(graph, schema, question)
        rag_preview = " | ".join(" ".join(row) for row in rag["rows"][:3]) if rag["rows"] else "No results"
        print(f"  Baseline: {baseline[:120]}...")
        print(f"  RAG:      {rag_preview[:120]}")
        results.append(
            {
                "question": question,
                "baseline_answer": baseline,
                "rag_query": rag["query"],
                "rag_rows": rag["rows"][:5],
                "repaired": rag["repaired"],
                "error": rag["error"],
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as file_obj:
        json.dump(results, file_obj, indent=2, ensure_ascii=False)
    print(f"\nOK Evaluation -> {output}")


def run_evaluation_cli():
    graph = load_graph()
    schema = build_schema(graph)
    run_evaluation(graph, schema)


if __name__ == "__main__":
    import sys

    graph = load_graph()
    schema = build_schema(graph)

    if len(sys.argv) > 1 and sys.argv[1] == "--eval":
        run_evaluation(graph, schema)
    else:
        print("\nMCU Films Knowledge Graph - RAG Chatbot")
        print("Type 'eval' to run evaluation, 'quit' to exit\n")
        while True:
            try:
                question = input("Question: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not question:
                continue
            if question.lower() == "quit":
                break
            if question.lower() == "eval":
                run_evaluation(graph, schema)
                continue

            print("\n--- Baseline (no RAG) ---")
            print(answer_baseline(question))
            print("\n--- SPARQL RAG ---")
            pretty(answer_rag(graph, schema, question))
            print()
