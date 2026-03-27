"""
Lab Session 5 - Exercise 8: SWRL vs KGE
SWRL rule: Film(?f) ^ partOfPhase(?f, Phase_3) ^ hasGenre(?f, Superhero_film)
           -> PhaseThreeSagaFilm(?f)
Analogy: vector(partOfPhase) + vector(Phase_3) ~= vector(Phase 3 film)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from pykeen.triples import TriplesFactory

RESULTS_DIR = Path("data/kge/results")
TRAIN_FILE = Path("data/kge/train.txt")
MODEL_FILE = RESULTS_DIR / "TransE" / "trained_model.pkl"


def cosine(vec_a, vec_b):
    return float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b) + 1e-9))


def get_entity_vec(model, fragment, entity_to_id):
    embeddings = model.entity_representations[0](indices=None).detach().cpu().numpy()
    matches = [key for key in entity_to_id if fragment.lower() in key.lower()]
    if not matches:
        return None, None
    return embeddings[entity_to_id[matches[0]]], matches[0]


def get_relation_vec(model, fragment, relation_to_id):
    embeddings = model.relation_representations[0](indices=None).detach().cpu().numpy()
    matches = [key for key in relation_to_id if fragment.lower() in key.lower()]
    if not matches:
        return None, None
    return embeddings[relation_to_id[matches[0]]], matches[0]


def run_comparison():
    print("=" * 60)
    print("Exercise 8 - SWRL Rule vs KGE Analogy")
    print("MCU Films Domain")
    print("=" * 60)

    if not MODEL_FILE.exists():
        print("Run train_kge.py first.")
        return

    model = torch.load(MODEL_FILE, map_location="cpu", weights_only=False)
    triples_factory = TriplesFactory.from_path(TRAIN_FILE)
    entity_to_id = triples_factory.entity_to_id
    relation_to_id = triples_factory.relation_to_id

    print("\nSWRL Rule:")
    print("  Film(?f) ^ partOfPhase(?f, Phase_3) ^ hasGenre(?f, Superhero_film) -> PhaseThreeSagaFilm(?f)")
    print("\nKGE TransE analogy:")
    print("  vector(partOfPhase) + vector(Phase_3) ~= vector(Avengers: Endgame or Infinity War)?")

    relation_vec, relation_label = get_relation_vec(model, "partOfPhase", relation_to_id)
    phase_vec, phase_label = get_entity_vec(model, "Phase_3", entity_to_id)
    film_vec, film_label = get_entity_vec(model, "Avengers_Endgame", entity_to_id)

    if relation_vec is None or phase_vec is None or film_vec is None:
        print("Required embeddings were not found in the trained model.")
        return

    composed = relation_vec + phase_vec
    similarity = cosine(composed, film_vec)
    print(f"\ncos(vector({relation_label}) + vector({phase_label}), vector({film_label})) = {similarity:.4f}")

    if similarity > 0.5:
        print("Interpretation: the embedding space loosely supports the Phase 3 grouping intuition.")
    elif similarity > 0.2:
        print("Interpretation: partial support only, which is common for approximate embeddings.")
    else:
        print("Interpretation: the analogy is weak, highlighting the gap between rules and embeddings.")

    print("\nDiscussion:")
    print("  SWRL is deterministic and directly interpretable.")
    print("  KGE is approximate and depends on repeated graph patterns.")
    print("  The MCU rule is easy for logic, but vector analogies capture it only indirectly.")


if __name__ == "__main__":
    run_comparison()
