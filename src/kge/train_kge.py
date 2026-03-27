"""
Lab Session 5 - KGE Training & Evaluation
Modèles: TransE, DistMult
Métriques: MRR, Hits@1/3/10
Analyses: voisins proches, t-SNE, sensibilité taille KB
"""

import csv
import json
import numpy as np
from pathlib import Path

from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

np.random.seed(42)

TRAIN_FILE  = Path("data/kge/train.txt")
VALID_FILE  = Path("data/kge/valid.txt")
TEST_FILE   = Path("data/kge/test.txt")
MAPPING_FILE = Path("data/entity_mapping.csv")
RESULTS_DIR = Path("data/kge/results")
PLOTS_DIR   = Path("data/kge/plots")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = {
    "embedding_dim": 100,
    "learning_rate": 0.001,
    "batch_size":    256,
    "num_epochs":    30,
    "size_sensitivity_epochs": 15,
}


def load_triples():
    tf_tr = TriplesFactory.from_path(TRAIN_FILE)
    tf_va = TriplesFactory.from_path(VALID_FILE,
                entity_to_id=tf_tr.entity_to_id,
                relation_to_id=tf_tr.relation_to_id)
    tf_te = TriplesFactory.from_path(TEST_FILE,
                entity_to_id=tf_tr.entity_to_id,
                relation_to_id=tf_tr.relation_to_id)
    return tf_tr, tf_va, tf_te


