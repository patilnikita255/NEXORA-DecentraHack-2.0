from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import cv2
from sympy import fps
import yaml
import numpy as np
from ultralytics import YOLO

from .detector import PersonDetector
from ..rules.event_rules import IntrusionRuleEngine
from ..rules.incident_manager import IncidentManager


class IntrusionPipeline:
    """
    Complete M03 inference pipeline.

    Video
        ↓
    YOLO11n Person Detection
        ↓
    ByteTrack
        ↓
    Restricted Zone Rules
        ↓
    Tripwire Rules
        ↓
    Intrusion Event Generation
        ↓
    Evidence Capture
        ↓
    Incident Creation

    Visualization:
        - Restricted zones
        - Tripwires
        - Person bounding boxes
        - Track IDs
        - Event banner

    Evidence:
        - Event frame
        - Pre-event video
        - Post-event video

    Incident:
        - Standard NEXORA incident object
        - PENDING review status
        - Human review fields
    """

    def __init__(self, config_path: str):
        self.config_path = Path(
            config_path
        ).resolve()

        with open(
            self.config_path,
            "r",
            encoding="utf-8"
        ) as file:
            self.config = yaml.safe_load(file)

        self.detector = PersonDetector(
            str(self.config_path)
        )

        self.rule_engine = IntrusionRuleEngine(
            self.config
        )

        # ----------------------------------------------------------
        # Incident manager
        # ----------------------------------------------------------

        self.incident_manager = IncidentManager()

        tracking_config = self.config[
            "tracking"
        ]

        self.tracking_enabled = bool(
            tracking_config["enabled"]
        )

        self.tracker = tracking_config[
            "tracker"
        ]

        model_path = Path(
            self.config["model"]["path"]
        )

        if not model_path.is_absolute():
            module_root = (
                self.config_path.parent.parent
            )

            model_path = (
                module_root / model_path
            )

        self.model = YOLO(
            str(model_path.resolve())
        )

        self.previous_detections = {}
        self.event_count = 0

        # ----------------------------------------------------------
        # Evidence configuration
        # ----------------------------------------------------------

        evidence_config = self.config.get(
            "evidence",
            {}
        )

        self.save_evidence_frame = bool(
            evidence_config.get(
                "save_frame",
                True
            )
        )

        self.save_evidence_clip = bool(
            evidence_config.get(
                "save_clip",
                True
            )
        )

        self.pre_event_seconds = float(
            evidence_config.get(
                "pre_event_seconds",
                5
            )
        )

        self.post_event_seconds = float(
            evidence_config.get(
                "post_event_seconds",
                5
            )
        )

        # ----------------------------------------------------------
        # Evidence directories
        # ----------------------------------------------------------

        self.module_root = (
            self.config_path.parent.parent
        )

        self.evidence_root = (
            self.module_root / "evidence"
        )

        self.evidence_frames_dir = (
            self.evidence_root / "frames"
        )

        self.evidence_clips_dir = (
            self.evidence_root / "clips"
        )

        # ----------------------------------------------------------
        # Annotated video output
        # ----------------------------------------------------------

        self.output_root = (
            self.module_root / "outputs"
        )

        self.annotated_videos_dir = (
            self.output_root / "annotated_videos"
        )

        self.annotated_videos_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.evidence_frames_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.evidence_clips_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # ----------------------------------------------------------
        # Video/evidence runtime state
        # ----------------------------------------------------------

        self.video_fps = 25.0

        self.pre_event_buffer = deque()

        self.pending_evidence = []

    # ==========================================================
    # FRAME PROCESSING
    # ==========================================================

    def process_frame(
        self,
        frame,
        camera_id: str,
        frame_id: int,
    ):
        if frame is None:
            raise ValueError(
                "Frame cannot be None."
            )

        # ------------------------------------------------------
        # Detection only mode
        # ------------------------------------------------------

        if not self.tracking_enabled:

            detections = self.detector.detect(
                frame,
                camera_id,
                frame_id,
            )

            events = []

            for detection in detections:

                events.extend(
                    self.rule_engine.check_detection(
                        detection
                    )
                )

            return detections, events

        # ------------------------------------------------------
        # YOLO + ByteTrack
        # ------------------------------------------------------

        results = self.model.track(
            source=frame,
            imgsz=self.config["model"][
                "input_size"
            ],
            conf=self.config["model"][
                "confidence_threshold"
            ],
            iou=self.config["model"][
                "iou_threshold"
            ],
            classes=[
                self.config["model"][
                    "person_class_id"
                ]
            ],
            tracker=self.tracker,
            persist=True,
            verbose=False,
        )

        detections = []

        if not results:
            return [], []

        result = results[0]

        if result.boxes is None:
            return [], []

        boxes = result.boxes

        for index in range(len(boxes)):

            class_id = int(
                boxes.cls[index].item()
            )

            if (
                class_id
                != self.config["model"][
                    "person_class_id"
                ]
            ):
                continue

            confidence = float(
                boxes.conf[index].item()
            )

            x1, y1, x2, y2 = (
                boxes.xyxy[index].tolist()
            )

            track_id = None

            if boxes.id is not None:

                track_id = int(
                    boxes.id[index].item()
                )

            detection = {
                "module": "module_03_intrusion",
                "camera_id": camera_id,
                "frame_id": frame_id,
                "timestamp": self._timestamp(),
                "track_id": track_id,
                "class_name": "person",
                "confidence": round(
                    confidence,
                    4
                ),
                "bbox": {
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2),
                },
            }

            detections.append(
                detection
            )

        # ------------------------------------------------------
        # Event processing
        # ------------------------------------------------------

        events = []

        current_time = datetime.now()

        for detection in detections:

            track_id = detection.get(
                "track_id"
            )

            if track_id is None:
                continue

            # Restricted zone
            events.extend(
                self.rule_engine.check_detection(
                    detection,
                    current_time=current_time,
                )
            )

            # Previous detection
            previous_detection = (
                self.previous_detections.get(
                    track_id
                )
            )

            # Tripwire
            events.extend(
                self.rule_engine.check_tripwires(
                    previous_detection,
                    detection,
                    current_time=current_time,
                )
            )

            # Save current detection
            self.previous_detections[
                track_id
            ] = detection

        return detections, events

    # ==========================================================
    # VIDEO PROCESSING
    # ==========================================================

    def process_video(
        self,
        source: str,
        camera_id: str,
        display: bool = False,
    ):
        video_source = source

        if (
            isinstance(source, str)
            and source.isdigit()
        ):
            video_source = int(source)

        capture = cv2.VideoCapture(
            video_source
        )

        if not capture.isOpened():
            raise RuntimeError(
                f"Could not open video source: {source}"
            )

        # ------------------------------------------------------
        # Reset run-specific state
        # ------------------------------------------------------

        self.event_count = 0
        self.previous_detections = {}
        self.pending_evidence = []
        self.pre_event_buffer = deque()

        # Use a fresh incident manager for every
        # complete video-processing run.
        self.incident_manager = IncidentManager()

        # ------------------------------------------------------
        # Get video properties
        # ------------------------------------------------------

        fps = capture.get(
            cv2.CAP_PROP_FPS
        )

        # Some video files can report an invalid
        # or unrealistic FPS through OpenCV.
        if (
            fps is None
            or fps <= 0
            or fps > 120
        ):
            print(
                f"Warning: Invalid FPS "
                f"reported by OpenCV: {fps}. "
                f"Defaulting to 25 FPS."
            )

            fps = 25.0

        self.video_fps = float(fps)

        video_width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        video_height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )


        # ------------------------------------------------------
        # Annotated output video
        # ------------------------------------------------------

        annotated_video_path = (
            self.annotated_videos_dir
            / f"{camera_id}_annotated.mp4"
        )

        video_writer = cv2.VideoWriter(
            str(annotated_video_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            self.video_fps,
            (
                video_width,
                video_height,
            ),
        )

        if not video_writer.isOpened():

            capture.release()

            raise RuntimeError(
                "Could not create annotated output video: "
                f"{annotated_video_path}"
            )

        # ------------------------------------------------------
        # Calculate evidence buffer size
        # ------------------------------------------------------

        pre_event_frames = max(
            1,
            int(
                self.pre_event_seconds
                * self.video_fps
            )
        )

        post_event_frames = max(
            1,
            int(
                self.post_event_seconds
                * self.video_fps
            )
        )

        # Store approximately the previous
        # configured number of seconds.
        self.pre_event_buffer = deque(
            maxlen=pre_event_frames
        )

        frame_id = 0

        all_results = []

        total_events = []

        try:

            while True:

                success, frame = (
                    capture.read()
                )

                if not success:
                    break

                frame_id += 1

                # --------------------------------------------------
                # Process frame
                # --------------------------------------------------

                detections, events = (
                    self.process_frame(
                        frame=frame,
                        camera_id=camera_id,
                        frame_id=frame_id,
                    )
                )

                # --------------------------------------------------
                # Draw current frame
                # --------------------------------------------------

                annotated = self._draw_frame(
                    frame,
                    detections,
                    events,
                )

                # --------------------------------------------------
                # Save annotated frame to output video
                # --------------------------------------------------

                video_writer.write(
                    annotated
                )

                # --------------------------------------------------
                # Continue existing evidence clips
                # --------------------------------------------------

                self._update_pending_evidence(
                    annotated
                )

                # --------------------------------------------------
                # Event output
                # --------------------------------------------------

                if events:

                    total_events.extend(
                        events
                    )

                    for event in events:

                        self.event_count += 1

                        # ------------------------------------------
                        # Create evidence
                        # ------------------------------------------

                        evidence = (
                            self._start_evidence_capture(
                                event=event,
                                annotated_frame=annotated,
                                frame_id=frame_id,
                                post_event_frames=post_event_frames,
                                video_width=video_width,
                                video_height=video_height,
                            )
                        )

                        if evidence:
                            event[
                                "evidence"
                            ] = evidence

                        print()
                        print(
                            "🚨 M03 EVENT DETECTED"
                        )

                        print(event)

                # --------------------------------------------------
                # Add current frame to pre-event buffer
                #
                # This happens AFTER event handling so that
                # the buffer represents frames before the event.
                # --------------------------------------------------

                self.pre_event_buffer.append(
                    annotated.copy()
                )

                # --------------------------------------------------
                # Store result
                # --------------------------------------------------

                all_results.append(
                    {
                        "frame_id": frame_id,
                        "detections": detections,
                        "events": events,
                    }
                )

                # --------------------------------------------------
                # Display
                # --------------------------------------------------

                if display:

                    cv2.imshow(
                        "NEXORA - M03 Intrusion",
                        annotated,
                    )

                    key = (
                        cv2.waitKey(1)
                        & 0xFF
                    )

                    if key == ord("q"):

                        print(
                            "Video stopped by user."
                        )

                        break

        finally:

            capture.release()

            video_writer.release()

            if display:

                cv2.destroyAllWindows()

            # ------------------------------------------------------
            # Finalize evidence clips
            # ------------------------------------------------------

            self._finalize_all_pending_evidence()

        # ----------------------------------------------------------
        # Create incidents AFTER evidence finalization
        #
        # This is intentional:
        # event -> evidence -> incident
        #
        # Therefore an incident can contain both the event frame
        # and the completed post-event video clip.
        # ----------------------------------------------------------

        incidents = []

        for event in total_events:

            try:

                incident = (
                    self.incident_manager.create_incident(
                        event
                    )
                )

                incidents.append(
                    incident
                )

                print()
                print(
                    "🚨 M03 INCIDENT CREATED"
                )

                print(incident)

            except (KeyError, ValueError) as error:

                print()
                print(
                    "⚠️ M03 INCIDENT CREATION FAILED"
                )

                print(
                    f"Event ID: "
                    f"{event.get('event_id')}"
                )

                print(
                    f"Reason: {error}"
                )

        # ----------------------------------------------------------
        # Summary
        # ----------------------------------------------------------

        print()

        print(
            "========================================"
        )

        print(
            "M03 VIDEO PROCESSING COMPLETE"
        )

        print(
            "========================================"
        )

        print(
            f"Frames processed: {frame_id}"
        )

        print(
            f"Events generated: "
            f"{len(total_events)}"
        )

        print(
            f"Incidents created: "
            f"{len(incidents)}"
        )

        print(
            f"Evidence directory: "
            f"{self.evidence_root}"
        )

        return {
            "camera_id": camera_id,
            "frames_processed": frame_id,
            "annotated_video": str(
                annotated_video_path.relative_to(
                    self.module_root
                )
            ),
            "events": total_events,
            "incidents": incidents,
            "results": all_results,
        }

    # ==========================================================
    # EVIDENCE CAPTURE
    # ==========================================================

    def _start_evidence_capture(
        self,
        event,
        annotated_frame,
        frame_id,
        post_event_frames,
        video_width,
        video_height,
    ):
        """
        Start evidence capture for one event.

        Evidence contains:
        - Event frame
        - Previous frames from rolling buffer
        - Future frames for post-event duration
        """

        event_id = event.get(
            "event_id",
            f"EVT-{frame_id}"
        )

        safe_event_id = (
            str(event_id)
            .replace("/", "_")
            .replace(" ", "_")
        )

        evidence = {}

        # ----------------------------------------------------------
        # Save event frame
        # ----------------------------------------------------------

        if self.save_evidence_frame:

            frame_filename = (
                f"{safe_event_id}.jpg"
            )

            frame_path = (
                self.evidence_frames_dir
                / frame_filename
            )

            success = cv2.imwrite(
                str(frame_path),
                annotated_frame,
            )

            if success:

                evidence[
                    "frame"
                ] = str(
                    frame_path.relative_to(
                        self.module_root
                    )
                )

        # ----------------------------------------------------------
        # Save clip
        # ----------------------------------------------------------

        writer = None
        clip_path = None

        if self.save_evidence_clip:

            clip_filename = (
                f"{safe_event_id}.mp4"
            )

            clip_path = (
                self.evidence_clips_dir
                / clip_filename
            )

            writer = cv2.VideoWriter(
                str(clip_path),
                cv2.VideoWriter_fourcc(
                    *"mp4v"
                ),
                self.video_fps,
                (
                    video_width,
                    video_height,
                ),
            )

            if not writer.isOpened():

                writer.release()

                writer = None

                clip_path = None

            else:

                # ----------------------------------------------
                # Write pre-event frames
                # ----------------------------------------------

                for buffered_frame in (
                    self.pre_event_buffer
                ):
                    writer.write(
                        buffered_frame
                    )

                # ----------------------------------------------
                # Write event frame
                # ----------------------------------------------

                writer.write(
                    annotated_frame
                )

        # ----------------------------------------------------------
        # Track pending evidence
        # ----------------------------------------------------------

        pending = {
            "event": event,
            "writer": writer,
            "clip_path": clip_path,
            "remaining_frames": (
                post_event_frames
                if writer is not None
                else 0
            ),
            "frame_path": evidence.get(
                "frame"
            ),
        }

        if writer is None:

            # No clip was created.
            # The event still keeps frame evidence.
            if evidence:
                return evidence

            return None

        self.pending_evidence.append(
            pending
        )

        # Frame path can be returned immediately.
        #
        # Clip path is attached after the
        # post-event frames have been captured.

        if evidence:
            return evidence

        return {
            "clip": str(
                clip_path.relative_to(
                    self.module_root
                )
            )
        }

    def _update_pending_evidence(
        self,
        annotated_frame
    ):
        """
        Write the current frame to all active
        evidence clips.

        Once the configured post-event duration
        is reached, finalize the clip and attach
        its path to the event.
        """

        if not self.pending_evidence:
            return

        completed = []

        for pending in self.pending_evidence:

            writer = pending.get(
                "writer"
            )

            if writer is None:
                completed.append(
                    pending
                )
                continue

            writer.write(
                annotated_frame
            )

            pending[
                "remaining_frames"
            ] -= 1

            if (
                pending[
                    "remaining_frames"
                ]
                <= 0
            ):

                self._finalize_pending_evidence(
                    pending
                )

                completed.append(
                    pending
                )

        for pending in completed:

            if pending in self.pending_evidence:

                self.pending_evidence.remove(
                    pending
                )

    def _finalize_pending_evidence(
        self,
        pending
    ):
        """
        Finalize one evidence clip and attach
        the relative evidence path to the event.
        """

        writer = pending.get(
            "writer"
        )

        if writer is not None:

            writer.release()

            pending[
                "writer"
            ] = None

        clip_path = pending.get(
            "clip_path"
        )

        if clip_path is not None:

            pending[
                "event"
            ][
                "evidence"
            ] = pending[
                "event"
            ].get(
                "evidence",
                {}
            )

            pending[
                "event"
            ][
                "evidence"
            ][
                "clip"
            ] = str(
                clip_path.relative_to(
                    self.module_root
                )
            )

    def _finalize_all_pending_evidence(
        self
    ):
        """
        Finalize any evidence clips still active
        when the video ends.
        """

        for pending in list(
            self.pending_evidence
        ):

            self._finalize_pending_evidence(
                pending
            )

        self.pending_evidence.clear()

    # ==========================================================
    # FRAME DRAWING
    # ==========================================================

    def _draw_frame(
        self,
        frame,
        detections,
        events,
    ):

        output = frame.copy()

        # ------------------------------------------------------
        # Restricted zones
        # ------------------------------------------------------

        self._draw_restricted_zones(
            output
        )

        # ------------------------------------------------------
        # Tripwires
        # ------------------------------------------------------

        self._draw_tripwires(
            output
        )

        # ------------------------------------------------------
        # Person detections
        # ------------------------------------------------------

        for detection in detections:

            bbox = detection["bbox"]

            x1 = bbox["x1"]
            y1 = bbox["y1"]
            x2 = bbox["x2"]
            y2 = bbox["y2"]

            track_id = detection[
                "track_id"
            ]

            confidence = detection[
                "confidence"
            ]

            label = (
                f"person "
                f"ID:{track_id} "
                f"{confidence:.2f}"
            )

            # Person bounding box
            cv2.rectangle(
                output,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2,
            )

            # Label
            cv2.putText(
                output,
                label,
                (
                    x1,
                    max(
                        y1 - 10,
                        20
                    ),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

            # Bottom-center tracking point
            center_x = int(
                (x1 + x2) / 2
            )

            center_y = int(y2)

            cv2.circle(
                output,
                (
                    center_x,
                    center_y
                ),
                5,
                (255, 255, 0),
                -1,
            )

        # ------------------------------------------------------
        # Event banner
        # ------------------------------------------------------

        if events:

            cv2.rectangle(
                output,
                (0, 0),
                (
                    output.shape[1],
                    65,
                ),
                (0, 0, 255),
                -1,
            )

            event_text = (
                "INTRUSION EVENT DETECTED"
            )

            cv2.putText(
                output,
                event_text,
                (20, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2,
            )

        return output

    # ==========================================================
    # RESTRICTED ZONE DRAWING
    # ==========================================================

    def _draw_restricted_zones(
        self,
        frame,
    ):

        zones = (
            self.config
            .get("zones", {})
            .get(
                "restricted_zones",
                []
            )
        )

        for zone in zones:

            polygon = zone.get(
                "polygon",
                []
            )

            if len(polygon) < 3:
                continue

            points = [
                tuple(point)
                for point in polygon
            ]

            polygon_array = np.array(
                points,
                dtype=np.int32
            )

            # Transparent fill
            overlay = frame.copy()

            cv2.fillPoly(
                overlay,
                [polygon_array],
                (0, 0, 255)
            )

            cv2.addWeighted(
                overlay,
                0.15,
                frame,
                0.85,
                0,
                frame,
            )

            # Boundary
            cv2.polylines(
                frame,
                [polygon_array],
                True,
                (0, 0, 255),
                3,
            )

            # Zone name
            x, y = points[0]

            cv2.putText(
                frame,
                zone.get(
                    "name",
                    "Restricted Zone"
                ),
                (
                    x,
                    max(
                        y - 10,
                        20
                    ),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

    # ==========================================================
    # TRIPWIRE DRAWING
    # ==========================================================

    def _draw_tripwires(
        self,
        frame,
    ):

        tripwires = (
            self.config
            .get("zones", {})
            .get(
                "tripwires",
                []
            )
        )

        for tripwire in tripwires:

            line = tripwire.get(
                "line",
                []
            )

            if len(line) != 2:
                continue

            point_a = tuple(
                line[0]
            )

            point_b = tuple(
                line[1]
            )

            # Tripwire line
            cv2.line(
                frame,
                point_a,
                point_b,
                (255, 0, 0),
                4,
            )

            # Point A
            cv2.circle(
                frame,
                point_a,
                8,
                (255, 0, 0),
                -1,
            )

            # Point B
            cv2.circle(
                frame,
                point_b,
                8,
                (255, 0, 0),
                -1,
            )

            # A label
            cv2.putText(
                frame,
                "A",
                (
                    point_a[0] + 10,
                    point_a[1] - 10,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2,
            )

            # B label
            cv2.putText(
                frame,
                "B",
                (
                    point_b[0] + 10,
                    point_b[1] - 10,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2,
            )

            # Direction arrow A -> B
            midpoint_x = int(
                (
                    point_a[0]
                    + point_b[0]
                ) / 2
            )

            midpoint_y = int(
                (
                    point_a[1]
                    + point_b[1]
                ) / 2
            )

            cv2.arrowedLine(
                frame,
                point_a,
                point_b,
                (255, 0, 0),
                3,
                tipLength=0.06,
            )

            cv2.putText(
                frame,
                "A -> B",
                (
                    midpoint_x + 10,
                    midpoint_y,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2,
            )

            # Tripwire name
            cv2.putText(
                frame,
                tripwire.get(
                    "name",
                    "Tripwire"
                ),
                (
                    point_a[0] + 15,
                    point_a[1] + 30,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 0, 0),
                2,
            )

    # ==========================================================
    # TIMESTAMP
    # ==========================================================

    @staticmethod
    def _timestamp():

        return datetime.now(
            timezone.utc
        ).isoformat()


# ==============================================================
# MAIN
# ==============================================================

if __name__ == "__main__":

    module_root = Path(
        __file__
    ).resolve().parents[1]

    config_path = (
        module_root
        / "config"
        / "config.yaml"
    )

    video_path = (
        module_root
        / "test_videos"
        / "test.mp4"
    )

    pipeline = IntrusionPipeline(
        str(config_path)
    )

    pipeline.process_video(
        source=str(video_path),
        camera_id="CAM-001",
        display=True,
    )
