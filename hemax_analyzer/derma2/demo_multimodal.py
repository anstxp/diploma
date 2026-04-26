from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from engine.multimodal_inference import MultimodalDermaPredictor

ROOT = Path(__file__).parent
PROCESSED = ROOT / "data_processed"
META_CSV = ROOT / "data" / "HAM10000_metadata.csv"
IMAGE_DIR = ROOT / "data" / "HAM10000_images"


def pick_examples(test_df, classes, n_per_class=1):
    examples = []
    for cls in classes:
        sample = test_df[test_df["dx"] == cls]
        if len(sample) > 0:
            examples.append(sample.sample(1, random_state=42).iloc[0])
    return examples


def main(model_dir: Path = None):
    if model_dir is None:
        mm_dir = ROOT / "model_out" / "multimodal"
        candidates = []
        for d in mm_dir.iterdir():
            if d.is_dir():
                metrics_path = d / "metrics.json"
                if metrics_path.exists():
                    with open(metrics_path) as f:
                        m = json.load(f)
                    candidates.append((m["best_val_auc"], d, m["model_name"]))
        candidates.sort(reverse=True)
        _, model_dir, name = candidates[0]
        print(f"\nUsing best model: {name}\n")

    predictor = MultimodalDermaPredictor(model_dir)

    print("=" * 80)
    print(f"  HEMAX_DERMA — Multimodal Demo  [{predictor.model_name}]")
    print("=" * 80)

    meta_df = pd.read_csv(META_CSV)
    test_df = pd.read_csv(PROCESSED / "test.csv").merge(
        meta_df[["image_id", "age", "sex", "localization"]],
        on="image_id", how="left",
    )

    examples = pick_examples(test_df, predictor.classes)
    correct_count = 0

    for ex in examples:
        img_path = IMAGE_DIR / f"{ex['image_id']}.jpg"
        if not img_path.exists():
            continue
        with open(img_path, "rb") as f:
            image_bytes = f.read()

        result = predictor.predict(
            image_bytes,
            age=float(ex["age"]) if not pd.isna(ex["age"]) else None,
            sex=str(ex["sex"]) if not pd.isna(ex["sex"]) else None,
            localization=str(ex["localization"]) if not pd.isna(ex["localization"]) else None,
        )

        true_dx = ex["dx"]
        is_correct = result["top_class"] == true_dx
        if is_correct:
            correct_count += 1

        verdict = "✓ CORRECT" if is_correct else "✗ WRONG"

        print()
        print("─" * 80)
        print(f"  {ex['image_id']}.jpg")
        print(f"  Patient: age={ex.get('age')} sex={ex.get('sex')} site={ex.get('localization')}")
        print(f"  Ground truth: {true_dx.upper()}")
        print("─" * 80)
        print(f"  Top diagnosis: {result['top_class'].upper()}  ({result['top_class_name']})")
        print(f"  Confidence:    {result['confidence']:.1%}")
        print(f"  Severity:      {result['severity']}")
        print(f"  Verdict:       {verdict}")
        print()
        print(f"  Top-3:")
        for tk in result["top_k"]:
            bar = "█" * int(tk["probability"] * 30) + "░" * (30 - int(tk["probability"] * 30))
            print(f"    {bar}  {tk['class_code'].upper():<6}  "
                  f"{tk['probability']:.1%}  {tk['class_name']}")

    print()
    print("=" * 80)
    print(f"  Summary: {correct_count}/{len(examples)} correct")
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=None)
    args = parser.parse_args()
    main(args.model_dir)
