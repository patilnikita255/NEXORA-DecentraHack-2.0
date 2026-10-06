# Module 03 — Intrusion & Unauthorized Access Monitoring

## 1. Module Overview

Module 03 of the NEXORA platform provides CCTV-based intrusion and unauthorized-access monitoring.

The module uses a pretrained YOLO11n model to detect people in video frames, ByteTrack to maintain person identities across frames, and rule-based logic to identify potentially unauthorized access events.

### Processing Flow

CCTV / Video
↓
YOLO11n Person Detection
↓
ByteTrack Tracking
↓
Restricted Zone / Tripwire Rules
↓
Intrusion Events
↓
Evidence Frame + Video Clip
↓
Incident Management
↓
Human Review

### Main Features

- Person detection
- Person tracking
- Restricted-zone monitoring
- Virtual tripwire monitoring
- Event generation
- Incident creation
- Evidence generation
- Ground-truth detection evaluation
- Edge-case testing
- Human-review-ready incident states

---

## 2. Objective

The objective of Module 03 is to monitor video streams and identify situations that may represent unauthorized access.

The system should:

1. Detect people in CCTV/video frames.
2. Track detected people across frames.
3. Monitor configured restricted areas.
4. Monitor configured virtual tripwires.
5. Apply event rules.
6. Generate intrusion-related events.
7. Create incidents from events.
8. Preserve evidence such as frames and clips.
9. Provide structured JSON output.
10. Support quantitative detection evaluation using manually annotated ground-truth images.

Important:

Detection of a person does not automatically mean that the person is unauthorized.

Authorization is a security/business rule. Therefore, the module identifies a potential unauthorized-access event based on configured zones, tripwires, schedules, and other rules. Final confirmation can be performed through human review.

---

## 3. Module Architecture

CCTV / Video Input
↓
YOLO11n Person Detection
↓
ByteTrack Tracking
↓
Rule Evaluation
├── Restricted Zone
├── Tripwire
├── Restricted Schedule
├── Loitering
└── Event Cooldown
↓
Events
↓
Evidence
├── Frame
└── Video Clip
↓
Incidents
↓
Human Review

---

## 4. Detection vs Event vs Incident

The system separates three concepts.

### Detection

A detection means that the YOLO model identified a person in a frame.

Example:

Person detected
Confidence = 0.87
Bounding box = [x1, y1, x2, y2]
Track ID = 12

A detection alone is not an intrusion.

### Event

An event is generated when a detection satisfies one of the configured monitoring rules.

Examples:

- Person enters Restricted Zone 1
- Person crosses Main Entrance Tripwire

### Incident

An incident is the higher-level security record created from an event.

The incident can later be reviewed by a human operator.

Detection
↓
Rule matched
↓
Event
↓
Incident
↓
Human Review

---

## 5. Human Review Concept

The system should not automatically assume that every detected intrusion is malicious.

A suitable operational workflow is:

Potential Intrusion
↓
PENDING
├── CONFIRMED
├── DISMISSED
├── UNCERTAIN
└── ESCALATED / RESOLVED

The current incident manager provides structured incident handling, while long-term database persistence can be integrated later.

---

## 6. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.9.6 |
| Object Detection | YOLO11n |
| Object Tracking | ByteTrack |
| Computer Vision | OpenCV |
| Configuration | YAML |
| Numerical Processing | NumPy |
| Testing | Pytest |
| Evaluation | Custom Python evaluation pipeline |
| Model Framework | Ultralytics |
| Output | JSON |
| Video Processing | OpenCV |

---

## 7. Project Structure

The following structure reflects the current Module 03 directory.

