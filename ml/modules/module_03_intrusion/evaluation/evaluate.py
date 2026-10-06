"""
M03 Intrusion Module Evaluation Framework.

Evaluates:
- Video information
- End-to-end processing performance
- Processing FPS
- Real-time factor
- Event and incident counts
- Ground-truth detection metrics:
    - Precision
    - Recall
    - F1
    - mAP@50
    - mAP@50:95

Tracking and operational event metrics remain unavailable until
appropriate ground-truth annotations are provided.
"""

import argparse
import json
import sys
import time
from pathlib import Path


# ============================================================
# PYTHON IMPORT PATH
# ============================================================

MODULE_ROOT = Path(__file__).resolve().parents[1]

if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))


import cv2

from inference.pipeline import IntrusionPipeline


# ============================================================
# PATHS
# ============================================================

RESULTS_DIR = MODULE_ROOT / "evaluation" / "results"


# ============================================================
# VIDEO INFORMATION
# ============================================================

def get_video_info(video_path):

    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():
        raise RuntimeError(
            f"Could not open video: {video_path}"
        )

    reported_fps = capture.get(cv2.CAP_PROP_FPS)

    reported_frame_count = int(
        capture.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    width = int(
        capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    if reported_fps > 120:
        source_fps = 25.0
        fps_correction_applied = True
        fps_note = (
            "OpenCV reported an invalid FPS value. "
            "25 FPS nominal stream rate used for evaluation."
        )

    elif reported_fps <= 0:
        source_fps = 25.0
        fps_correction_applied = True
        fps_note = (
            "OpenCV did not provide a valid FPS value. "
            "25 FPS nominal stream rate used for evaluation."
        )

    else:
        source_fps = float(reported_fps)
        fps_correction_applied = False
        fps_note = "OpenCV reported FPS used."

    decoded_frame_count = 0

    while True:

        success, _ = capture.read()

        if not success:
            break

        decoded_frame_count += 1

    capture.release()

    return {
        "reported_fps": round(
            float(reported_fps), 3
        ),
        "source_fps": round(
            float(source_fps), 3
        ),
        "fps_correction_applied":
            fps_correction_applied,
        "fps_note": fps_note,
        "reported_frame_count":
            reported_frame_count,
        "decoded_frame_count":
            decoded_frame_count,
        "width": width,
        "height": height,
    }


# ============================================================
# IOU
# ============================================================

def calculate_iou(box_a, box_b):

    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(
        0.0,
        ix2 - ix1
    )

    ih = max(
        0.0,
        iy2 - iy1
    )

    intersection = iw * ih

    area_a = (
        max(0.0, ax2 - ax1) *
        max(0.0, ay2 - ay1)
    )

    area_b = (
        max(0.0, bx2 - bx1) *
        max(0.0, by2 - by1)
    )

    union = (
        area_a +
        area_b -
        intersection
    )

    if union <= 0:
        return 0.0

    return intersection / union


# ============================================================
# YOLO ANNOTATION READING
# ============================================================

def load_yolo_annotations(
    annotation_path,
    image_width,
    image_height,
):

    boxes = []

    if not annotation_path.exists():
        return boxes

    with open(
        annotation_path,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            values = line.split()

            if len(values) != 5:
                continue

            class_id = int(values[0])

            if class_id != 0:
                continue

            center_x = float(values[1])
            center_y = float(values[2])
            width = float(values[3])
            height = float(values[4])

            center_x *= image_width
            center_y *= image_height
            width *= image_width
            height *= image_height

            x1 = center_x - width / 2
            y1 = center_y - height / 2
            x2 = center_x + width / 2
            y2 = center_y + height / 2

            boxes.append(
                [
                    x1,
                    y1,
                    x2,
                    y2,
                ]
            )

    return boxes


# ============================================================
# YOLO PREDICTION
# ============================================================

def get_predictions(
    model,
    image,
    confidence_threshold,
):

    results = model.predict(
        source=image,
        imgsz=640,
        conf=confidence_threshold,
        verbose=False,
    )

    predictions = []

    if not results:
        return predictions

    result = results[0]

    if result.boxes is None:
        return predictions

    for box in result.boxes:

        class_id = int(
            box.cls[0].item()
        )

        # YOLO class 0 = person
        if class_id != 0:
            continue

        confidence = float(
            box.conf[0].item()
        )

        coordinates = (
            box.xyxy[0]
            .cpu()
            .numpy()
            .tolist()
        )

        predictions.append(
            {
                "box": coordinates,
                "confidence": confidence,
            }
        )

    return predictions


# ============================================================
# MATCHING
# ============================================================

def match_predictions(
    ground_truth_boxes,
    predictions,
    iou_threshold,
):

    matched_gt = set()

    true_positives = 0
    false_positives = 0

    predictions = sorted(
        predictions,
        key=lambda item: item["confidence"],
        reverse=True,
    )

    for prediction in predictions:

        best_iou = 0.0
        best_index = None

        for index, gt_box in enumerate(
            ground_truth_boxes
        ):

            if index in matched_gt:
                continue

            iou = calculate_iou(
                prediction["box"],
                gt_box,
            )

            if iou > best_iou:
                best_iou = iou
                best_index = index

        if (
            best_index is not None
            and best_iou >= iou_threshold
        ):

            true_positives += 1

            matched_gt.add(
                best_index
            )

        else:

            false_positives += 1

    false_negatives = (
        len(ground_truth_boxes)
        - len(matched_gt)
    )

    return (
        true_positives,
        false_positives,
        false_negatives,
    )


# ============================================================
# PRECISION / RECALL / F1
# ============================================================

def calculate_prf(
    true_positives,
    false_positives,
    false_negatives,
):

    precision_denominator = (
        true_positives +
        false_positives
    )

    recall_denominator = (
        true_positives +
        false_negatives
    )

    if precision_denominator > 0:
        precision = (
            true_positives /
            precision_denominator
        )
    else:
        precision = 0.0

    if recall_denominator > 0:
        recall = (
            true_positives /
            recall_denominator
        )
    else:
        recall = 0.0

    if precision + recall > 0:

        f1 = (
            2 *
            precision *
            recall /
            (precision + recall)
        )

    else:

        f1 = 0.0

    return (
        precision,
        recall,
        f1,
    )


# ============================================================
# AVERAGE PRECISION
# ============================================================

def calculate_average_precision(
    image_records,
    iou_threshold,
):
    """
    Calculate AP using confidence-ranked predictions.

    IMPORTANT:
    Ground-truth objects are counted once per image,
    not once per prediction.
    """

    total_ground_truth = sum(
        len(record["ground_truth"])
        for record in image_records
    )

    if total_ground_truth == 0:
        return 0.0

    prediction_records = []

    for record in image_records:

        for prediction in record["predictions"]:

            prediction_records.append(
                {
                    "image_id":
                        record["image_id"],

                    "box":
                        prediction["box"],

                    "confidence":
                        prediction["confidence"],

                    "ground_truth":
                        record["ground_truth"],
                }
            )

    prediction_records.sort(
        key=lambda item: item["confidence"],
        reverse=True,
    )

    matched = {}

    true_positive_flags = []
    false_positive_flags = []

    for prediction in prediction_records:

        image_id = prediction["image_id"]

        ground_truth_boxes = (
            prediction["ground_truth"]
        )

        best_iou = 0.0
        best_gt_index = None

        for gt_index, gt_box in enumerate(
            ground_truth_boxes
        ):

            match_key = (
                image_id,
                gt_index,
            )

            if match_key in matched:
                continue

            iou = calculate_iou(
                prediction["box"],
                gt_box,
            )

            if iou > best_iou:

                best_iou = iou
                best_gt_index = gt_index

        if (
            best_gt_index is not None
            and best_iou >= iou_threshold
        ):

            matched[
                (
                    image_id,
                    best_gt_index,
                )
            ] = True

            true_positive_flags.append(1)
            false_positive_flags.append(0)

        else:

            true_positive_flags.append(0)
            false_positive_flags.append(1)

    cumulative_tp = 0
    cumulative_fp = 0

    precisions = []
    recalls = []

    for tp, fp in zip(
        true_positive_flags,
        false_positive_flags,
    ):

        cumulative_tp += tp
        cumulative_fp += fp

        total_predictions = (
            cumulative_tp +
            cumulative_fp
        )

        precision = (
            cumulative_tp /
            total_predictions
        )

        recall = (
            cumulative_tp /
            total_ground_truth
        )

        precisions.append(precision)
        recalls.append(recall)

    # 101-point interpolated AP.
    ap = 0.0

    for recall_level in range(101):

        recall_threshold = (
            recall_level / 100.0
        )

        maximum_precision = 0.0

        for precision, recall in zip(
            precisions,
            recalls,
        ):

            if recall >= recall_threshold:

                maximum_precision = max(
                    maximum_precision,
                    precision,
                )

        ap += (
            maximum_precision /
            101.0
        )

    return ap


# ============================================================
# GROUND-TRUTH EVALUATION
# ============================================================

def evaluate_ground_truth(
    images_dir,
    annotations_dir,
    model_path,
    confidence_threshold=0.5,
):

    images_dir = Path(images_dir)
    annotations_dir = Path(annotations_dir)
    model_path = Path(model_path)

    if not images_dir.exists():
        raise FileNotFoundError(
            f"Ground-truth image directory not found: "
            f"{images_dir}"
        )

    if not annotations_dir.exists():
        raise FileNotFoundError(
            f"Ground-truth annotation directory not found: "
            f"{annotations_dir}"
        )

    if not model_path.exists():
        raise FileNotFoundError(
            f"YOLO model not found: "
            f"{model_path}"
        )

    from ultralytics import YOLO

    print()
    print("=" * 60)
    print("GROUND-TRUTH DETECTION EVALUATION")
    print("=" * 60)

    image_paths = sorted(
        images_dir.glob("*.jpg")
    )

    if not image_paths:
        raise RuntimeError(
            "No ground-truth images found."
        )

    print(
        f"Images found: {len(image_paths)}"
    )

    print(
        f"Model: {model_path}"
    )

    model = YOLO(
        str(model_path)
    )

    image_records = []

    total_ground_truth = 0
    total_predictions = 0

    # --------------------------------------------------------
    # Run YOLO once per image
    # --------------------------------------------------------

    for image_path in image_paths:

        image = cv2.imread(
            str(image_path)
        )

        if image is None:

            print(
                f"WARNING: Could not read "
                f"{image_path}"
            )

            continue

        image_height, image_width = (
            image.shape[:2]
        )

        annotation_path = (
            annotations_dir /
            f"{image_path.stem}.txt"
        )

        ground_truth = (
            load_yolo_annotations(
                annotation_path,
                image_width,
                image_height,
            )
        )

        predictions = get_predictions(
            model,
            image,
            confidence_threshold,
        )

        image_records.append(
            {
                "image_id":
                    image_path.stem,

                "ground_truth":
                    ground_truth,

                "predictions":
                    predictions,
            }
        )

        total_ground_truth += len(
            ground_truth
        )

        total_predictions += len(
            predictions
        )

    # --------------------------------------------------------
    # Precision / Recall / F1 @ IoU 0.50
    # --------------------------------------------------------

    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for record in image_records:

        (
            tp,
            fp,
            fn,
        ) = match_predictions(
            record["ground_truth"],
            record["predictions"],
            iou_threshold=0.50,
        )

        true_positives += tp
        false_positives += fp
        false_negatives += fn

    (
        precision,
        recall,
        f1,
    ) = calculate_prf(
        true_positives,
        false_positives,
        false_negatives,
    )

    # --------------------------------------------------------
    # mAP@50
    # --------------------------------------------------------

    map50 = calculate_average_precision(
        image_records,
        0.50,
    )

    # --------------------------------------------------------
    # mAP@50:95
    # --------------------------------------------------------

    ap_values = []

    for iou_threshold in [
        0.50,
        0.55,
        0.60,
        0.65,
        0.70,
        0.75,
        0.80,
        0.85,
        0.90,
        0.95,
    ]:

        ap = calculate_average_precision(
            image_records,
            iou_threshold,
        )

        ap_values.append(ap)

    map50_95 = (
        sum(ap_values) /
        len(ap_values)
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    evaluation = {

        "status": "AVAILABLE",

        "images_evaluated":
            len(image_records),

        "ground_truth_persons":
            total_ground_truth,

        "predicted_persons":
            total_predictions,

        "true_positives_iou50":
            true_positives,

        "false_positives_iou50":
            false_positives,

        "false_negatives_iou50":
            false_negatives,

        "precision":
            round(precision, 4),

        "recall":
            round(recall, 4),

        "f1":
            round(f1, 4),

        "map50":
            round(map50, 4),

        "map50_95":
            round(map50_95, 4),

        "iou_threshold_for_pr_f1":
            0.50,

        "confidence_threshold":
            confidence_threshold,
    }

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    print()
    print(
        f"Ground-truth persons: "
        f"{total_ground_truth}"
    )

    print(
        f"Predicted persons: "
        f"{total_predictions}"
    )

    print(
        f"True positives @ IoU 0.50: "
        f"{true_positives}"
    )

    print(
        f"False positives @ IoU 0.50: "
        f"{false_positives}"
    )

    print(
        f"False negatives @ IoU 0.50: "
        f"{false_negatives}"
    )

    print(
        f"Precision: "
        f"{precision:.4f}"
    )

    print(
        f"Recall: "
        f"{recall:.4f}"
    )

    print(
        f"F1: "
        f"{f1:.4f}"
    )

    print(
        f"mAP@50: "
        f"{map50:.4f}"
    )

    print(
        f"mAP@50:95: "
        f"{map50_95:.4f}"
    )

    return evaluation


# ============================================================
# VIDEO EVALUATION
# ============================================================

def evaluate_video(
    video_path,
    config_path,
    camera_id,
):

    video_path = Path(video_path)
    config_path = Path(config_path)

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video file not found: {video_path}"
        )

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}"
        )

    print("=" * 60)
    print("M03 INTRUSION MODULE EVALUATION")
    print("=" * 60)

    print(
        f"Video: {video_path}"
    )

    print(
        f"Config: {config_path}"
    )

    print(
        f"Camera ID: {camera_id}"
    )

    print()

    print(
        "Reading video information..."
    )

    video_info = get_video_info(
        video_path
    )

    print(
        f"Reported FPS: "
        f"{video_info['reported_fps']}"
    )

    print(
        f"Evaluation FPS: "
        f"{video_info['source_fps']}"
    )

    print(
        f"Decoded frames: "
        f"{video_info['decoded_frame_count']}"
    )

    if video_info[
        "fps_correction_applied"
    ]:

        print(
            "FPS correction: Applied"
        )

    print()

    print(
        "Initializing IntrusionPipeline..."
    )

    pipeline = IntrusionPipeline(
        str(config_path)
    )

    print(
        "Pipeline initialized."
    )

    print()

    print(
        "Running inference..."
    )

    print(
        "This may take some time..."
    )

    print()

    start_time = time.perf_counter()

    result = pipeline.process_video(
        str(video_path),
        camera_id,
        display=False,
    )

    end_time = time.perf_counter()

    processing_time = (
        end_time -
        start_time
    )

    frames_processed = int(
        result.get(
            "frames_processed",
            0,
        )
    )

    events = result.get(
        "events",
        [],
    )

    incidents = result.get(
        "incidents",
        [],
    )

    total_events = len(events)
    total_incidents = len(incidents)

    if processing_time > 0:

        processing_fps = (
            frames_processed /
            processing_time
        )

    else:

        processing_fps = 0.0

    source_fps = video_info[
        "source_fps"
    ]

    if source_fps > 0:

        real_time_factor = (
            processing_fps /
            source_fps
        )

    else:

        real_time_factor = 0.0

    real_time_percentage = (
        real_time_factor * 100
    )

    return {

        "module": {
            "id":
                "module_03_intrusion",

            "name":
                "Intrusion & Unauthorized "
                "Access Monitoring",
        },

        "evaluation_type":
            "video_end_to_end",

        "video": {

            "path":
                str(video_path),

            "reported_fps":
                video_info["reported_fps"],

            "source_fps":
                video_info["source_fps"],

            "fps_correction_applied":
                video_info[
                    "fps_correction_applied"
                ],

            "fps_note":
                video_info["fps_note"],

            "reported_frame_count":
                video_info[
                    "reported_frame_count"
                ],

            "decoded_frame_count":
                video_info[
                    "decoded_frame_count"
                ],

            "width":
                video_info["width"],

            "height":
                video_info["height"],
        },

        "pipeline": {

            "camera_id":
                camera_id,

            "frames_processed":
                frames_processed,

            "processing_time_seconds":
                round(
                    processing_time,
                    3,
                ),

            "processing_fps":
                round(
                    processing_fps,
                    3,
                ),

            "real_time_factor":
                round(
                    real_time_factor,
                    3,
                ),

            "real_time_percentage":
                round(
                    real_time_percentage,
                    2,
                ),
        },

        "events": {
            "total":
                total_events,
        },

        "incidents": {
            "total":
                total_incidents,
        },

        "detection_metrics": {

            "precision": None,
            "recall": None,
            "f1": None,
            "map50": None,
            "map50_95": None,

            "status":
                "NOT_AVAILABLE",

            "reason":
                "Run evaluation with "
                "--ground-truth.",
        },

        "tracking_metrics": {

            "id_switches": None,

            "status":
                "NOT_AVAILABLE",

            "reason":
                "Ground-truth tracking "
                "annotations are required.",
        },

        "operational_metrics": {

            "false_alerts": None,
            "missed_events": None,
            "false_alerts_per_camera_hour":
                None,

            "status":
                "NOT_AVAILABLE",

            "reason":
                "Human-reviewed ground-truth "
                "event labels are required.",
        },
    }


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    results,
    filename="m03_results.json",
):

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        RESULTS_DIR /
        filename
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
        )

    return output_path


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(results):

    video = results["video"]
    pipeline = results["pipeline"]

    print()
    print("=" * 50)
    print("M03 EVALUATION SUMMARY")
    print("=" * 50)

    print(
        f"Reported FPS: "
        f"{video['reported_fps']}"
    )

    print(
        f"Evaluation FPS: "
        f"{video['source_fps']}"
    )

    if video[
        "fps_correction_applied"
    ]:

        print(
            "FPS correction: Applied"
        )

    print(
        f"Decoded frames: "
        f"{video['decoded_frame_count']}"
    )

    print(
        f"Frames processed: "
        f"{pipeline['frames_processed']}"
    )

    print(
        f"Processing time: "
        f"{pipeline['processing_time_seconds']} s"
    )

    print(
        f"Processing FPS: "
        f"{pipeline['processing_fps']}"
    )

    print(
        f"Real-time factor: "
        f"{pipeline['real_time_factor']}"
    )

    print(
        f"Real-time performance: "
        f"{pipeline['real_time_percentage']}%"
    )

    print(
        f"Events generated: "
        f"{results['events']['total']}"
    )

    print(
        f"Incidents created: "
        f"{results['incidents']['total']}"
    )

    print()

    detection = results.get(
        "detection_metrics"
    )

    if (
        detection
        and detection.get("status")
        == "AVAILABLE"
    ):

        print(
            f"Detection Precision: "
            f"{detection['precision']}"
        )

        print(
            f"Detection Recall: "
            f"{detection['recall']}"
        )

        print(
            f"Detection F1: "
            f"{detection['f1']}"
        )

        print(
            f"Detection mAP@50: "
            f"{detection['map50']}"
        )

        print(
            f"Detection mAP@50:95: "
            f"{detection['map50_95']}"
        )

    else:

        print(
            "Detection metrics: "
            "NOT AVAILABLE"
        )

    print(
        "Tracking metrics: "
        "NOT AVAILABLE without "
        "tracking ground truth."
    )

    print(
        "Operational metrics: "
        "NOT AVAILABLE without "
        "human-reviewed event labels."
    )

    print(
        "=" * 50
    )


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate NEXORA Module 03 "
            "Intrusion Detection Pipeline."
        )
    )

    parser.add_argument(
        "--video",
        required=True,
        help="Path to evaluation video.",
    )

    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to M03 configuration file.",
    )

    parser.add_argument(
        "--camera-id",
        default="CAM-001",
        help="Camera identifier.",
    )

    parser.add_argument(
        "--output",
        default="m03_results.json",
        help="Output JSON filename.",
    )

    parser.add_argument(
        "--ground-truth",
        action="store_true",
        help=(
            "Run detection evaluation using "
            "annotated ground-truth images."
        ),
    )

    parser.add_argument(
        "--ground-truth-images",
        default="datasets/ground_truth/images",
        help="Ground-truth image directory.",
    )

    parser.add_argument(
        "--ground-truth-annotations",
        default="datasets/ground_truth/annotations",
        help="Ground-truth annotation directory.",
    )

    parser.add_argument(
        "--ground-truth-model",
        default="models/checkpoints/yolo11n.pt",
        help="YOLO model used for ground-truth evaluation.",
    )

    parser.add_argument(
        "--ground-truth-confidence",
        type=float,
        default=0.5,
        help="Confidence threshold.",
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Run video evaluation only when requested.
    # --------------------------------------------------------

    if args.ground_truth:

        # We still load the video evaluation if desired,
        # but the ground-truth evaluation can be run separately
        # to avoid spending time on the full video.
        results = {
            "module": {
                "id":
                    "module_03_intrusion",

                "name":
                    "Intrusion & Unauthorized "
                    "Access Monitoring",
            },

            "evaluation_type":
                "ground_truth_detection_only",

            "video": {},

            "pipeline": {},

            "events": {
                "total": None,
            },

            "incidents": {
                "total": None,
            },
        }

        detection_metrics = (
            evaluate_ground_truth(
                images_dir=
                    args.ground_truth_images,

                annotations_dir=
                    args.ground_truth_annotations,

                model_path=
                    args.ground_truth_model,

                confidence_threshold=
                    args.ground_truth_confidence,
            )
        )

        results[
            "detection_metrics"
        ] = detection_metrics

        results[
            "tracking_metrics"
        ] = {
            "id_switches": None,
            "status": "NOT_AVAILABLE",
            "reason":
                "Ground-truth tracking "
                "annotations are required.",
        }

        results[
            "operational_metrics"
        ] = {
            "false_alerts": None,
            "missed_events": None,
            "false_alerts_per_camera_hour":
                None,
            "status": "NOT_AVAILABLE",
            "reason":
                "Human-reviewed ground-truth "
                "event labels are required.",
        }

        output_path = save_results(
            results,
            args.output,
        )

        print(
            f"\nResults saved to: "
            f"{output_path}"
        )

        return

    # --------------------------------------------------------
    # Normal full-video evaluation
    # --------------------------------------------------------

    results = evaluate_video(
        video_path=args.video,
        config_path=args.config,
        camera_id=args.camera_id,
    )

    output_path = save_results(
        results,
        args.output,
    )

    print_summary(results)

    print()

    print(
        f"Results saved to: "
        f"{output_path}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
