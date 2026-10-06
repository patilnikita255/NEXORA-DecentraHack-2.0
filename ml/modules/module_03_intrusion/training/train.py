"""
M03 custom training script.

Use this when the NEXORA custom CCTV dataset is ready.

Expected dataset structure:

datasets/custom/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/

A dataset.yaml file should define:
- train
- val
- test
- names
"""

from pathlib import Path

from ultralytics import YOLO


MODULE_ROOT = Path(
    __file__
).resolve().parents[1]

MODEL_PATH = (
    MODULE_ROOT
    / "models"
    / "checkpoints"
    / "yolo11n.pt"
)

DATASET_YAML = (
    MODULE_ROOT
    / "datasets"
    / "custom"
    / "dataset.yaml"
)

OUTPUT_DIR = (
    MODULE_ROOT
    / "models"
    / "exports"
)


def train():
    """
    Train a custom M03 person detector.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Base model not found: {MODEL_PATH}"
        )

    if not DATASET_YAML.exists():
        raise FileNotFoundError(
            f"Dataset YAML not found: {DATASET_YAML}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    model = YOLO(
        str(MODEL_PATH)
    )

    results = model.train(
        data=str(DATASET_YAML),
        epochs=50,
        imgsz=640,
        batch=16,
        project=str(OUTPUT_DIR),
        name="m03_person_detector",
    )

    return results


if __name__ == "__main__":
    print(
        "Starting M03 custom person detector training..."
    )

    train()

    print(
        "Training completed."
    )