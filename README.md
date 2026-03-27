# MCU Films and Directors Knowledge Graph

Suggested repository name: `mcu-films-kg`

Course project for **Web Mining & Semantics** built around a simpler, more stable theme:
**Marvel Cinematic Universe films, directors, cast, characters, genres, and phases**.

The repository keeps the full lab pipeline:
- data acquisition and information extraction
- RDF knowledge graph construction
- entity alignment
- KB expansion
- SWRL reasoning
- KGE preparation and training
- RAG over RDF/SPARQL

The whole project is designed to be **deterministic and reproducible offline**.  
Instead of depending on fragile live crawling or public SPARQL endpoints during execution, it uses a curated MCU corpus and a local schema-driven expansion strategy.

## Project Structure

```text
project/
|-- src/
|   |-- crawl/
|   |   `-- crawler.py
|   |-- domain/
|   |   `-- mcu_data.py
|   |-- ie/
|   |   `-- ner_extractor.py
|   |-- kg/
|   |   |-- build_kg.py
|   |   |-- align_entities.py
|   |   `-- expand_sparql.py
|   |-- reason/
|   |   `-- swrl_reasoning.py
|   |-- kge/
|   |   |-- prepare_kge_data.py
|   |   |-- train_kge.py
|   |   `-- swrl_vs_kge.py
|   `-- rag/
|       `-- rag_sparql.py
|-- data/
|-- kg_artifacts/
|-- run_pipeline.py
|-- requirements.txt
`-- README.md
```

## Domain

Core entities:
- `Film`
- `Director`
- `Actor`
- `Character`
- `Genre`
- `Phase`
- `Franchise`
- `Studio`
- `Country`

Core relations:
- `directedBy`
- `hasCastMember`
- `portraysCharacter`
- `appearsInFilm`
- `hasGenre`
- `partOfPhase`
- `partOfFranchise`
- `producedBy`
- `hasCountry`
- `releaseDate`
- `releaseYear`
- `followsFilm`

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Optional for the RAG part:

```bash
ollama pull gemma:2b
ollama serve
```

## Run the Pipeline

Full pipeline:

```bash
python run_pipeline.py
```

Specific steps:

```bash
python run_pipeline.py --step 1      # MCU corpus generation
python run_pipeline.py --step 2      # information extraction
python run_pipeline.py --step 3      # RDF ontology + initial KG
python run_pipeline.py --step 4      # entity alignment
python run_pipeline.py --step 5      # KB expansion
python run_pipeline.py --step 6      # KGE train/valid/test splits
python run_pipeline.py --step 7      # KGE training
python run_pipeline.py --step 8      # SWRL reasoning
python run_pipeline.py --step 9      # SWRL vs KGE comparison
python run_pipeline.py --step 10     # RAG evaluation
```

## Current KB Statistics

After running steps 1 to 6:
- initial KG: `1,155` triples
- expanded KB: `122,392` triples
- expanded entities: `7,992`
- expanded relations: `70`
- clean KGE triples: `99,769`

These values satisfy the target scale expected in the labs.

## Main Outputs

Generated data:
- `data/crawler_output.jsonl`
- `data/extracted_knowledge.csv`
- `data/extracted_relations.csv`
- `data/entity_mapping.csv`
- `data/kb_statistics.txt`
- `data/kge/train.txt`
- `data/kge/valid.txt`
- `data/kge/test.txt`

KG artifacts:
- `kg_artifacts/ontology.ttl`
- `kg_artifacts/initial_kg.ttl`
- `kg_artifacts/alignment.ttl`
- `kg_artifacts/expanded.nt`
- `kg_artifacts/mcu_reasoned.owl`

## RAG Demo

CLI mode:

```bash
python src/rag/rag_sparql.py
```

Batch evaluation:

```bash
python src/rag/rag_sparql.py --eval
```

Example questions:
- `Who directed Iron Man?`
- `Which films are in Phase 3?`
- `Which actors appear in Avengers: Endgame?`
- `Which films were directed by the Russo brothers?`
- `Which characters does Robert Downey Jr. portray?`

## Notes

- The project is intentionally stable and coursework-friendly.
- Live crawling and live SPARQL expansion were avoided because they make grading and reruns unreliable.
- The SWRL scripts include a manual fallback when a Java reasoner is unavailable.
