# ⚽ Football Player Injuries — Knowledge Graph Project

**Cours** : Web Mining & Semantics  
**Domaine** : Blessures de joueurs de football professionnels  
**Sources** : Wikipedia (crawling) + Wikidata (expansion SPARQL)

---

## Structure du projet

```
project/
├── src/
│   ├── crawl/        crawler.py           – Crawl Wikipedia (joueurs blessés)
│   ├── ie/           ner_extractor.py     – NER spaCy + extraction relations
│   ├── kg/           build_kg.py          – Construction KG RDF + ontologie
│   │                 align_entities.py    – Alignement entités → Wikidata
│   │                 expand_sparql.py     – Expansion SPARQL (50k–200k triplets)
│   ├── reason/       swrl_reasoning.py    – Règles SWRL (family.owl + KB foot)
│   ├── kge/          prepare_kge_data.py  – Splits train/val/test
│   │                 train_kge.py         – TransE + DistMult, MRR, t-SNE
│   │                 swrl_vs_kge.py       – Exercice 8 : analogie vectorielle
│   └── rag/          rag_sparql.py        – RAG NL→SPARQL + self-repair + CLI
├── data/
│   ├── crawler_output.jsonl
│   ├── extracted_knowledge.csv
│   ├── extracted_relations.csv
│   ├── entity_mapping.csv
│   └── kge/   train.txt · valid.txt · test.txt · entity2id.txt · relation2id.txt
├── kg_artifacts/
│   ├── ontology.ttl        – Ontologie OWL (classes + propriétés)
│   ├── initial_kg.ttl      – KG initial (entités extraites + crawl)
│   ├── alignment.ttl       – owl:sameAs + owl:equivalentProperty
│   └── expanded.nt         – KB étendu via SPARQL (50k–200k triplets)
├── run_pipeline.py
├── requirements.txt
└── README.md
```

---

## Ontologie — Domaine Blessures Football

**Classes :** `Player`, `Club`, `Injury`, `InjuryType`, `BodyPart`, `Competition`, `Country`, `Season`, `MedicalStaff`

**Sous-classes d'InjuryType :** `ACLRupture`, `HamstringStrain`, `AchillesRupture`, `Fracture`, `MetatarsalFracture`, `Concussion`, `MuscleTear`, `MeniscusTear`

**Propriétés clés :** `suffersInjury`, `injuryType`, `affectsBodyPart`, `playsFor`, `occuredDuring`, `recoveryDays`, `gamesAbsent`, `represents`

---

## Installation

```bash
# 1. Cloner le repo
git clone <votre-repo>
cd project

# 2. Environnement virtuel
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Dépendances
pip install -r requirements.txt
python -m spacy download en_core_web_trf

# 4. Ollama (pour le RAG)
# Installer Ollama : https://ollama.com/
ollama pull gemma:2b
```

---

## Exécution

### Pipeline complet
```bash
python run_pipeline.py
```

### Étapes individuelles
```bash
python run_pipeline.py --step 1      # Crawling Wikipedia
python run_pipeline.py --step 2      # NER + extraction relations
python run_pipeline.py --step 3      # Construction KG RDF
python run_pipeline.py --step 4      # Alignement Wikidata
python run_pipeline.py --step 5      # Expansion SPARQL
python run_pipeline.py --step 6      # Préparation données KGE
python run_pipeline.py --step 7      # Entraînement TransE + DistMult
python run_pipeline.py --step 8      # Raisonnement SWRL
python run_pipeline.py --step 9      # Comparaison SWRL vs KGE
python run_pipeline.py --step 10     # Évaluation RAG
```

### Demo RAG interactive
```bash
# Démarrer Ollama
ollama serve

# Lancer le chatbot
python src/rag/rag_sparql.py

# Lancer l'évaluation (≥5 questions)
python src/rag/rag_sparql.py --eval
```

**Exemple d'interaction :**
```
Question: Which players suffered an ACL injury?
--- Baseline (no RAG) ---
I don't have specific information about...
--- SPARQL RAG ---
SELECT ?player ?label WHERE {
  ?player a footy:Player .
  ?player footy:suffersInjury ?inj .
  ?inj a footy:ACLRupture .
  ?player rdfs:label ?label .
}
[Results]
player | label
http://example.org/football/Messi | Messi
```

---

## Règles SWRL

```
# Règle 1 — sur family.owl
Person(?p) ∧ hasAge(?p, ?a) ∧ swrlb:greaterThan(?a, 60) → OldPerson(?p)

# Règle 2 — sur le KB foot (HighRiskPlayer)
Player(?p) ∧ suffersInjury(?p,?i) ∧ ACLRupture(?i) → HighRiskPlayer(?p)

# Règle 3 — sur le KB foot (LongTermInjuredPlayer)
Player(?p) ∧ suffersInjury(?p,?i) ∧ recoveryDays(?i,?d) ∧ ?d > 90
  → LongTermInjuredPlayer(?p)
```

---

## Configuration matérielle requise

| Composant | Minimum | Recommandé |
|-----------|---------|------------|
| RAM | 8 Go | 16 Go |
| CPU | 4 cœurs | 8 cœurs |
| Disque | 5 Go | 10 Go |
| GPU | Non requis | Accélère l'entraînement KGE |

KGE : ~20 min sur CPU pour 100 epochs sur 100k triplets.

---

## Checklist soumission

- [x] Crawler + robots.txt + JSONL
- [x] NER spaCy (en_core_web_trf) + CSV relations
- [x] Ontologie RDF/OWL (classes, propriétés, sous-classes blessures)
- [x] Entity linking Wikidata (owl:sameAs) + mapping CSV
- [x] Alignement prédicats (owl:equivalentProperty)
- [x] Expansion SPARQL (1-hop, prédicats, 2-hop)
- [x] SWRL family.owl (age > 60)
- [x] SWRL KB foot (HighRiskPlayer, LongTermInjuredPlayer)
- [x] KGE TransE + DistMult
- [x] MRR, Hits@1/3/10, sensibilité taille
- [x] t-SNE + voisins proches
- [x] RAG NL→SPARQL + self-repair
- [x] Évaluation baseline vs RAG (≥7 questions)
- [x] README + requirements.txt + .gitignore
