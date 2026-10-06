import sys
from pathlib import Path

import numpy as np


MODULE_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(MODULE_ROOT)
)

from inference.detector import PersonDetector


CONFIG_PATH = (
    MODULE_ROOT
    / "config"
    / "config.yaml"
)


def test_detector_initializes():
    """
    Test that YOLO person detector loads.
    """

    detector = PersonDetector(
        str(CONFIG_PATH)
    )

    assert detector.model is not None


def test_detector_returns_list():
    """
    Test that detection returns a list.
    """

    detector = PersonDetector(
        str(CONFIG_PATH)
    )

    frame = np.zeros(
        (640, 640, 3),
        dtype=np.uint8
    )

    detections = detector.detect(
        frame=frame,
        camera_id="CAM-TEST",
        frame_id=1,
    )

    assert isinstance(
        detections,
        list
    )


def test_detection_output_structure():
    """
    Test the standard NEXORA detection format.
    """

    detector = PersonDetector(
        str(CONFIG_PATH)
    )

    frame = np.zeros(
        (640, 640, 3),
        dtype=np.uint8
    )

    detections = detector.detect(
        frame=frame,
        camera_id="CAM-TEST",
        frame_id=1,
    )

    required_fields = {
        "module",
        "camera_id",
        "frame_id",
        "timestamp",
        "track_id",
        "class_name",
        "confidence",
        "bbox",
    }

    for detection in detections:

        assert required_fields.issubset(
            detection.keys()
        )

        assert (
            detection["module"]
            == "module_03_intrusion"
        )

        assert (
            detection["camera_id"]
            == "CAM-TEST"
        )

        assert (
            detection["class_name"]
            == "person"
        )

        assert (
            0.0
            <= detection["confidence"]
            <= 1.0
        )

        bbox = detection["bbox"]

        assert "x1" in bbox
        assert "y1" in bbox
        assert "x2" in bbox
        assert "y2" in bbox


def test_detection_bbox_is_valid():
    """
    Test that bounding boxes have valid coordinates.
    """

    detector = PersonDetector(
        str(CONFIG_PATH)
    )

    frame = np.zeros(
        (640, 640, 3),
        dtype=np.uint8
    )

    detections = detector.detect(
        frame=frame,
        camera_id="CAM-TEST",
        frame_id=1,
    )

    for detection in detections:

        bbox = detection["bbox"]

        assert bbox["x1"] <= bbox["x2"]
        assert bbox["y1"] <= bbox["y2"]

        assert bbox["x1"] >= 0
        assert bbox["y1"] >= 0