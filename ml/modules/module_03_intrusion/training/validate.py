"""
M03 model validation script.

This script reports actual measured evaluation
results from the trained model.

Do not manually enter or fabricate metrics.
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


def validate():
    """
    Run YOLO validation.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    if not DATASET_YAML.exists():
        raise FileNotFoundError(
            f"Dataset YAML not found: {DATASET_YAML}"
        )

    model = YOLO(
        str(MODEL_PATH)
    )

    metrics = model.val(
        data=str(DATASET_YAML),
        imgsz=640,
    )

    return metrics


if __name__ == "__main__":
    print(
        "Running M03 model validation..."
    )

    metrics = validate()

    print(
        "Validation completed."
    )

    print(metrics)