module_03_intrusion/
├── README.md
├── config/
│   └── config.yaml
├── datasets/
│   ├── README.md
│   └── ground_truth/
│       ├── annotations/
│       │   ├── frame_00000.txt
│       │   ├── frame_00013.txt
│       │   ├── frame_00026.txt
│       │   ├── frame_00039.txt
│       │   ├── frame_00052.txt
│       │   ├── frame_00064.txt
│       │   ├── frame_00077.txt
│       │   ├── frame_00090.txt
│       │   ├── frame_00103.txt
│       │   ├── frame_00116.txt
│       │   ├── frame_00129.txt
│       │   ├── frame_00142.txt
│       │   ├── frame_00155.txt
│       │   ├── frame_00168.txt
│       │   ├── frame_00181.txt
│       │   ├── frame_00193.txt
│       │   ├── frame_00206.txt
│       │   ├── frame_00219.txt
│       │   ├── frame_00232.txt
│       │   ├── frame_00245.txt
│       │   ├── frame_00258.txt
│       │   ├── frame_00271.txt
│       │   ├── frame_00284.txt
│       │   ├── frame_00297.txt
│       │   ├── frame_00310.txt
│       │   ├── frame_00322.txt
│       │   ├── frame_00335.txt
│       │   ├── frame_00348.txt
│       │   ├── frame_00361.txt
│       │   └── frame_00374.txt
│       ├── images/
│       │   ├── frame_00000.jpg
│       │   ├── frame_00013.jpg
│       │   ├── frame_00026.jpg
│       │   ├── frame_00039.jpg
│       │   ├── frame_00052.jpg
│       │   ├── frame_00064.jpg
│       │   ├── frame_00077.jpg
│       │   ├── frame_00090.jpg
│       │   ├── frame_00103.jpg
│       │   ├── frame_00116.jpg
│       │   ├── frame_00129.jpg
│       │   ├── frame_00142.jpg
│       │   ├── frame_00155.jpg
│       │   ├── frame_00168.jpg
│       │   ├── frame_00181.jpg
│       │   ├── frame_00193.jpg
│       │   ├── frame_00206.jpg
│       │   ├── frame_00219.jpg
│       │   ├── frame_00232.jpg
│       │   ├── frame_00245.jpg
│       │   ├── frame_00258.jpg
│       │   ├── frame_00271.jpg
│       │   ├── frame_00284.jpg
│       │   ├── frame_00297.jpg
│       │   ├── frame_00310.jpg
│       │   ├── frame_00322.jpg
│       │   ├── frame_00335.jpg
│       │   ├── frame_00348.jpg
│       │   ├── frame_00361.jpg
│       │   └── frame_00374.jpg
│       └── scripts/
│           ├── annotate.py
│           └── extract_frames.py
├── evaluation/
│   ├── evaluate.py
│   └── results/
│       └── m03_results.json
├── inference/
│   ├── detector.py
│   ├── pipeline.py
│   ├── tripwire_editor.py
│   └── zone_editor.py
├── models/
│   └── checkpoints/
│       └── yolo11n.pt
├── rules/
│   ├── event_rules.py
│   └── incident_manager.py
├── test_videos/
│   └── test.mp4
├── tests/
│   ├── test_detection.py
│   ├── test_edge_cases.py
│   ├── test_events.py
│   ├── test_incidents.py
│   └── test_tripwire.py
└── training/
    ├── augmentations.py
    ├── train.py
    └── validate.py

### Generated / Cache Files

The repository may also contain generated files such as:

.pytest_cache/
.DS_Store

These are not part of the core Module 03 source architecture.

---

## 8. Configuration

The module configuration is stored at:

config/config.yaml

Current configuration:

module:
  id: module_03_intrusion
  name: Intrusion & Unauthorized Access Monitoring
  version: 1.0.0

model:
  path: models/checkpoints/yolo11n.pt
  input_size: 640
  confidence_threshold: 0.5
  iou_threshold: 0.5
  person_class_id: 0

tracking:
  enabled: true
  tracker: bytetrack.yaml
  max_age: 30

zones:
  restricted_zones:
  - name: Restricted Zone 1
    polygon:
    - - 1438
      - 154
    - - 1835
      - 149
    - - 1838
      - 849
    - - 1449
      - 854

  tripwires:
  - name: Main Entrance Tripwire
    line:
    - - 1194
      - 156
    - - 1215
      - 894

