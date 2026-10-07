from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import asyncio
import base64
import shutil
import uuid

import cv2

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ml.modules.module_03_intrusion.inference.pipeline import (
    IntrusionPipeline,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="NEXORA Backend",
    version="1.0.0",
    description="NEXORA Intelligent Monitoring Backend",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

M03_DIR = (
    BASE_DIR
    / "ml"
    / "modules"
    / "module_03_intrusion"
)

M03_CONFIG = (
    M03_DIR
    / "config"
    / "config.yaml"
)

M03_TEST_VIDEO = (
    M03_DIR
    / "test_videos"
    / "test.mp4"
)

M03_UPLOAD_DIR = (
    M03_DIR
    / "uploads"
)

M03_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

M03_EVIDENCE_DIR = (
    M03_DIR
    / "evidence"
)

M03_EVIDENCE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# STATIC EVIDENCE
# ============================================================

app.mount(
    "/api/v1/modules/module_03/evidence",
    StaticFiles(
        directory=str(M03_EVIDENCE_DIR)
    ),
    name="m03-evidence",
)


# ============================================================
# GLOBAL RESULT
# ============================================================

latest_m03_result = None


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
def root():

    return {
        "name": "NEXORA",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/api/v1/health")
def health():

    return {
        "status": "UP"
    }


# ============================================================
# MODULE LIST
# ============================================================

@app.get("/api/v1/modules")
def get_modules():

    return {
        "modules": [
            {
                "id": "module_03",
                "name": (
                    "Intrusion & Unauthorized "
                    "Access Monitoring"
                ),
                "status": "READY",
            }
        ]
    }


# ============================================================
# M03 STATUS
# ============================================================

@app.get(
    "/api/v1/modules/module_03/status"
)
def module_03_status():

    return {
        "module": "module_03",
        "name": (
            "Intrusion & Unauthorized "
            "Access Monitoring"
        ),
        "status": "READY",
        "model": "YOLO11n",
        "tracking": "ByteTrack",
        "review": "Human-in-the-loop",
        "config_exists": M03_CONFIG.exists(),
        "test_video_exists": M03_TEST_VIDEO.exists(),
        "upload_directory": str(
            M03_UPLOAD_DIR
        ),
    }


# ============================================================
# M03 ORIGINAL VIDEO
# ============================================================

@app.get(
    "/api/v1/modules/module_03/video"
)
def get_m03_video():

    if not M03_TEST_VIDEO.exists():

        raise HTTPException(
            status_code=404,
            detail="M03 test video not found.",
        )

    return FileResponse(
        path=str(M03_TEST_VIDEO),
        media_type="video/mp4",
        filename="test.mp4",
    )


# ============================================================
# M03 ANNOTATED VIDEO
# ============================================================

@app.get(
    "/api/v1/modules/module_03/annotated-video"
)
def get_m03_annotated_video():

    candidates = [
        M03_DIR
        / "outputs"
        / "CAM-001_annotated_h264.mp4",

        M03_DIR
        / "outputs"
        / "CAM-001_annotated.mp4",

        M03_DIR
        / "CAM-001_annotated_h264.mp4",

        M03_DIR
        / "CAM-001_annotated.mp4",
    ]

    for video_path in candidates:

        if video_path.exists():

            return FileResponse(
                path=str(video_path),
                media_type="video/mp4",
                filename=video_path.name,
            )

    raise HTTPException(
        status_code=404,
        detail=(
            "Annotated M03 video not found. "
            "Use the WebSocket streaming endpoint "
            "for dynamic processing."
        ),
    )


# ============================================================
# UPLOAD VIDEO
# ============================================================

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
}


@app.post(
    "/api/v1/modules/module_03/upload"
)
async def upload_m03_video(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    original_filename = file.filename

    extension = (
        Path(original_filename)
        .suffix
        .lower()
    )

    if extension not in ALLOWED_VIDEO_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported video format. "
                "Allowed formats: "
                ".mp4, .avi, .mov, .mkv, .webm"
            ),
        )

    upload_id = uuid.uuid4().hex

    saved_filename = (
        f"{upload_id}{extension}"
    )

    destination = (
        M03_UPLOAD_DIR
        / saved_filename
    )

    try:

        with destination.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

    except Exception as error:

        if destination.exists():

            destination.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save uploaded video: "
                f"{error}"
            ),
        )

    finally:

        await file.close()

    return {
        "status": "success",
        "message": (
            "Video uploaded successfully."
        ),
        "filename": original_filename,
        "upload_id": upload_id,
        "extension": extension,
        "video_path": str(destination),
    }


