"""
Lab Session 5 - KGE Training & Evaluation
Models: TransE, DistMult
Metrics: MRR, Hits@1/3/10
Analyses: nearest neighbours, t-SNE, KB size sensitivity
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory
from sklearn.manifold import TSNE

np.random.seed(42)

TRAIN_FILE = Path("data/kge/train.txt")
VALID_FILE = Path("data/kge/valid.txt")
TEST_FILE = Path("data/kge/test.txt")
MAPPING_FILE = Path("data/entity_mapping.csv")
RESULTS_DIR = Path("data/kge/results")
PLOTS_DIR = Path("data/kge/plots")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = {
    "embedding_dim": 64,
    "learning_rate": 0.001,
    "batch_size": 512,
    "num_epochs": 5,
    "size_sensitivity_epochs": 3,
}


def load_triples():
    tf_train = TriplesFactory.from_path(TRAIN_FILE)
    tf_valid = TriplesFactory.from_path(
        VALID_FILE,
        entity_to_id=tf_train.entity_to_id,
        relation_to_id=tf_train.relation_to_id,
    )
    tf_test = TriplesFactory.from_path(
        TEST_FILE,
        entity_to_id=tf_train.entity_to_id,
        relation_to_id=tf_train.relation_to_id,
    )
    return tf_train, tf_valid, tf_test


def extract_realistic_metrics(metric_dict):
    realistic = metric_dict.get("both", {}).get("realistic", {})
    return {
        "MRR": realistic.get("inverse_harmonic_mean_rank", 0.0),
        "Hits@1": realistic.get("hits_at_1", 0.0),
        "Hits@3": realistic.get("hits_at_3", 0.0),
        "Hits@10": realistic.get("hits_at_10", 0.0),
    }


def load_entity_labels():
    labels = {}
    if not MAPPING_FILE.exists():
        return labels
    with open(MAPPING_FILE, encoding="utf-8") as file_obj:
        for row in csv.DictReader(file_obj):
            external_uri = row.get("external_uri", "")
            label = row.get("private_entity", "").strip()
            if external_uri.startswith("http") and label:
                labels[external_uri] = label
    return labels


def train_model(name, tf_train, tf_valid, tf_test, epochs=None, save_as=None):
    epoch_count = epochs or CONFIG["num_epochs"]
    print(
        f"\n{'=' * 55}\n"
        f"Training {name} (dim={CONFIG['embedding_dim']}, epochs={epoch_count})\n"
        f"{'=' * 55}"
    )
    result = pipeline(
        model=name,
        training=tf_train,
        validation=tf_valid,
        testing=tf_test,
        model_kwargs={"embedding_dim": CONFIG["embedding_dim"]},
        optimizer="Adam",
        optimizer_kwargs={"lr": CONFIG["learning_rate"]},
        training_kwargs={"num_epochs": epoch_count, "batch_size": CONFIG["batch_size"]},
        negative_sampler="basic",
        evaluator="RankBasedEvaluator",
        evaluator_kwargs={"filtered": True},
        random_seed=42,
        use_testing_data=True,
    )
    scores = extract_realistic_metrics(result.metric_results.to_dict())
    flat = {"model": name, "epochs": epoch_count, **scores}
    output_dir = RESULTS_DIR / (save_as or name)
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(result.model, output_dir / "trained_model.pkl")
    with open(output_dir / "metrics.json", "w", encoding="utf-8") as file_obj:
        json.dump(flat, file_obj, indent=2)
    print(f"Saved model to: {output_dir}")
    return flat, result


def experiment_comparison(tf_train, tf_valid, tf_test):
    results = []
    trained = {}
    for model_name in ["TransE", "DistMult"]:
        flat, result = train_model(model_name, tf_train, tf_valid, tf_test, save_as=model_name)
        results.append(flat)
        trained[model_name] = result
    with open(RESULTS_DIR / "comparison.json", "w", encoding="utf-8") as file_obj:
        json.dump(results, file_obj, indent=2)
    return results, trained


def experiment_size_sensitivity(tf_train, tf_valid, tf_test):
    target_sizes = [20_000, 50_000, len(tf_train.triples)]
    seen = set()
    results = []
    for size in target_sizes:
        actual = min(size, len(tf_train.triples))
        if actual in seen:
            continue
        seen.add(actual)

        print(f"\nSubsampling -> {actual:,} triples")
        if actual < len(tf_train.triples):
            indices = np.random.choice(len(tf_train.triples), actual, replace=False)
            subset = tf_train.triples[indices]
            tf_subset = TriplesFactory.from_labeled_triples(
                subset,
                entity_to_id=tf_train.entity_to_id,
                relation_to_id=tf_train.relation_to_id,
            )
        else:
            tf_subset = tf_train

        flat, _ = train_model(
            "TransE",
            tf_subset,
            tf_valid,
            tf_test,
            epochs=CONFIG["size_sensitivity_epochs"],
            save_as=f"TransE_size_{actual}",
        )
        flat["kb_size"] = actual
        results.append(flat)

    with open(RESULTS_DIR / "size_sensitivity.json", "w", encoding="utf-8") as file_obj:
        json.dump(results, file_obj, indent=2)


def nearest_neighbours_readable(model, tf_train, names, k=5):
    print("\nNearest neighbours (MCU context)")
    embeddings = model.entity_representations[0](indices=None).detach().cpu().numpy()
    entity_to_id = tf_train.entity_to_id
    id_to_entity = {value: key for key, value in entity_to_id.items()}

    for name in names:
        matches = [entity for entity in entity_to_id if name.lower() in entity.lower()]
        if not matches:
            print(f"  '{name}' not found")
            continue

        entity = matches[0]
        entity_id = entity_to_id[entity]
        vector = embeddings[entity_id]
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-9
        similarities = (embeddings / norms) @ (vector / (np.linalg.norm(vector) + 1e-9))
        top_indices = np.argsort(-similarities)[1 : k + 1]
        print(f"\n  Neighbours of '{entity}':")
        for idx in top_indices:
            print(f"    {id_to_entity[idx]}  (sim={similarities[idx]:.3f})")


def tsne_plot(model):
    print("\nCreating t-SNE plot")
    embeddings = model.entity_representations[0](indices=None).detach().cpu().numpy()
    sample_size = min(400, len(embeddings))
    indices = np.random.choice(len(embeddings), sample_size, replace=False)
    reduced = TSNE(n_components=2, perplexity=20, random_state=42, max_iter=300).fit_transform(
        embeddings[indices]
    )
    plt.figure(figsize=(12, 8))
    plt.scatter(reduced[:, 0], reduced[:, 1], alpha=0.5, s=10, c="firebrick")
    plt.title("t-SNE - Entity Embeddings (TransE, MCU KG)")
    plt.xlabel("dim 1")
    plt.ylabel("dim 2")
    plt.tight_layout()
    output = PLOTS_DIR / "tsne_entities.png"
    plt.savefig(output, dpi=150)
    plt.close()
    print(f"Saved {output}")


def main():
    print("Loading triple factories...")
    tf_train, tf_valid, tf_test = load_triples()
    print(
        f"Train:{len(tf_train.triples):,} "
        f"Valid:{len(tf_valid.triples):,} "
        f"Test:{len(tf_test.triples):,}"
    )

    _, trained = experiment_comparison(tf_train, tf_valid, tf_test)
    experiment_size_sensitivity(tf_train, tf_valid, tf_test)

    best = trained.get("TransE")
    if best is not None:
        nearest_neighbours_readable(
            best.model,
            tf_train,
            ["Iron_Man", "Avengers_Endgame", "Chris_Evans", "Robert_Downey_Jr", "Phase_3"],
        )
        tsne_plot(best.model)

    print("\nKGE experiments complete.")


if __name__ == "__main__":
    main()
