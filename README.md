# NEXORA

NEXORA is an intelligent monitoring platform designed to combine computer vision, machine learning, backend services, and a web-based dashboard into a modular security and safety monitoring system.

The project is being developed as a modular platform where individual AI-based monitoring capabilities can be developed and integrated independently.

The current project contains the core frontend and backend structure along with the implementation of Module 03 — Intrusion & Unauthorized Access Monitoring.

## Project Overview

NEXORA follows this workflow:

Camera / Video Input
↓
AI / Computer Vision Module
↓
Event Detection
↓
Incident Generation
↓
Backend API
↓
Web Dashboard
↓
Human Review

The current implementation focuses on Module 03 — Intrusion & Unauthorized Access Monitoring.

## Current Module

### Module 03 — Intrusion & Unauthorized Access Monitoring

Module 03 analyzes CCTV footage to detect people and identify potential intrusion events using computer vision.

It currently supports:

- Person detection using YOLO11n
- Person tracking using ByteTrack
- Restricted-zone monitoring
- Tripwire monitoring
- Rule-based event generation
- Incident generation
- Evidence generation
- Annotated video generation
- Human-review workflow

Detailed documentation:

ml/modules/module_03_intrusion/README.md

## Technology Stack

### Frontend

- React
- React DOM
- Vite
- JavaScript
- HTML
- CSS

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

### Machine Learning

- Python 3.9.6
- Ultralytics YOLO11n
- ByteTrack
- OpenCV
- NumPy
- PyYAML

### Testing

- Pytest

## Project Structure

NEXORA/

    backend/
        app/
            main.py
        __init__.py

    frontend/
        src/
        package.json
        vite.config.js
        index.html

    ml/
        modules/
            module_03_intrusion/
                config/
                datasets/
                evaluation/
                inference/
                rules/
                tests/
                training/
                models/
                outputs/
                evidence/
                test_videos/
                README.md

    .gitignore
    README.md

## Backend

The NEXORA backend is implemented using FastAPI.

Main backend file:

backend/app/main.py

The backend provides APIs for:

- Health checking
- Available modules
- Module 03 status
- Video processing
- Test video access
- Annotated video access
- Module 03 results
- Incident retrieval
- Incident review

### Start Backend

From the project root:

    cd ~/Documents/NEXORA
    source .venv/bin/activate
    python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

Backend:

http://127.0.0.1:8000

## Frontend

The NEXORA frontend is built using React and Vite.

### Start Frontend

Open another terminal:

    cd ~/Documents/NEXORA/frontend
    npm install
    npm run dev

Frontend:

http://localhost:5173

## Running the Complete Project

Terminal 1 — Backend:

    cd ~/Documents/NEXORA
    source .venv/bin/activate
    python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

Terminal 2 — Frontend:

    cd ~/Documents/NEXORA/frontend
    npm run dev

Open:

http://localhost:5173

## Module 03 Processing

The Module 03 pipeline is:

Video
↓
YOLO11n Person Detection
↓
ByteTrack Tracking
↓
Restricted Zone / Tripwire Rules
↓
Event Generation
↓
Evidence
↓
Incident
↓
Human Review

Configuration:

ml/modules/module_03_intrusion/config/config.yaml

Main pipeline:

ml/modules/module_03_intrusion/inference/pipeline.py

## Important Design Principle

NEXORA separates detection, events, and incidents.

A detected person does not automatically mean that the person is unauthorized.

The AI system identifies potential security events according to configured rules. Human review can then be used to confirm, dismiss, or mark an incident as uncertain.

## Testing

Module 03 contains automated tests.

Run:

    cd ~/Documents/NEXORA
    source .venv/bin/activate
    pytest -q

## Evaluation

Module 03 includes an evaluation pipeline for measuring person-detection performance against available ground-truth data.

Detailed evaluation information is available in:

ml/modules/module_03_intrusion/README.md

## Git and Large Files

Large and generated files are intentionally excluded from Git.

These include:

- Python virtual environments
- Node.js dependencies
- Build outputs
- ML model checkpoints
- CCTV video files
- Generated evidence
- Generated ML outputs
- Logs
- Temporary files

The project .gitignore contains the corresponding rules.

## Current Development Status

Implemented:

- NEXORA project structure
- React frontend
- FastAPI backend
- Module 03 integration
- YOLO11n person detection
- ByteTrack tracking
- Restricted zones
- Tripwires
- Event rules
- Incident management
- Evidence generation
- Annotated video generation
- REST API integration
- Frontend monitoring workflow
- Automated tests
- Detection evaluation

## Future Improvements

Possible future development includes:

- Additional monitoring modules
- Live CCTV camera integration
- Database-backed incident storage
- Authentication and authorization
- Real-time notifications
- Multi-camera monitoring
- GPU acceleration
- Improved tracking evaluation
- Site-specific model training
- Cloud deployment
- Mobile application integration
- Advanced incident analytics

## Documentation

Detailed Module 03 documentation:

ml/modules/module_03_intrusion/README.md

The module documentation contains its architecture, configuration, inference workflow, rules, testing, evaluation, limitations, and development details.

## Project Purpose

NEXORA is being developed as a modular intelligent monitoring platform that can combine multiple AI-based safety and security capabilities into a single system.

The architecture is designed to allow additional computer-vision modules to be added without replacing the existing frontend and backend structure.

## License

This project is intended for academic, research, and prototype development purposes.

Third-party libraries, frameworks, datasets, and pretrained models remain subject to their respective licenses.