# ============================================================
# FIND UPLOADED VIDEO FROM ID
# ============================================================

def resolve_uploaded_video(
    upload_id: str,
):

    if not upload_id:

        return None

    # Prevent path traversal.
    if (
        "/" in upload_id
        or "\\" in upload_id
        or ".." in upload_id
    ):

        return None

    matches = list(
        M03_UPLOAD_DIR.glob(
            f"{upload_id}.*"
        )
    )

    for path in matches:

        if (
            path.is_file()
            and path.suffix.lower()
            in ALLOWED_VIDEO_EXTENSIONS
        ):

            return path

    return None


# ============================================================
# M03 PROCESS REQUEST MODEL
# ============================================================

class M03ProcessRequest(BaseModel):

    video_path: str = None

    upload_id: str = None

    camera_id: str = "CAM-01"

    display: bool = False


# ============================================================
# M03 PROCESS
# ============================================================

@app.post(
    "/api/v1/modules/module_03/process"
)
def process_m03_video(
    request: M03ProcessRequest,
):

    global latest_m03_result

    # --------------------------------------------------------
    # Resolve video
    # --------------------------------------------------------

    video_path = None

    if request.upload_id:

        video_path = resolve_uploaded_video(
            request.upload_id
        )

        if video_path is None:

            raise HTTPException(
                status_code=404,
                detail="Uploaded video not found.",
            )

    elif request.video_path:

        video_path = Path(
            request.video_path
        ).expanduser()

    else:

        video_path = M03_TEST_VIDEO

    if not video_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                f"Video not found: "
                f"{video_path}"
            ),
        )

    # --------------------------------------------------------
    # Validate configuration
    # --------------------------------------------------------

    if not M03_CONFIG.exists():

        raise HTTPException(
            status_code=500,
            detail=(
                "M03 configuration "
                "not found."
            ),
        )

    # --------------------------------------------------------
    # Initialize pipeline
    # --------------------------------------------------------

    try:

        pipeline = IntrusionPipeline(
            str(M03_CONFIG)
        )

        result = pipeline.process_video(
            video_path=str(video_path),
            camera_id=request.camera_id,
            display=request.display,
        )

        latest_m03_result = result

        return {
            "status": "success",
            "result": result,
        }

    except Exception as error:

        print(
            "M03 processing error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# M03 RESULTS
# ============================================================

@app.get(
    "/api/v1/modules/module_03/results"
)
def get_m03_results():

    if latest_m03_result is None:

        return {
            "status": "success",
            "result": None,
        }

    return {
        "status": "success",
        "result": latest_m03_result,
    }


# ============================================================
# M03 INCIDENTS
# ============================================================

@app.get(
    "/api/v1/modules/module_03/incidents"
)
def get_m03_incidents():

    if latest_m03_result is None:

        return {
            "status": "success",
            "incidents": [],
        }

    return {
        "status": "success",
        "incidents": (
            latest_m03_result.get(
                "incidents",
                [],
            )
        ),
    }


# ============================================================
# INCIDENT REVIEW MODEL
# ============================================================

class IncidentReviewRequest(BaseModel):

    status: Literal[
        "PENDING",
        "CONFIRMED",
        "DISMISSED",
        "UNCERTAIN",
        "RESOLVED",
    ]

    reviewer: str = "operator"

    notes: str = ""


# ============================================================
# REVIEW INCIDENT
# ============================================================

@app.patch(
    "/api/v1/modules/module_03/incidents/{incident_id}/review"
)
def review_m03_incident(
    incident_id: str,
    request: IncidentReviewRequest,
):

    if latest_m03_result is None:

        raise HTTPException(
            status_code=404,
            detail="No M03 incidents available.",
        )

    incidents = latest_m03_result.get(
        "incidents",
        [],
    )

    for incident in incidents:

        if (
            incident.get("incident_id")
            == incident_id
        ):

            incident["status"] = (
                request.status
            )

            incident["reviewer"] = (
                request.reviewer
            )

            incident["review_notes"] = (
                request.notes
            )

            incident["reviewed_at"] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            return {
                "status": "success",
                "incident": incident,
            }

    raise HTTPException(
        status_code=404,
        detail=(
            f"Incident not found: "
            f"{incident_id}"
        ),
    )


# ============================================================
# M03 WEBSOCKET STREAM
# ============================================================

@app.websocket(
    "/api/v1/modules/module_03/stream"
)
async def m03_stream(
    websocket: WebSocket,
):

    await websocket.accept()

    pipeline = None
    capture = None

    try:

        # ====================================================
        # RECEIVE INITIAL CONFIGURATION
        # ====================================================

        initial_message = (
            await websocket.receive_json()
        )

        upload_id = initial_message.get(
            "upload_id"
        )

        video_path_value = initial_message.get(
            "video_path"
        )

        camera_id = initial_message.get(
            "camera_id",
            "CAM-01",
        )

        # ----------------------------------------------------
        # Resolve upload_id first
        # ----------------------------------------------------

        if upload_id:

            video_path = (
                resolve_uploaded_video(
                    upload_id
                )
            )

            if video_path is None:

                await websocket.send_json(
                    {
                        "type": "error",
                        "message": (
                            "Uploaded video "
                            "not found."
                        ),
                    }
                )

                await websocket.close()

                return

        # ----------------------------------------------------
        # Backward compatibility:
        # allow existing video_path clients
        # ----------------------------------------------------

        elif video_path_value:

            video_path = Path(
                video_path_value
            ).expanduser()

        else:

            await websocket.send_json(
                {
                    "type": "error",
                    "message": (
                        "No upload_id or "
                        "video_path provided."
                    ),
                }
            )

            await websocket.close()

            return

        # ====================================================
        # CHECK VIDEO
        # ====================================================

        if not video_path.exists():

            await websocket.send_json(
                {
                    "type": "error",
                    "message": (
                        "Video not found: "
                        f"{video_path}"
                    ),
                }
            )

            await websocket.close()

            return

        # ====================================================
        # CHECK CONFIGURATION
        # ====================================================

        if not M03_CONFIG.exists():

            await websocket.send_json(
                {
                    "type": "error",
                    "message": (
                        "M03 configuration "
                        "not found."
                    ),
                }
            )

            await websocket.close()

            return

        # ====================================================
        # INITIALIZE PIPELINE
        # ====================================================

        pipeline = IntrusionPipeline(
            str(M03_CONFIG)
        )

        # ====================================================
        # OPEN VIDEO
        # ====================================================

        capture = cv2.VideoCapture(
            str(video_path)
        )

        if not capture.isOpened():

            await websocket.send_json(
                {
                    "type": "error",
                    "message": (
                        "Could not open "
                        "uploaded video."
                    ),
                }
            )

            await websocket.close()

            return

        # ====================================================
        # VIDEO INFORMATION
        # ====================================================

        fps = capture.get(
            cv2.CAP_PROP_FPS
        )

        if (
            fps is None
            or fps <= 0
            or fps > 120
        ):

            fps = 25.0

        width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        # ====================================================
        # RESET PIPELINE STATE
        # ====================================================

        pipeline.video_fps = float(fps)

        pipeline.event_count = 0

        pipeline.previous_detections = {}

        pipeline.pending_evidence = []

        pipeline.pre_event_buffer.clear()

        # ----------------------------------------------------
        # Fresh incident manager
        # ----------------------------------------------------

        from ml.modules.module_03_intrusion.rules.incident_manager import (
            IncidentManager,
        )

        pipeline.incident_manager = (
            IncidentManager()
        )

        # ----------------------------------------------------
        # Scale zones/tripwires to THIS video's resolution.
        #
        # process_video() does this internally, but the
        # websocket path drives process_frame() directly per
        # frame instead of going through process_video(), so
        # it must be called explicitly here before the frame
        # loop starts.
        # ----------------------------------------------------

        pipeline.configure_zones_for_resolution(
            width,
            height,
        )

        frame_id = 0

        total_events = []

        incidents = []

        # ====================================================
        # SEND STARTED MESSAGE
        # ====================================================

        await websocket.send_json(
            {
                "type": "started",
                "camera_id": camera_id,
                "upload_id": upload_id,
                "width": width,
                "height": height,
                "fps": fps,
            }
        )

        # ====================================================
        # FRAME PROCESSING LOOP
        # ====================================================

        while True:

            # ------------------------------------------------
            # Read next frame
            # ------------------------------------------------

            success, frame = (
                capture.read()
            )

            if not success:

                break

            frame_id += 1

            # ------------------------------------------------
            # M03 PROCESSING
            # ------------------------------------------------

            detections, events = (
                pipeline.process_frame(
                    frame=frame,
                    camera_id=camera_id,
                    frame_id=frame_id,
                )
            )

            # ------------------------------------------------
            # DRAW ANNOTATIONS
            # ------------------------------------------------

            annotated = (
                pipeline._draw_frame(
                    frame,
                    detections,
                    events,
                )
            )

            # ------------------------------------------------
            # EVENTS
            # ------------------------------------------------

            if events:

                total_events.extend(
                    events
                )

                for event in events:

                    pipeline.event_count += 1

                    try:

                        evidence = (
                            pipeline._start_evidence_capture(
                                event=event,
                                annotated_frame=annotated,
                                frame_id=frame_id,
                                post_event_frames=max(
                                    1,
                                    int(
                                        pipeline.post_event_seconds
                                        * fps
                                    ),
                                ),
                                video_width=width,
                                video_height=height,
                            )
                        )

                        if evidence:

                            event[
                                "evidence"
                            ] = evidence

                    except Exception as evidence_error:

                        print(
                            "Evidence error:",
                            evidence_error,
                        )

            # ------------------------------------------------
            # EVIDENCE HANDLING
            # ------------------------------------------------

            pipeline._update_pending_evidence(
                annotated
            )

            pipeline.pre_event_buffer.append(
                annotated.copy()
            )

            # ------------------------------------------------
            # ENCODE JPEG
            # ------------------------------------------------

            success_encode, buffer = (
                cv2.imencode(
                    ".jpg",
                    annotated,
                    [
                        cv2.IMWRITE_JPEG_QUALITY,
                        75,
                    ],
                )
            )

            if not success_encode:

                continue

            encoded_frame = (
                base64.b64encode(
                    buffer.tobytes()
                ).decode("utf-8")
            )

            # ------------------------------------------------
            # SEND FRAME
            # ------------------------------------------------

            await websocket.send_json(
                {
                    "type": "frame",
                    "frame_id": frame_id,
                    "camera_id": camera_id,
                    "timestamp": (
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                    ),
                    "detections": len(
                        detections
                    ),
                    "events": len(
                        events
                    ),
                    "image": encoded_frame,
                }
            )

            # ------------------------------------------------
            # Allow WebSocket event loop to continue
            # ------------------------------------------------

            await asyncio.sleep(0)

        # ====================================================
        # FINALIZE EVIDENCE
        # ====================================================

        try:

            pipeline._finalize_all_pending_evidence()

        except Exception as evidence_error:

            print(
                "Evidence finalization error:",
                evidence_error,
            )

        # ====================================================
        # CREATE INCIDENTS
        # ====================================================

        for event in total_events:

            try:

                incident = (
                    pipeline.incident_manager
                    .create_incident(event)
                )

                incidents.append(
                    incident
                )

            except (
                KeyError,
                ValueError,
            ) as error:

                print(
                    "Incident creation failed:",
                    error,
                )

        # ====================================================
        # SAVE LATEST RESULT
        # ====================================================

        latest_m03_result = {
            "camera_id": camera_id,
            "upload_id": upload_id,
            "frames_processed": frame_id,
            "events": total_events,
            "incidents": incidents,
            "fps": fps,
            "video_path": str(
                video_path
            ),
        }

        # ====================================================
        # SEND COMPLETION
        # ====================================================

        await websocket.send_json(
            {
                "type": "complete",
                "camera_id": camera_id,
                "upload_id": upload_id,
                "frames_processed": frame_id,
                "events": len(
                    total_events
                ),
                "incidents": incidents,
            }
        )

    # ========================================================
    # CLIENT DISCONNECTED
    # ========================================================

    except WebSocketDisconnect:

        print(
            "M03 WebSocket disconnected."
        )

    # ========================================================
    # OTHER STREAMING ERROR
    # ========================================================

    except Exception as exc:

        print(
            "M03 streaming error:",
            exc,
        )

        try:

            await websocket.send_json(
                {
                    "type": "error",
                    "message": str(exc),
                }
            )

        except Exception:

            pass

    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        if capture is not None:

            capture.release()

        print(
            "M03 stream closed."
        )