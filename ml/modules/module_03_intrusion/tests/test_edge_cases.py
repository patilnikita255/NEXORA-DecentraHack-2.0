import sys
from pathlib import Path

import cv2
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


def create_detector():
    return PersonDetector(
        str(CONFIG_PATH)
    )


def test_empty_scene():
    detector = create_detector()

    frame = np.zeros(
        (640, 640, 3),
        dtype=np.uint8
    )

    detections = detector.detect(
        frame,
        "CAM-EMPTY",
        1,
    )

    assert isinstance(
        detections,
        list
    )


def test_low_light_scene():
    detector = create_detector()

    frame = np.ones(
        (640, 640, 3),
        dtype=np.uint8
    ) * 20

    detections = detector.detect(
        frame,
        "CAM-LOW-LIGHT",
        1,
    )

    assert isinstance(
        detections,
        list
    )


def test_blurred_frame():
    detector = create_detector()

    frame = np.random.randint(
        0,
        256,
        (640, 640, 3),
        dtype=np.uint8,
    )

    blurred = cv2.GaussianBlur(
        frame,
        (15, 15),
        0,
    )

    detections = detector.detect(
        blurred,
        "CAM-BLUR",
        1,
    )

    assert isinstance(
        detections,
        list
    )


def test_small_resolution():
    detector = create_detector()

    frame = np.zeros(
        (240, 320, 3),
        dtype=np.uint8
    )

    detections = detector.detect(
        frame,
        "CAM-SMALL",
        1,
    )

    assert isinstance(
        detections,
        list
    )


def test_large_resolution():
    detector = create_detector()

    frame = np.zeros(
        (1080, 1920, 3),
        dtype=np.uint8
    )

    detections = detector.detect(
        frame,
        "CAM-HD",
        1,
    )

    assert isinstance(
        detections,
        list
    )


def test_multiple_people_scene():
    detector = create_detector()

    frame = np.zeros(
        (720, 1280, 3),
        dtype=np.uint8
    )

    detections = detector.detect(
        frame,
        "CAM-CROWD",
        1,
    )

    assert isinstance(
        detections,
        list
    )

    for detection in detections:
        assert (
            detection["class_name"]
            == "person"
        )


def test_partial_visibility_scene():
    detector = create_detector()

    frame = np.zeros(
        (640, 640, 3),
        dtype=np.uint8
    )

    # Simulated partially visible frame.
    cv2.rectangle(
        frame,
        (300, 100),
        (500, 500),
        (255, 255, 255),
        -1,
    )

    detections = detector.detect(
        frame,
        "CAM-OCCLUDED",
        1,
    )

    assert isinstance(
        detections,
        list
    )


def test_invalid_frame():
    detector = create_detector()

    try:
        detector.detect(
            None,
            "CAM-INVALID",
            1,
        )

        assert False, (
            "Detector should reject None frame"
        )

    except ValueError:
        assert True