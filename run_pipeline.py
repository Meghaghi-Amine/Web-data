"""
run_pipeline.py - End-to-end pipeline for the MCU films knowledge graph.

Usage:
    python run_pipeline.py
    python run_pipeline.py --step 1 2 3
"""

from __future__ import annotations

import argparse
import importlib
import sys

STEPS = {
    1: ("Crawling MCU corpus", "src.crawl.crawler", "run_crawler"),
    2: ("Information extraction", "src.ie.ner_extractor", "run_extraction"),
    3: ("RDF knowledge graph construction", "src.kg.build_kg", "main"),
    4: ("Entity alignment", "src.kg.align_entities", "run_alignment"),
    5: ("KB expansion", "src.kg.expand_sparql", "run_expansion"),
    6: ("KGE data preparation", "src.kge.prepare_kge_data", "run_preparation"),
    7: ("KGE training", "src.kge.train_kge", "main"),
    8: ("SWRL reasoning", "src.reason.swrl_reasoning", "run_reasoning_suite"),
    9: ("SWRL vs KGE comparison", "src.kge.swrl_vs_kge", "run_comparison"),
    10: ("RAG evaluation", "src.rag.rag_sparql", "run_evaluation_cli"),
}


def run_step(step_number: int):
    label, module_path, function_name = STEPS[step_number]
    print(f"\n{'=' * 60}\nSTEP {step_number}: {label}\n{'=' * 60}\n")
    module = importlib.import_module(module_path)
    function = getattr(module, function_name)
    function()


def main():
    parser = argparse.ArgumentParser(description="MCU Films Knowledge Graph Pipeline")
    parser.add_argument("--step", nargs="+", type=int)
    args = parser.parse_args()

    steps = args.step if args.step else list(STEPS.keys())
    print("\nMCU Films Knowledge Graph - Pipeline")
    print(f"Steps: {steps}\n")

    for step_number in steps:
        if step_number not in STEPS:
            print(f"Unknown step {step_number}")
            continue
        try:
            run_step(step_number)
        except Exception as exc:
            print(f"\nStep {step_number} failed: {exc}")
            sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
