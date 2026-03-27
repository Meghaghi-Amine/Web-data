"""
Lab Session 5 - KGE Data Preparation
Nettoyage du KB étendu + splits 80/10/10
"""

import re
import random
from pathlib import Path

random.seed(42)

EXPANDED_NT = Path("kg_artifacts/expanded.nt")
TRAIN_FILE  = Path("data/kge/train.txt")
VALID_FILE  = Path("data/kge/valid.txt")
TEST_FILE   = Path("data/kge/test.txt")
ENTITY2ID   = Path("data/kge/entity2id.txt")
RELATION2ID = Path("data/kge/relation2id.txt")

# Propriétés à retirer (binaires / littéraux / admin)
SKIP_PARTIAL = ["P18","P856","P973","P935","P1566","P625","P571","P569","P570","P18"]


def parse_nt(line: str):
    line = line.strip()
    if not line or line.startswith("#"): return None
    m = re.match(r'^(<[^>]+>)\s+(<[^>]+>)\s+(.+)\s+\.\s*$', line)
    if not m: return None
    s = m.group(1)[1:-1]
    p = m.group(2)[1:-1]
    o_raw = m.group(3).strip()
    o = o_raw[1:-1] if o_raw.startswith("<") else o_raw
    return s, p, o


def should_skip(p: str) -> bool:
    return any(f"/{sk}" in p for sk in SKIP_PARTIAL)


def load_and_clean():
    triples = set()
    skipped = 0
    with open(EXPANDED_NT, encoding="utf-8") as f:
        for line in f:
            t = parse_nt(line)
            if not t: continue
            s, p, o = t
            if should_skip(p) or not o.startswith("http"):
                skipped += 1
                continue
            triples.add((s, p, o))
    print(f"  {len(triples):,} clean triples ({skipped:,} skipped)")
    return list(triples)


def no_leakage(train, valid, test):
    train_e = {e for t in train for e in (t[0],t[2])}
    train_r = {t[1] for t in train}
    cv, ct = [], []
    for t in valid:
        if t[0] in train_e and t[2] in train_e and t[1] in train_r: cv.append(t)
        else: train.append(t)
    for t in test:
        if t[0] in train_e and t[2] in train_e and t[1] in train_r: ct.append(t)
        else: train.append(t)
    return train, cv, ct


def run_preparation():
    print("Cleaning expanded KB…")
    triples = load_and_clean()
    if len(triples) < 5000:
        print(f"⚠  Only {len(triples)} triples — re-run expand_sparql.py")

    random.shuffle(triples)
    n = len(triples)
    n_tr = int(n * 0.80)
    n_va = int(n * 0.10)
    train = triples[:n_tr]
    valid = triples[n_tr:n_tr+n_va]
    test  = triples[n_tr+n_va:]
    train, valid, test = no_leakage(train, valid, test)

    print(f"\nSplits:")
    print(f"  Train: {len(train):,} ({len(train)/n*100:.1f}%)")
    print(f"  Valid: {len(valid):,} ({len(valid)/n*100:.1f}%)")
    print(f"  Test:  {len(test):,}  ({len(test)/n*100:.1f}%)")

    entities  = sorted({e for t in triples for e in (t[0],t[2])})
    relations = sorted({t[1] for t in triples})
    e2id = {e:i for i,e in enumerate(entities)}
    r2id = {r:i for i,r in enumerate(relations)}

    TRAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    for split, path in [(train,TRAIN_FILE),(valid,VALID_FILE),(test,TEST_FILE)]:
        with open(path, "w", encoding="utf-8") as f:
            for s,p,o in split:
                f.write(f"{s}\t{p}\t{o}\n")

    with open(ENTITY2ID,"w",encoding="utf-8") as f:
        f.write(f"{len(e2id)}\n")
        for e,i in sorted(e2id.items(),key=lambda x:x[1]): f.write(f"{e}\t{i}\n")

    with open(RELATION2ID,"w",encoding="utf-8") as f:
        f.write(f"{len(r2id)}\n")
        for r,i in sorted(r2id.items(),key=lambda x:x[1]): f.write(f"{r}\t{i}\n")

    print(f"\n  Entities: {len(e2id):,} | Relations: {len(r2id):,}")
    print(f"✅ data/kge/ — train.txt · valid.txt · test.txt · entity2id.txt · relation2id.txt")


if __name__ == "__main__":
    run_preparation()