schedule:
  enabled: false
  restricted_start: '22:00'
  restricted_end: 06:00

event:
  minimum_frames: 5
  loitering_seconds: 30
  cooldown_seconds: 10

evidence:
  save_frame: true
  save_clip: true
  pre_event_seconds: 5
  post_event_seconds: 5

output:
  format: json

---

## 9. Configuration Explanation

### Model

model:
  path: models/checkpoints/yolo11n.pt
  input_size: 640
  confidence_threshold: 0.5
  iou_threshold: 0.5
  person_class_id: 0

The module uses YOLO11n.

Only the person class is relevant for Module 03.

Current confidence threshold:

0.50

Current IoU threshold:

0.50

### Tracking

tracking:
  enabled: true
  tracker: bytetrack.yaml
  max_age: 30

ByteTrack provides persistent track IDs for detected people.

Example:

Frame 100 → Person → Track ID 7
Frame 101 → Person → Track ID 7
Frame 102 → Person → Track ID 7

This allows the rule system to reason about movement over multiple frames.

### Restricted Zone

A restricted zone is represented as a polygon.

Current configuration:

Restricted Zone 1

with four configured polygon points.

Conceptually:

P1 ---------------- P2
 |                    |
 |   Restricted       |
 |      Zone          |
 |                    |
P4 ---------------- P3

When a tracked person enters the configured restricted area, the event-rule system can generate a potential intrusion event.

### Tripwire

The module also supports a virtual tripwire.

Current configuration:

Main Entrance Tripwire

When a tracked person crosses the configured line according to the tripwire logic, an event can be generated.

### Schedule Rules

The configuration supports restricted access hours:

schedule:
  enabled: false
  restricted_start: '22:00'
  restricted_end: 06:00

The schedule is currently disabled.

Configured values:

Start: 22:00
End: 06:00

### Event Configuration

event:
  minimum_frames: 5
  loitering_seconds: 30
  cooldown_seconds: 10

These parameters support:

- Minimum frame persistence
- Loitering detection
- Event cooldown

The cooldown helps prevent repeated events from being generated continuously for the same situation.

### Evidence

evidence:
  save_frame: true
  save_clip: true
  pre_event_seconds: 5
  post_event_seconds: 5

The intended evidence workflow is:

Event
├── Evidence Frame
└── Video Clip
    ├── 5 sec before event
    └── 5 sec after event

### Output

The current output format is JSON.

Evaluation results are stored at:

evaluation/results/m03_results.json

---

## 10. Installation

From the NEXORA project:

cd ~/Documents/NEXORA

Activate the virtual environment:

source .venv/bin/activate

Verify Python:

python --version

Expected environment:

Python 3.9.6

Move to Module 03:

cd ml/modules/module_03_intrusion

---

## 11. Verify the Model

Check that the YOLO model exists:

ls -lh models/checkpoints/yolo11n.pt

Expected file:

models/checkpoints/yolo11n.pt

---

## 12. Verify the Configuration

Run:

cat config/config.yaml

---

## 13. Python Files

The current Python implementation consists of:

datasets/ground_truth/scripts/annotate.py
datasets/ground_truth/scripts/extract_frames.py

evaluation/evaluate.py

inference/detector.py
inference/pipeline.py
inference/tripwire_editor.py
inference/zone_editor.py

rules/event_rules.py
rules/incident_manager.py

tests/test_detection.py
tests/test_edge_cases.py
tests/test_events.py
tests/test_incidents.py
tests/test_tripwire.py

training/augmentations.py
training/train.py
training/validate.py

---

## 14. Inference Components

### detector.py

Location:

inference/detector.py

Responsible for:

- Loading YOLO
- Running person detection
- Filtering for the person class
- Returning standardized detection objects
- Drawing detections for visualization

