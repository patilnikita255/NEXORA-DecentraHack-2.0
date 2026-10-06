from pathlib import Path
from datetime import datetime, timezone

import cv2
import yaml
from ultralytics import YOLO


class PersonDetector:
    """
    M03 Person Detector.

    Responsibilities:
    - Load YOLO model
    - Detect persons
    - Return standardized NEXORA detection objects

    This class does NOT:
    - Track people
    - Decide intrusion
    - Decide authorization
    - Generate incidents
    """

    def __init__(self, config_path: str):
        self.config_path = Path(config_path).resolve()

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

        with open(self.config_path, "r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)

        model_config = self.config["model"]

        self.input_size = int(model_config["input_size"])
        self.confidence_threshold = float(
            model_config["confidence_threshold"]
        )
        self.iou_threshold = float(
            model_config["iou_threshold"]
        )
        self.person_class_id = int(
            model_config["person_class_id"]
        )

        model_path = Path(model_config["path"])

        # Relative model paths are resolved from module_03_intrusion.
        if not model_path.is_absolute():
            module_root = self.config_path.parent.parent
            model_path = module_root / model_path

        self.model_path = model_path.resolve()

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"YOLO model not found: {self.model_path}\n"
                "Place yolo11n.pt inside models/checkpoints/"
            )

        self.model = YOLO(str(self.model_path))

    def detect(
        self,
        frame,
        camera_id: str,
        frame_id: int,
    ):
        """
        Detect persons in one video frame.

        Args:
            frame:
                OpenCV BGR frame.

            camera_id:
                NEXORA camera identifier.

            frame_id:
                Current video frame number.

        Returns:
            List of standardized NEXORA detections.
        """

        if frame is None:
            raise ValueError("Frame cannot be None.")

        results = self.model.predict(
            source=frame,
            imgsz=self.input_size,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            classes=[self.person_class_id],
            verbose=False,
        )

        detections = []

        if not results:
            return detections

        result = results[0]

        if result.boxes is None:
            return detections

        boxes = result.boxes

        for index in range(len(boxes)):
            class_id = int(boxes.cls[index].item())
            confidence = float(boxes.conf[index].item())

            # M03 focuses on persons.
            if class_id != self.person_class_id:
                continue

            x1, y1, x2, y2 = boxes.xyxy[index].tolist()

            detection = {
                "module": "module_03_intrusion",
                "camera_id": camera_id,
                "frame_id": frame_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "track_id": None,
                "class_name": "person",
                "confidence": round(confidence, 4),
                "bbox": {
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2),
                },
            }

            detections.append(detection)

        return detections


def draw_detections(frame, detections):
    """
    Draw detected persons on a frame.

    This is only a visualization helper.
    """

    if frame is None:
        raise ValueError("Frame cannot be None.")

    output = frame.copy()

    for detection in detections:
        bbox = detection["bbox"]

        x1 = bbox["x1"]
        y1 = bbox["y1"]
        x2 = bbox["x2"]
        y2 = bbox["y2"]

        confidence = detection["confidence"]

        label = f"person {confidence:.2f}"

        cv2.rectangle(
            output,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2,
        )

        cv2.putText(
            output,
            label,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    return output