def unique_sizes(values):
    seen = set()
    ordered = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


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
    with open(MAPPING_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uri = row.get("external_uri", "")
            label = row.get("private_entity", "").strip()
            if uri.startswith("http") and label:
                labels[uri] = label
    return labels


def choose_demo_entities(e2id, label_lookup, requested_names):
    selected = []
    for name in requested_names:
        match = next(
            (
                entity for entity in e2id
                if name.lower() in entity.lower()
                or name.lower() in label_lookup.get(entity, "").lower()
            ),
            None,
        )
        if match and match not in selected:
            selected.append(match)

    if selected:
        return selected

    preferred_labels = [
        "Anterior cruciate ligament rupture",
        "Ankle sprain",
        "wrist",
        "back",
        "groin",
        "Player",
    ]
    for label in preferred_labels:
        match = next(
            (entity for entity, mapped_label in label_lookup.items()
             if mapped_label == label and entity in e2id),
            None,
        )
        if match and match not in selected:
            selected.append(match)

    return selected[:5]


def short_entity_name(uri_or_label):
    if uri_or_label.startswith("http://www.wikidata.org/entity/"):
        return uri_or_label.rsplit("/", 1)[-1]
    if uri_or_label.startswith("http://"):
        return uri_or_label.rsplit("/", 1)[-1]
    return uri_or_label


def train_model(name, tf_tr, tf_va, tf_te, epochs=None, save_as=None):
    ep = epochs or CONFIG["num_epochs"]
    print(f"\n{'='*55}\n  Training {name}  (dim={CONFIG['embedding_dim']}, epochs={ep})\n{'='*55}")
    result = pipeline(
        model=name,
        training=tf_tr, validation=tf_va, testing=tf_te,
        model_kwargs={"embedding_dim": CONFIG["embedding_dim"]},
        optimizer="Adam",
        optimizer_kwargs={"lr": CONFIG["learning_rate"]},
        training_kwargs={"num_epochs": ep, "batch_size": CONFIG["batch_size"]},
        negative_sampler="basic",
        evaluator="RankBasedEvaluator",
        evaluator_kwargs={"filtered": True},
        random_seed=42,
        use_testing_data=True,
    )
    m = result.metric_results.to_dict()
    scores = extract_realistic_metrics(m)
    flat = {
        "model": name,
        "epochs": ep,
        **scores,
    }
    for k,v in flat.items():
        if isinstance(v, float): print(f"  {k}: {v:.4f}")
    out_dir = RESULTS_DIR / (save_as or name)
    result.save_to_directory(str(out_dir))
    print(f"  Saved model to: {out_dir}")
    return flat, result


# ── 5.1 Comparaison modèles ────────────────────────────────────────────────────
def experiment_comparison(tf_tr, tf_va, tf_te):
    results = []
    trained = {}
    for name in ["TransE", "DistMult"]:
        flat, result = train_model(name, tf_tr, tf_va, tf_te, save_as=name)
        results.append(flat)
        trained[name] = result
    print("\n📊 MODEL COMPARISON")
    print(f"{'Model':<12} {'MRR':>8} {'Hits@1':>8} {'Hits@3':>8} {'Hits@10':>8}")
    print("-"*50)
    for r in results:
        print(f"{r['model']:<12} {r['MRR']:>8.4f} {r['Hits@1']:>8.4f} {r['Hits@3']:>8.4f} {r['Hits@10']:>8.4f}")
    with open(RESULTS_DIR/"comparison.json","w") as f: json.dump(results,f,indent=2)
    return results, trained


# ── 5.2 Sensibilité taille KB ──────────────────────────────────────────────────
def experiment_size_sensitivity(tf_tr, tf_va, tf_te):
    sizes = unique_sizes([10_000, min(20_000, len(tf_tr.triples)), len(tf_tr.triples)])
    size_res = []
    for sz in sizes:
        actual = sz
        print(f"\n  Subsampling → {actual:,} triples")
        if actual < len(tf_tr.triples):
            idx = np.random.choice(len(tf_tr.triples), actual, replace=False)
            sub = tf_tr.triples[idx]
            tf_sub = TriplesFactory.from_labeled_triples(sub,
                         entity_to_id=tf_tr.entity_to_id,
                         relation_to_id=tf_tr.relation_to_id)
        else:
            tf_sub = tf_tr
        flat, _ = train_model(
            "TransE",
            tf_sub,
            tf_va,
            tf_te,
            epochs=CONFIG["size_sensitivity_epochs"],
            save_as=f"TransE_size_{actual}",
        )
        flat["kb_size"] = actual
        size_res.append(flat)
    print("\n📊 SIZE SENSITIVITY")
    print(f"{'Size':>10} {'MRR':>8} {'Hits@10':>8}")
    for r in size_res:
        print(f"{r['kb_size']:>10,} {r['MRR']:>8.4f} {r['Hits@10']:>8.4f}")
    with open(RESULTS_DIR/"size_sensitivity.json","w") as f: json.dump(size_res,f,indent=2)


# ── 6.1 Voisins proches ────────────────────────────────────────────────────────
def nearest_neighbours(model, tf_tr, names, k=5):
    print("\n🔍 NEAREST NEIGHBOURS (football injuries context)")
    emb = model.entity_representations[0](indices=None).detach().cpu().numpy()
    e2id = tf_tr.entity_to_id
    id2e = {v:k for k,v in e2id.items()}
    for name in names:
        matches = [e for e in e2id if name.lower() in e.lower()]
        if not matches: print(f"  '{name}' not found"); continue
        eid = e2id[matches[0]]
        vec = emb[eid]
        norms = np.linalg.norm(emb,axis=1,keepdims=True)+1e-9
        sims  = (emb/norms) @ (vec/(np.linalg.norm(vec)+1e-9))
        top_k = np.argsort(-sims)[1:k+1]
        print(f"\n  Neighbours of '{matches[0]}':")
        for idx in top_k:
            print(f"    {id2e[idx]}  (sim={sims[idx]:.3f})")


# ── 6.2 t-SNE ─────────────────────────────────────────────────────────────────
def tsne_plot(model, tf_tr, n=500):
    print("\n🗺  t-SNE clustering")
    emb = model.entity_representations[0](indices=None).detach().cpu().numpy()
    idx = np.random.choice(len(emb), min(n,len(emb)), replace=False)
    reduced = TSNE(n_components=2, perplexity=20, random_state=42, max_iter=300).fit_transform(emb[idx])
    plt.figure(figsize=(12,8))
    plt.scatter(reduced[:,0], reduced[:,1], alpha=0.5, s=10, c='steelblue')
    plt.title("t-SNE — Entity Embeddings (TransE, Football Injuries KB)")
    plt.xlabel("dim 1"); plt.ylabel("dim 2"); plt.tight_layout()
    out = PLOTS_DIR/"tsne_entities.png"
    plt.savefig(out, dpi=150); plt.close()
    print(f"  ✓ {out}")


# ── Main ───────────────────────────────────────────────────────────────────────
def nearest_neighbours_readable(model, tf_tr, names, k=5):
    print("\nNearest neighbours (football injuries context)")
    emb = model.entity_representations[0](indices=None).detach().cpu().numpy()
    e2id = tf_tr.entity_to_id
    id2e = {v: k for k, v in e2id.items()}
    label_lookup = load_entity_labels()
    demo_entities = choose_demo_entities(e2id, label_lookup, names)

    if not demo_entities:
        print("  No readable demo entities found in the current KGE.")
        return

    for entity in demo_entities:
        eid = e2id[entity]
        vec = emb[eid]
        norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9
        sims = (emb / norms) @ (vec / (np.linalg.norm(vec) + 1e-9))
        top_k = np.argsort(-sims)[1:k+1]
        label = label_lookup.get(entity, entity)
        print(f"\n  Neighbours of '{label}' ({short_entity_name(entity)}):")
        for idx in top_k:
            neighbour = id2e[idx]
            neighbour_label = label_lookup.get(neighbour, neighbour)
            print(f"    {neighbour_label} ({short_entity_name(neighbour)})  (sim={sims[idx]:.3f})")


def main():
    print("Loading triple factories…")
    tf_tr, tf_va, tf_te = load_triples()
    print(f"  Train:{len(tf_tr.triples):,} Valid:{len(tf_va.triples):,} Test:{len(tf_te.triples):,}")

    _, trained = experiment_comparison(tf_tr, tf_va, tf_te)
    experiment_size_sensitivity(tf_tr, tf_va, tf_te)

    best = trained.get("TransE")
    if best is not None:
        nearest_neighbours_readable(best.model, tf_tr,
            ["Messi","Neymar","Diaby","Cazorla","Arsenal","Chelsea","France"])
        tsne_plot(best.model, tf_tr)

    print("\n✅ KGE experiments complete!")


if __name__ == "__main__":
    main()
