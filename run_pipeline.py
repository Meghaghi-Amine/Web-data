"""
run_pipeline.py — Pipeline complet : Blessures de footballeurs
Usage:
    python run_pipeline.py              # tout
    python run_pipeline.py --step 1 2   # étapes spécifiques
"""
import sys, argparse, importlib

STEPS = {
    1:  ("Crawling Wikipedia",        "src.crawl.crawler",         "run_crawler"),
    2:  ("NER + Relations",           "src.ie.ner_extractor",      "run_extraction"),
    3:  ("Construction KG RDF",       "src.kg.build_kg",           "main"),
    4:  ("Alignement Wikidata",       "src.kg.align_entities",     "run_alignment"),
    5:  ("Expansion SPARQL",          "src.kg.expand_sparql",      "run_expansion"),
    6:  ("Preparation donnees KGE",   "src.kge.prepare_kge_data",  "run_preparation"),
    7:  ("Entrainement KGE",          "src.kge.train_kge",         "main"),
    8:  ("Raisonnement SWRL",         "src.reason.swrl_reasoning", "run_family_swrl"),
    9:  ("Comparaison SWRL vs KGE",   "src.kge.swrl_vs_kge",       "run_comparison"),
    10: ("Evaluation RAG",            "src.rag.rag_sparql",        "run_evaluation_cli"),
}

def run_step(n):
    label, mod_path, func_name = STEPS[n]
    print(f"\n{'='*60}\n  STEP {n}: {label}\n{'='*60}\n")
    mod  = importlib.import_module(mod_path)
    func = getattr(mod, func_name)
    func()

def main():
    parser = argparse.ArgumentParser(description="Football Injuries KG Pipeline")
    parser.add_argument("--step", nargs="+", type=int)
    args  = parser.parse_args()
    steps = args.step if args.step else list(STEPS.keys())
    print("\nFootball Injuries Knowledge Graph - Pipeline")
    print(f"   Steps: {steps}\n")
    for s in steps:
        if s not in STEPS: print(f"Unknown step {s}"); continue
        try:
            run_step(s)
        except Exception as e:
            print(f"\nStep {s} failed: {e}")
            sys.exit(1)
    print("\nDone!")

if __name__ == "__main__":
    main()
