"""Command-line entry for Auto-Hypothesis pipeline (스켈레톤)."""

import argparse

from auto_hypothesis_agent.config import (
    NEO4J_BOLT_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
)

from auto_hypothesis_agent.kg_interface import GraphClient
from auto_hypothesis_agent.hypothesis_generator import HypothesisGenerator
from auto_hypothesis_agent.optimization.bo_optimizer import BOOptimizer
from auto_hypothesis_agent.experiment_designer import ExperimentDesigner
from auto_hypothesis_agent.protocol_generator import ProtocolGenerator

print("Neo4j URI =", NEO4J_BOLT_URI)


def run(topic: str, n_hypo: int = 5):
    # Placeholder pipeline logic
    graph = GraphClient(NEO4J_BOLT_URI, NEO4J_USER, NEO4J_PASSWORD)
    hypo_gen = HypothesisGenerator(graph)
    optimizer = BOOptimizer(graph)
    designer = ExperimentDesigner()
    proto_gen = ProtocolGenerator()

    hypotheses = hypo_gen.generate(topic, n_hypo)

    print("\n=== Generated Hypotheses ===")
    for idx, h in enumerate(hypotheses, 1):
        print(f"{idx}. {h.text}")

    print("============================\n")

    for h in hypotheses:
        try:
            plans = optimizer.suggest(h, n_trials=3)
        except ValueError as e:
            print("[WARN]", e, "-- skipping hypothesis")
            continue

        for plan in plans:
            design = designer.design(plan)
            sop = proto_gen.render(design)
            print("--- Trial", plan.trial_index, plan.parameters)
            print(sop.markdown)


def main():
    parser = argparse.ArgumentParser(description="Auto-Hypothesis Agent CLI (stub)")
    parser.add_argument("--topic", required=True, help="연구 주제 키워드")
    parser.add_argument("--n_hypo", type=int, default=5, help="생성할 가설 개수")

    args = parser.parse_args()
    run(args.topic, args.n_hypo)


if __name__ == "__main__":
    main() 