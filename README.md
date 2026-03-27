# MCU Films and Directors Knowledge Graph

Course project for **Web Mining & Semantics** on a simpler and more stable domain:
**Marvel Cinematic Universe films, directors, cast, characters, genres, and phases**.

This repository implements the full pipeline requested in the grading guide:
- crawling and cleaning
- information extraction
- RDF knowledge graph construction
- entity and predicate alignment
- KB expansion
- SWRL reasoning
- KGE preparation, training, and evaluation
- RAG over RDF/SPARQL with a local LLM

## Repository Structure

```text
project/
|-- src/
|   |-- crawl/
|   |-- domain/
|   |-- ie/
|   |-- kg/
|   |-- reason/
|   |-- kge/
|   `-- rag/
|-- data/
|   `-- kge/
|-- kg_artifacts/
|-- reports/
|-- run_pipeline.py
|-- requirements.txt
`-- README.md
```

Important generated artifacts:
- `kg_artifacts/ontology.ttl`
- `kg_artifacts/initial_kg.ttl`
- `kg_artifacts/alignment.ttl`
- `kg_artifacts/expanded.nt`
- `kg_artifacts/mcu_reasoned.owl`
- `data/kb_statistics.txt`
- `data/kge/train.txt`
- `data/kge/valid.txt`
- `data/kge/test.txt`
- `data/rag_evaluation.json`

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Reproducibility and Data

The project is intentionally **deterministic and offline-friendly**.

- The initial corpus is generated locally from a curated MCU dataset.
- The alignment step uses deterministic DBpedia mappings.
- The expansion step is schema-driven and local, so it does not depend on public SPARQL endpoints during grading.
- No external large download is required to regenerate the data produced by the pipeline.

If the generated files are missing, simply rerun the corresponding pipeline steps.

## How to Run Each Module

Run the whole pipeline:

```powershell
python run_pipeline.py
```

Run individual steps:

```powershell
python run_pipeline.py --step 1      # crawling MCU corpus
python run_pipeline.py --step 2      # information extraction
python run_pipeline.py --step 3      # RDF ontology + initial KG
python run_pipeline.py --step 4      # entity alignment
python run_pipeline.py --step 5      # KB expansion
python run_pipeline.py --step 6      # KGE data preparation
python run_pipeline.py --step 7      # KGE training and evaluation
python run_pipeline.py --step 8      # SWRL reasoning
python run_pipeline.py --step 9      # SWRL vs KGE comparison
python run_pipeline.py --step 10     # RAG evaluation
```

Run modules directly if needed:

```powershell
python src/crawl/crawler.py
python src/ie/ner_extractor.py
python src/kg/build_kg.py
python src/kg/align_entities.py
python src/kg/expand_sparql.py
python src/kge/prepare_kge_data.py
python src/kge/train_kge.py
python src/reason/swrl_reasoning.py
python src/kge/swrl_vs_kge.py
python src/rag/rag_sparql.py --eval
```

## How to Run the RAG Demo

Install and start Ollama locally:

```powershell
ollama pull gemma:2b
ollama serve
```

Then start the CLI demo:

```powershell
python src/rag/rag_sparql.py
```

Example questions:
- `Who directed Iron Man?`
- `Which films are in Phase 3?`
- `Which actors appear in Avengers: Endgame?`
- `Which films were directed by the Russo brothers?`
- `Which characters does Robert Downey Jr. portray?`

## Hardware Requirements

Minimum:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 4 GB free
- GPU: not required

Recommended:
- CPU: 6 to 8 cores
- RAM: 16 GB
- Disk: 8 GB free
- GPU: optional

Observed setup notes:
- KGE training runs on CPU if no CUDA device is available.
- Ollama with a small model such as `gemma:2b` is sufficient for the RAG demo.

## Current Results

Current generated statistics:
- Initial KG: `1,155` triples
- Expanded KB: `122,392` triples
- Expanded entities: `7,992`
- Expanded relations: `70`
- Clean KGE triples: `99,769`
- KGE entities: `8,000`
- KGE relations: `64`

Main KGE comparison:

| Model | MRR | Hits@1 | Hits@3 | Hits@10 |
|------|-----:|--------:|--------:|---------:|
| TransE | 0.1193 | 0.0119 | 0.1958 | 0.2820 |
| DistMult | 0.0102 | 0.0041 | 0.0099 | 0.0185 |

## Screenshot

If the repository contains an `images/` folder, a representative project screenshot can be included in GitHub markdown like this:

```markdown
![RAG evaluation screenshot](images/step10.png)
```

For the final report, the LaTeX source is available in:
- `reports/final_report.tex`

## Notes

- Warnings about CPU-only training are expected if no GPU is available.
- OWLReady2 may print Java reasoner attempts; a manual fallback is implemented when Java is unavailable.
- The project keeps the full lab logic while choosing a domain that is much easier to align, expand, and evaluate than a live sports dataset.
