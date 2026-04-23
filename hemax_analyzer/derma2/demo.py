from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from engine.inference import DermaPredictor


class C:
    R = "\033[0m"; B = "\033[1m"; D = "\033[2m"
    GRN = "\033[92m"; YEL = "\033[93m"; RED = "\033[91m"
    CYN = "\033[96m"; MAG = "\033[95m"


SEVERITY_COLOR = {
    "critical": C.RED,
    "high":     C.RED,
    "medium":   C.YEL,
    "low":      C.GRN,
}


def print_prediction(predictor: DermaPredictor, img_path: str,
                     true_label: str = None, save_heatmap: bool = False):
    img_name = Path(img_path).name
    print()
    print("━" * 80)
    print(f"  {C.B}{img_name}{C.R}")
    if true_label:
        print(f"  {C.D}Ground truth: {true_label.upper()}{C.R}")
    print("━" * 80)

    pred = predictor.predict(img_path)
    severity_color = SEVERITY_COLOR.get(pred.severity, C.R)

    print(f"  Top diagnosis: {severity_color}{C.B}{pred.top_class.upper()}{C.R}  "
          f"({pred.top_class_name_en})")
    print(f"  Confidence:    {pred.top_prob*100:.1f}%")
    print(f"  Severity:      {severity_color}{pred.severity}{C.R}")
    if true_label:
        is_correct = pred.top_class == true_label
        marker = "✓ CORRECT" if is_correct else "✗ WRONG"
        color = C.GRN if is_correct else C.RED
        print(f"  Verdict:       {color}{C.B}{marker}{C.R}")

    print()
    print(f"  {C.B}{C.D}Top-3 predictions:{C.R}")
    for cls, p in pred.top_k[:3]:
        sev_color = SEVERITY_COLOR.get(predictor.class_severity.get(cls, "low"), C.R)
        bar_len = int(p * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        name_en = predictor.class_names_en.get(cls, cls)
        print(f"    {sev_color}{bar}{C.R}  {cls.upper():<6}  "
              f"{p*100:5.1f}%  {C.D}{name_en}{C.R}")

    if save_heatmap:
        try:
            _, overlay = predictor.gradcam(img_path)
            out = Path(img_path).with_suffix(".gradcam.png")
            Image.fromarray(overlay).save(out)
            print(f"\n  {C.CYN}↳ saved Grad-CAM heatmap: {out}{C.R}")
        except Exception as e:
            print(f"\n  {C.RED}Grad-CAM failed: {e}{C.R}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("images", nargs="*",
                        help="One or more image paths (JPEG/PNG)")
    parser.add_argument("--gradcam", action="store_true",
                        help="Save Grad-CAM PNG next to each image")
    parser.add_argument("--test-set", action="store_true",
                        help="Pick 7 random test cases (one per class)")
    parser.add_argument("--model", default="model_out/model.pt",
                        help="Path to trained model")
    args = parser.parse_args()

    print(f"\n{C.B}{'═' * 80}{C.R}")
    print(f"  {C.B}HEMAX_DERMA — Skin Lesion Classifier Demo{C.R}")
    print(f"  {C.D}HAM10000-trained ResNet-18, 7 dermatoscopic classes{C.R}")
    print(f"{C.B}{'═' * 80}{C.R}")

    predictor = DermaPredictor(args.model, device="cpu")

    if args.test_set:
        test_csv = Path(__file__).parent / "data_processed" / "test.csv"
        if not test_csv.exists():
            print(f"{C.RED}{test_csv} not found — run prepare_data.py first{C.R}")
            return
        df = pd.read_csv(test_csv)
        for cls in predictor.classes:
            sub = df[df["dx"] == cls]
            if sub.empty:
                continue
            row = sub.iloc[0]
            print_prediction(predictor, row["image_path"],
                             true_label=cls, save_heatmap=args.gradcam)
    elif args.images:
        for img in args.images:
            print_prediction(predictor, img, save_heatmap=args.gradcam)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
