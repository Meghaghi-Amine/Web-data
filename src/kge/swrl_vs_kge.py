"""
Lab Session 5 - Exercise 8: SWRL vs KGE
Règle SWRL: Player(?p) ∧ suffersInjury(?p,?i) ∧ ACLRupture(?i) → HighRiskPlayer(?p)
Analogie KGE: vector(suffersInjury) + vector(ACLRupture) ≈ vector(HighRiskPlayer) ?
"""

import numpy as np
import torch
from pathlib import Path
from pykeen.triples import TriplesFactory

RESULTS_DIR = Path("data/kge/results")
TRAIN_FILE  = Path("data/kge/train.txt")
MODEL_FILE  = RESULTS_DIR / "TransE" / "trained_model.pkl"


def cosine(a, b):
    return float(np.dot(a,b) / (np.linalg.norm(a)*np.linalg.norm(b) + 1e-9))


def get_entity_vec(model, name, e2id):
    emb = model.entity_representations[0](indices=None).detach().cpu().numpy()
    matches = [k for k in e2id if name.lower() in k.lower()]
    if not matches: return None, None
    return emb[e2id[matches[0]]], matches[0]


def get_relation_vec(model, name, r2id):
    emb = model.relation_representations[0](indices=None).detach().cpu().numpy()
    matches = [k for k in r2id if name.lower() in k.lower()]
    if not matches: return None, None
    return emb[r2id[matches[0]]], matches[0]


def run_comparison():
    print("=" * 60)
    print("Exercise 8 — SWRL Rule vs KGE Analogy")
    print("Football Injuries Domain")
    print("=" * 60)

    rd = RESULTS_DIR / "TransE"
    if not MODEL_FILE.exists():
        print("⚠  Run train_kge.py first."); return

    model  = torch.load(MODEL_FILE, map_location="cpu", weights_only=False)
    tf     = TriplesFactory.from_path(TRAIN_FILE)
    e2id   = tf.entity_to_id
    r2id   = tf.relation_to_id

    print("\n📜 SWRL Rule:")
    print("  Player(?p) ∧ suffersInjury(?p,?i) ∧ ACLRupture(?i) → HighRiskPlayer(?p)")
    print("\n🔢 KGE TransE analogy:")
    print("  vector(suffersInjury) + vector(ACLRupture) ≈ vector(known ACL player)?")

    # Chercher les vecteurs de relation et d'entité ACL
    r_vec, r_lbl = get_relation_vec(model, "P54", r2id)    # playsFor comme proxy
    acl_vec, acl_lbl = get_entity_vec(model, "Neymar", e2id)   # joueur blessé ACL
    player_vec, p_lbl = get_entity_vec(model, "Diaby", e2id)   # autre joueur blessé

    if r_vec is not None and acl_vec is not None and player_vec is not None:
        composed = r_vec + acl_vec
        sim = cosine(composed, player_vec)
        print(f"\n  cos(vector({r_lbl}) + vector({acl_lbl}), vector({p_lbl})) = {sim:.4f}")
        if sim > 0.5:
            print("  ✅ Analogie KGE cohérente avec la règle SWRL")
        elif sim > 0.2:
            print("  ⚠  Corrélation partielle — relation capturée approximativement")
        else:
            print("  ❌ Analogie non confirmée — attendu avec TransE sur données bruitées")
    else:
        print("  ⚠  Entités/relations non trouvées — vérifier le KB.")

    print("\n📝 Discussion:")
    print("  SWRL: déterministe, interprétable, exact — si ACLRupture alors HighRisk.")
    print("  KGE:  probabiliste, gère l'incomplétude, mais approximatif.")
    print("  TransE v+r≈t fonctionne bien pour relations 1-to-1 simples.")
    print("  Pour ACL → HighRisk: relation complexe, multi-saut → KGE moins fiable.")
    print("  ComplEx ou RotatE captureraient mieux les relations asymétriques.")


if __name__ == "__main__":
    run_comparison()
