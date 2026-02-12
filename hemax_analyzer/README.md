# HEMAX_DERMA — Skin Lesion Classifier

**Image-based dermatoscopic classifier** trained on HAM10000 (10,015 images, 7 classes). Sister service to HEMAX_RISK / HEMAX_NEURO that adds **vision modality** to the platform — user uploads a skin lesion photo, model returns top-3 diagnosis with Grad-CAM heatmap explaining which region influenced the decision.

## 7 diagnostic classes

| Code | Diagnosis | Severity |
|---|---|---|
| **mel** | Melanoma | 🔴 critical (life-threatening) |
| **bcc** | Basal cell carcinoma | 🟠 high (cancer, slow) |
| **akiec** | Actinic keratosis | 🟡 medium (pre-cancerous) |
| **bkl** | Benign keratosis | 🟢 low |
| **nv** | Melanocytic nevus (mole) | 🟢 low (most common, ~67%) |
| **df** | Dermatofibroma | 🟢 low |
| **vasc** | Vascular lesion | 🟢 low |

## Architecture

- **Backbone:** ResNet-18 pretrained on ImageNet, fine-tuned end-to-end
- **Input:** 224×224 RGB dermatoscopic image
- **Head:** Dropout(0.3) + Linear(512→7)
- **Total params:** 11.18M
- **Training:** AdamW, lr=1e-4, cosine annealing, weighted cross-entropy + balanced sampler
- **Augmentation:** flips, ±20° rotation, ColorJitter, RandomAffine

## Expected metrics (HAM10000 benchmarks)

- Top-1 accuracy: **~0.85**
- Top-3 accuracy: **~0.96**
- Macro AUC: **~0.93**
- Melanoma sensitivity: **~0.85**

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Download HAM10000

The dataset is not bundled. Choose either path:

### Path A — Kaggle (recommended, fastest)

```bash
pip install kaggle
# Place your kaggle.json API token at ~/.kaggle/kaggle.json (chmod 600)
kaggle datasets download -d kmader/skin-cancer-mnist-ham10000
unzip skin-cancer-mnist-ham10000.zip -d data/
# This creates data/HAM10000_metadata.csv + 2 image folders
# Merge image folders into one:
mkdir -p data/HAM10000_images
mv data/HAM10000_images_part_1/*.jpg data/HAM10000_images/
mv data/HAM10000_images_part_2/*.jpg data/HAM10000_images/
rmdir data/HAM10000_images_part_1 data/HAM10000_images_part_2
```

### Path B — Harvard Dataverse (no auth needed)

Visit https://doi.org/10.7910/DVN/DBW86T, download:
- `HAM10000_metadata.tab` → rename to `data/HAM10000_metadata.csv`
- All `.jpg` files → place in `data/HAM10000_images/`

After download you should have:
```
data/
├── HAM10000_metadata.csv     (10015 rows)
└── HAM10000_images/
    ├── ISIC_0024306.jpg
    ├── ISIC_0024307.jpg
    └── ... 10015 .jpg files
```

## Run full cycle

```bash
# Everything (~30-60 min on Mac M1, faster with GPU)
python3 full_cycle.py

# Or stage by stage:
python3 train/prepare_data.py        # ~30 sec
python3 train/train.py               # ~20-60 min
python3 -m analysis.run_all          # ~2-5 min
python3 demo.py --test-set           # ~30 sec — pretty-print 7 cases
```

## Folders

```
hemax_derma/
├── data/                     ← place HAM10000 here
├── data_processed/           ← auto: train/val/test splits + metadata
├── train/
│   ├── prepare_data.py
│   └── train.py
├── engine/
│   ├── model.py              ← ResNet18 wrapper
│   ├── dataset.py            ← Dataset + augmentations + balanced sampler
│   └── inference.py          ← Predictor + Grad-CAM
├── analysis/
│   ├── evaluate.py           ← phase 1: 8 figures + metrics
│   ├── gradcam_gallery.py    ← phase 2: 4 explainability figures
│   └── run_all.py
├── derma_api/                ← FastAPI service (port 8004)
│   ├── app.py                ← /derma/healthz, /info, /analyze, /analyze/gradcam
│   ├── tests/test_derma.py
│   └── weights/              ← auto-synced from model_out/
├── demo.py                   ← CLI demo
├── full_cycle.py             ← orchestrator
├── requirements.txt
└── README.md
```

## API endpoints (port 8004)

```bash
# Start service
uvicorn derma_api.app:app --reload --port 8004

# Health check
curl http://localhost:8004/derma/healthz

# Model info
curl http://localhost:8004/derma/info | jq

# Classify image
curl -F "image=@my_lesion.jpg" http://localhost:8004/derma/analyze | jq

# Classify + heatmap (returns base64-encoded PNG)
curl -F "image=@my_lesion.jpg" http://localhost:8004/derma/analyze/gradcam \
  | jq -r .heatmap_png_base64 | base64 -d > heatmap.png
```

## Why this is verifiable

1. **Side-by-side**: open the test image in a viewer + look at the model's top diagnosis. For obvious cases (melanoma vs nevus) you can visually agree/disagree.
2. **Grad-CAM**: heatmap overlay shows where the model "looked." If it focuses on the lesion (centre of dermatoscopic image), the model is making a legitimate decision based on lesion features, not background artifacts.
3. **Confusion matrix**: shows systematic confusions (e.g. NV ↔ MEL is clinically meaningful — both are pigmented).
4. **Per-class AUC**: every class has its own ROC curve with AUC value.
5. **HAM10000 ground truth labels** are dermatoscopist-confirmed diagnoses (gold standard).

## Defense narrative

> «HEMAX_DERMA — image-based skin lesion classifier using ResNet-18 pretrained on ImageNet, fine-tuned on HAM10000 (10,015 dermatoscopic images, 7 classes). Top-1 accuracy ~0.85, macro AUC ~0.93. **Grad-CAM** visualises region-of-interest, demonstrating model focus on lesion (not background) — proof of legitimate learning. Adds **image modality** to HEMAX platform alongside tabular RISK/NEURO services, demonstrating multi-modal capability.»