A detection contains information such as:

- module
- camera_id
- frame_id
- timestamp
- track_id
- class_name
- confidence
- bbox

### pipeline.py

Location:

inference/pipeline.py

This is the main orchestration component.

The pipeline connects:

Model
↓
Tracking
↓
Rules
↓
Events
↓
Incidents
↓
Evidence

The frame-processing interface is:

process_frame(frame, camera_id, frame_id)

It returns:

detections
events

Video processing produces structured results containing camera information, processed frames, events/incidents, and frame-level results.

### Zone Editor

Location:

inference/zone_editor.py

This component is used for configuring/editing restricted zones.

### Tripwire Editor

Location:

inference/tripwire_editor.py

This component is used for configuring/editing virtual tripwire lines.

---

## 15. Event Rules

Location:

rules/event_rules.py

This component contains the rule-based event logic.

Supported concepts include:

- Restricted zones
- Tripwires
- Restricted hours
- Loitering
- Cooldown handling

Event IDs are designed to remain unique even when multiple events occur at the same frame/track combination.

---

## 16. Incident Manager

Location:

rules/incident_manager.py

The incident manager handles incident creation and lifecycle operations.

The current implementation is an in-memory incident manager.

Therefore:

Incidents are not currently persisted to a database.

Database persistence can be added during later NEXORA integration.

---

## 17. Test Suite

The project contains five test files:

tests/test_detection.py
tests/test_edge_cases.py
tests/test_events.py
tests/test_incidents.py
tests/test_tripwire.py

Run the complete test suite:

pytest -q

Previously verified complete test suite:

43 passed

If code is changed after this README is updated, rerun the test suite to confirm the current status.

---

## 18. Detection Tests

File:

tests/test_detection.py

These tests verify the basic person-detection functionality.

Previously verified:

4/4 tests passed

---

## 19. Event Tests

File:

tests/test_events.py

These tests verify event-rule behavior.

Previously verified:

5/5 tests passed

The event implementation also includes unique event sequencing to prevent duplicate event IDs.

---

## 20. Tripwire Tests

File:

tests/test_tripwire.py

The tripwire functionality has been tested together with the event rules.

Previously verified:

16 tests passed

---

## 21. Incident Tests

File:

tests/test_incidents.py

The incident manager has been tested separately.

Previously verified:

15 tests passed

---

## 22. Edge-Case Tests

File:

tests/test_edge_cases.py

The edge-case suite covers scenarios such as:

- Empty input
- Low-light conditions
- Blurred input
- Small resolution
- Large resolution
- Multiple people
- Partial visibility

Previously verified:

8 tests collected

---

## 23. Ground-Truth Dataset

The module contains a manually annotated ground-truth evaluation set.

Location:

datasets/ground_truth/

It contains:

- images/
- annotations/
- scripts/

There are currently:

30 annotated images
30 annotation files

The ground-truth images were sampled from the test video.

Important:

These 30 images are evaluation data, not a model-training dataset.

---

## 24. Extracting Ground-Truth Frames

The frame extraction script is:

datasets/ground_truth/scripts/extract_frames.py

To extract 30 evenly sampled frames from the test video:

python datasets/ground_truth/scripts/extract_frames.py \
  --video test_videos/test.mp4 \
  --output datasets/ground_truth/images \
  --num-frames 30

The corrected extraction process counts the actually readable video frames before sampling.

For the current test video:

Readable frames: 375

Selected frame indices:

0, 13, 26, 39, 52, 64, 77, 90, 103, 116,
129, 142, 155, 168, 181, 193, 206, 219, 232, 245,
258, 271, 284, 297, 310, 322, 335, 348, 361, 374

---

## 25. Ground-Truth Annotation

The annotation tool is:

datasets/ground_truth/scripts/annotate.py

Annotation controls:

- Left Mouse Button: Draw bounding box
- S: Save and next image
- R: Reset current image
- Q: Quit

The annotations use:

