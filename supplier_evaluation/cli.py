"""python -m supplier_evaluation.cli: generate/train/evaluate/infer/demo/reproduce."""

import argparse
from dataclasses import asdict
from pathlib import Path

from supplier_evaluation.artifacts import load_model, save_model
from supplier_evaluation.contracts import QuantityValidity, canonical
from supplier_evaluation.dataset import generate_dataset, load_dataset, save_dataset
from supplier_evaluation.evaluation import demonstrate_planning, evaluate
from supplier_evaluation.model import train


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("generate", "train", "evaluate", "infer", "demo", "reproduce")
    )
    parser.add_argument("--directory", type=Path, default=Path(".artifacts/t14"))
    args = parser.parse_args()
    root = args.directory
    dataset, artifact = root / "dataset.json", root / "model"
    if args.command in ("generate", "reproduce"):
        save_dataset(dataset, generate_dataset())
    if args.command == "generate":
        print(f"Generated explicitly synthetic dataset: {dataset}")
        return
    split = load_dataset(dataset)
    if args.command in ("train", "reproduce"):
        save_model(train(split), artifact)
    # Every reporting/inference operation reloads the trusted locally generated artifact.
    model = load_model(artifact, trusted_local=True)
    if args.command == "train":
        print(f"Trained and reloaded model: {model.metadata['model_id']}")
        return
    root.mkdir(parents=True, exist_ok=True)
    if args.command == "infer":
        assessment = model.infer(
            split.test[0].snapshot, QuantityValidity(1, 1000, "controlled-proxy-v1")
        )
        result = asdict(assessment) | {
            "predicted_class_name": assessment.class_name,
            "raw_class1_fraction": str(assessment.raw_class1_fraction),
            "leaf_support": sum(assessment.leaf_counts),
            "score_is_calibrated_probability": False,
        }
    elif args.command == "demo":
        result = demonstrate_planning(model, split)
    else:
        result = evaluate(model, split)
        if args.command == "reproduce":
            result["solver_demonstration"] = demonstrate_planning(model, split)
    (root / f"{args.command}.json").write_text(canonical(result) + "\n", encoding="utf-8")
    print(canonical(result))


if __name__ == "__main__":
    main()
