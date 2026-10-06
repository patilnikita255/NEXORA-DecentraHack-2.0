from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ml.modules.module_03_intrusion.inference.pipeline import IntrusionPipeline


app = FastAPI(
    title="NEXORA API",
    version="1.0.0",
    description="Backend API for the NEXORA intelligent monitoring platform.",
)


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

M03_DIR = BASE_DIR / "ml" / "modules" / "module_03_intrusion"

M03_CONFIG = M03_DIR / "config" / "config.yaml"

M03_EVIDENCE_DIR = M03_DIR / "evidence"

M03_TEST_VIDEO = M03_DIR / "test_videos" / "test.mp4"


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Evidence Files
# ---------------------------------------------------------

if M03_EVIDENCE_DIR.exists():
    app.mount(
        "/api/v1/modules/module_03/evidence",
        StaticFiles(directory=str(M03_EVIDENCE_DIR)),
        name="m03-evidence",
    )


# ---------------------------------------------------------
# M03 Test Video
# ---------------------------------------------------------

@app.get("/api/v1/modules/module_03/video")
def get_m03_test_video():

    if not M03_TEST_VIDEO.exists():
        raise HTTPException(
            status_code=404,
            detail=f"M03 test video not found: {M03_TEST_VIDEO}",
        )

    return FileResponse(
        path=str(M03_TEST_VIDEO),
        media_type="video/mp4",
        filename="test.mp4",
    )

@app.get("/api/v1/modules/module_03/annotated-video")
def get_m03_annotated_video():
    annotated_video = (
        M03_DIR
        / "outputs"
        / "annotated_videos"
        / "CAM-001_annotated_h264.mp4"
    )

    if not annotated_video.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Annotated video not found: {annotated_video}",
        )

    return FileResponse(
        path=str(annotated_video),
        media_type="video/mp4",
        filename="CAM-001_annotated_h264.mp4",
    )

# ---------------------------------------------------------
# In-memory storage
# ---------------------------------------------------------

latest_m03_result = None


# ---------------------------------------------------------
# API Models
# ---------------------------------------------------------

class VideoProcessRequest(BaseModel):
    video_path: str
    camera_id: str = "CAM-01"
    display: bool = False


class IncidentReviewRequest(BaseModel):
    decision: Literal["CONFIRMED", "DISMISSED", "UNCERTAIN"]
    reviewer_id: str = "DEMO-REVIEWER"


# ---------------------------------------------------------
# Root
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "NEXORA API is running"
    }


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/api/v1/health")
def health():
    return {
        "status": "UP"
    }


# ---------------------------------------------------------
# Available Modules
# ---------------------------------------------------------

@app.get("/api/v1/modules")
def modules():
    return {
        "modules": [
            {
                "id": "module_03_intrusion",
                "name": "Intrusion & Unauthorized Access Monitoring",
                "status": "available",
            }
        ]
    }


# ---------------------------------------------------------
# M03 Status
# ---------------------------------------------------------

@app.get("/api/v1/modules/module_03/status")
def module_03_status():
    return {
        "module_id": "module_03_intrusion",
        "name": "Intrusion & Unauthorized Access Monitoring",
        "status": "ready",
        "config": str(M03_CONFIG),
    }


# ---------------------------------------------------------
# M03 Video Processing
# ---------------------------------------------------------

@app.post("/api/v1/modules/module_03/process")
def process_module_03(request: VideoProcessRequest):

    global latest_m03_result

    video_path = Path(request.video_path).expanduser()

    if not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Video not found: {video_path}",
        )

    if not M03_CONFIG.exists():
        raise HTTPException(
            status_code=500,
            detail=f"M03 configuration not found: {M03_CONFIG}",
        )

    try:
        pipeline = IntrusionPipeline(str(M03_CONFIG))

        result = pipeline.process_video(
            source=str(video_path),
            camera_id=request.camera_id,
            display=request.display,
        )

        latest_m03_result = result

        return {
            "status": "success",
            "module": "module_03_intrusion",
            "result": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"M03 processing failed: {str(exc)}",
        )


# ---------------------------------------------------------
# M03 Latest Result
# ---------------------------------------------------------

@app.get("/api/v1/modules/module_03/results")
def get_m03_results():

    if latest_m03_result is None:
        return {
            "status": "empty",
            "module": "module_03_intrusion",
            "message": "No M03 processing run has been completed yet.",
            "result": None,
        }

    return {
        "status": "success",
        "module": "module_03_intrusion",
        "result": latest_m03_result,
    }


# ---------------------------------------------------------
# M03 Incidents
# ---------------------------------------------------------

@app.get("/api/v1/modules/module_03/incidents")
def get_m03_incidents():

    if latest_m03_result is None:
        return {
            "status": "empty",
            "module": "module_03_intrusion",
            "count": 0,
            "incidents": [],
        }

    incidents = latest_m03_result.get("incidents", [])

    return {
        "status": "success",
        "module": "module_03_intrusion",
        "count": len(incidents),
        "incidents": incidents,
    }


# ---------------------------------------------------------
# M03 Incident Review
# ---------------------------------------------------------

@app.patch("/api/v1/modules/module_03/incidents/{incident_id}/review")
def review_m03_incident(
    incident_id: str,
    request: IncidentReviewRequest,
):

    global latest_m03_result

    if latest_m03_result is None:
        raise HTTPException(
            status_code=404,
            detail="No M03 processing result is available.",
        )

    incidents = latest_m03_result.get("incidents", [])

    target_incident = None

    for incident in incidents:
        if incident.get("incident_id") == incident_id:
            target_incident = incident
            break

    if target_incident is None:
        raise HTTPException(
            status_code=404,
            detail=f"Incident not found: {incident_id}",
        )

    reviewed_at = datetime.now(timezone.utc).isoformat()

    target_incident["status"] = request.decision

    target_incident["review"] = {
        "decision": request.decision,
        "reviewer_id": request.reviewer_id,
        "reviewed_at": reviewed_at,
    }

    return {
        "status": "success",
        "message": "Incident review updated.",
        "incident": target_incident,
    }