Class 0 = person

---

## 26. Current Ground-Truth Statistics

Images evaluated:

30

Ground-truth persons:

100

The number of ground-truth persons varies across frames.

This provides a baseline for measuring person detection performance on the selected CCTV footage.

---

## 27. Detection Evaluation

The evaluation script is:

evaluation/evaluate.py

The ground-truth evaluation mode evaluates the detection model against the manually annotated images.

The current evaluation is detection-only.

It does not claim to provide tracking accuracy because tracking ground truth has not been created.

---

## 28. Evaluation Command

Run:

python evaluation/evaluate.py \
  --ground-truth \
  --ground-truth-images datasets/ground_truth/images \
  --ground-truth-annotations datasets/ground_truth/annotations \
  --ground-truth-model models/checkpoints/yolo11n.pt \
  --ground-truth-confidence 0.5

The results are written to:

evaluation/results/m03_results.json

---

## 29. Current Detection Evaluation Results

| Metric | Result |
|---|---:|
| Images evaluated | 30 |
| Ground-truth persons | 100 |
| Predicted persons | 199 |
| True positives @ IoU 0.50 | 92 |
| False positives @ IoU 0.50 | 107 |
| False negatives @ IoU 0.50 | 8 |
| Precision | 46.23% |
| Recall | 92.00% |
| F1 Score | 61.54% |
| mAP@50 | 62.60% |
| mAP@50:95 | 32.02% |
| Confidence threshold | 0.50 |
| IoU threshold | 0.50 |

---

## 30. Understanding the Results

The most important observation is:

Recall = 92.00%
Precision = 46.23%

The high recall means that the detector successfully found most of the manually annotated people.

The lower precision indicates that the model also produced a significant number of false-positive person detections.

Therefore:

The model is relatively good at finding people, but it still produces many extra detections.

For security monitoring, high recall can be valuable because missed people can result in missed potential intrusion events.

However, the false positives mean that additional filtering, better camera-specific training, confidence tuning, or downstream rules may be useful before production deployment.

Do not interpret 92% recall as 92% accuracy.

They are different metrics.

---

## 31. Evaluation Result File

The evaluation result is stored in:

evaluation/results/m03_results.json

To inspect it:

python -m json.tool evaluation/results/m03_results.json

To print only the detection metrics:

python -c "import json; d=json.load(open('evaluation/results/m03_results.json')); print(d['detection_metrics'])"

---

## 32. Tracking Evaluation

A separate tracking ground-truth dataset has not been created.

Therefore, the current project does not report:

- MOTA
- MOTP
- IDF1
- HOTA

or other tracking-specific benchmark metrics.

ByteTrack is enabled operationally, but tracking accuracy should not be claimed without suitable tracking ground truth.

---

## 33. Operational Event Evaluation

The current ground-truth dataset contains person bounding boxes.

It does not contain manually verified labels for:

- Unauthorized access
- Authorized access
- Confirmed intrusion
- False alarm
- Loitering event
- Tripwire event

Therefore, operational event metrics such as event precision, event recall, false alarm rate, and incident confirmation rate are not currently reported.

These can be added after creating human-reviewed event labels.

---

## 34. Test Video

The current test video is:

test_videos/test.mp4

Observed video characteristics:

- Resolution: 1920 × 1080
- Nominal/source frame rate: 25 FPS
- Readable frames: 375
- Approximate duration: 15.125 seconds

The video metadata contains an unusual OpenCV FPS value, so the 25 FPS value should be treated as the nominal playback/source frame rate rather than the misleading OpenCV-reported 1000 FPS value.

---

## 35. Performance

A previous full-video benchmark processed approximately:

Frames: 375
Processing time: ~111.5 seconds
Throughput: ~3.36 FPS

Compared with the nominal 25 FPS source:

Real-time factor ≈ 3.36 / 25
                 ≈ 0.134

Therefore, the current CPU-based pipeline does not process this video in real time.

Future optimization can include:

- GPU acceleration
- Model optimization
- Lower input resolution
- Frame skipping
- Batch inference
- Hardware-specific acceleration
- Stream-specific processing optimization

Performance may vary between runs and hardware.

---

## 36. Training Components

The project currently contains:

training/augmentations.py
training/train.py
training/validate.py

These files provide the structure for model training and validation workflows.

However, Module 03 currently uses the pretrained:

models/checkpoints/yolo11n.pt

A custom training dataset is not required for the current baseline.

---

## 37. Why Custom Training Is Not Required Yet

The current objective is to establish a working intrusion-monitoring pipeline.

The pretrained YOLO11n model already provides person detection.

Current workflow:

Pretrained YOLO11n
↓
Person Detection
↓
Tracking
↓
Security Rules
↓
Intrusion Events

Custom training can be introduced later if the project needs better performance on:

- Specific CCTV camera angles
- Crowded scenes
- Low-light environments
- Small/distant people
- Heavy occlusion
- NEXORA-specific environments

The existing 30 annotated frames should not be treated as a proper training dataset.

---

## 38. Current Security Logic

The current security model follows this principle:

Person detected
↓
Person tracked
↓
Movement/position checked
↓
Security rule matched
↓
Potential intrusion event
↓
Incident
↓
Human review

This prevents the system from incorrectly treating every person detection as an unauthorized user.

---

## 39. Example Scenario

Suppose a CCTV camera monitors an equipment room.

The equipment room is configured as:

Restricted Zone 1

A person enters the polygon.

The pipeline can produce:

Detection
↓
Track ID assigned
↓
Person enters restricted zone
↓
Restricted-zone rule triggered
↓
Intrusion event generated
↓
Incident created
↓
Evidence captured
↓
Human review

The operator can then determine whether the access was actually unauthorized.

---

## 40. Event ID Uniqueness

Event identifiers include a sequence component to avoid duplicate IDs when multiple events occur for the same camera/frame/track combination.

Conceptually:

EVT-camera-frame-track-sequence

Example:

EVT-CAM01-120-7-1
EVT-CAM01-120-7-2

This ensures that event identifiers are not accidentally identical when multiple events are generated at the same frame.

---

## 41. Important Limitations

The current implementation is a development/research baseline.

Important limitations include:

1. The detector is pretrained rather than custom-trained for the target CCTV environment.
2. The evaluation dataset contains only 30 manually annotated frames.
3. The ground-truth dataset comes from one test video.
4. Tracking metrics are not currently available.
5. Operational event metrics are not currently available.
6. Incident persistence is not currently backed by a database.
7. The current benchmark does not achieve real-time 25 FPS processing on the tested CPU setup.
8. False-positive detections remain significant.
9. Authorization cannot be inferred purely from person detection.
10. Production deployment requires additional security, reliability, and monitoring validation.

---

## 42. Troubleshooting

### Model not found

Check:

ls -lh models/checkpoints/yolo11n.pt

### Configuration error

Check:

cat config/config.yaml

Make sure the paths are relative to:

ml/modules/module_03_intrusion

### Python environment issue

Activate the NEXORA environment:

cd ~/Documents/NEXORA
source .venv/bin/activate

Verify:

python --version

### Tests failing

Run:

pytest -q

For a specific test file:

pytest -q tests/test_detection.py

pytest -q tests/test_events.py

pytest -q tests/test_incidents.py

pytest -q tests/test_tripwire.py

---

## 43. Useful Verification Commands

From the Module 03 directory:

Check the complete source tree:

find . -type f \
  -not -path './evidence/*' \
  -not -path './__pycache__/*' \
  -not -path './*.pyc' \
  | sort

Check Python files:

find . -name "*.py" \
  -not -path './__pycache__/*' \
  | sort

Check configuration:

cat config/config.yaml

Run all tests:

pytest -q

Inspect evaluation results:

python -m json.tool evaluation/results/m03_results.json

---

## 44. Development Status

Current Module 03 status:

YOLO11n Person Detection       ✓
ByteTrack Tracking             ✓
Restricted Zone Rules          ✓
Tripwire Rules                 ✓
Schedule Rule Support          ✓
Loitering Rule Support         ✓
Event Cooldown                 ✓
Incident Management            ✓
Evidence Configuration         ✓
Ground-Truth Dataset           ✓
Detection Evaluation           ✓
Edge-Case Tests                ✓
Unit Tests                     ✓
Custom Model Training          Optional / Future
Tracking Benchmark             Not Available
Operational Event Benchmark    Not Available
Database Persistence           Future Integration

---

## 45. Recommended Next Development Steps

Recommended order for continuing Module 03:

1. Stable backend pipeline
2. Evaluation and documentation
3. NEXORA dashboard integration
4. Live/recorded video visualization
5. Incident review interface
6. Optional camera-specific training
7. Performance optimization
8. Database persistence

The current detection/evaluation baseline should be preserved before introducing major model or pipeline changes.

---

## 46. NEXORA Integration

Module 03 is intended to operate as one module within the NEXORA security-monitoring platform.

The NEXORA platform can consume structured information from the module such as:

- Camera ID
- Frame ID
- Track ID
- Detection confidence
- Bounding box
- Event type
- Event ID
- Incident ID
- Severity
- Timestamp
- Evidence reference
- Review status

This allows the central NEXORA dashboard to present intrusion incidents alongside other safety/security modules.

---

## 47. Suggested NEXORA Dashboard Flow

NEXORA Dashboard
│
├── Live Camera
├── Detected Persons
├── Restricted Zone
├── Tripwire
├── Active Events
├── Incidents
└── Evidence / Review

An operator should be able to select an incident and inspect the associated evidence before confirming or dismissing it.

---

## 48. Reproducibility

To reproduce the current development environment:

cd ~/Documents/NEXORA
source .venv/bin/activate
cd ml/modules/module_03_intrusion

Verify the model:

ls -lh models/checkpoints/yolo11n.pt

Verify the configuration:

cat config/config.yaml

Run tests:

pytest -q

Run the ground-truth evaluation:

python evaluation/evaluate.py \
  --ground-truth \
  --ground-truth-images datasets/ground_truth/images \
  --ground-truth-annotations datasets/ground_truth/annotations \
  --ground-truth-model models/checkpoints/yolo11n.pt \
  --ground-truth-confidence 0.5

Inspect the generated evaluation:

python -m json.tool evaluation/results/m03_results.json

---

## 49. Quick Start

For a quick verification of Module 03:

cd ~/Documents/NEXORA
source .venv/bin/activate
cd ml/modules/module_03_intrusion

Run:

pytest -q

Then run:

python evaluation/evaluate.py \
  --ground-truth \
  --ground-truth-images datasets/ground_truth/images \
  --ground-truth-annotations datasets/ground_truth/annotations \
  --ground-truth-model models/checkpoints/yolo11n.pt \
  --ground-truth-confidence 0.5

Inspect:

python -m json.tool evaluation/results/m03_results.json

---

## 50. Final Summary

Module 03 provides the NEXORA platform with a complete baseline for CCTV-based intrusion and unauthorized-access monitoring.

The current system combines:

YOLO11n
+
ByteTrack
+
Restricted Zones
+
Tripwires
+
Security Rules
+
Evidence
+
Incident Management
+
Ground-Truth Evaluation

Current detection baseline on 30 manually annotated images:

Precision: 46.23%
Recall: 92.00%
F1: 61.54%
mAP@50: 62.60%
mAP@50:95: 32.02%

The results demonstrate that the current pretrained detector can identify most people in the selected CCTV footage, while also showing that false positives remain an important area for improvement.

The module is suitable as a working NEXORA development baseline and can next be integrated with the NEXORA dashboard, followed by optional camera-specific training and performance optimization.
