# M03 Dataset Documentation

## Dataset Purpose

Module 03 — Intrusion & Unauthorized Access Monitoring primarily requires:

1. Person detection
2. Person tracking
3. Camera-specific zone testing
4. Tripwire testing
5. Entry and exit events
6. Loitering scenarios
7. Difficult CCTV conditions

The NEXORA specification identifies camera-specific CCTV footage and
zone/event test footage as especially important for this module.

---

# 1. COCO

## Dataset Name

Microsoft COCO

## Source

Microsoft COCO dataset.

## URL

https://cocodataset.org/

## License

License must be verified for the exact version and intended use before
redistribution or commercial use.

## Purpose

General-purpose object detection.

For M03, the relevant class is:

- person

## Classes Used

- person

## Classes Not Used

All other COCO classes are outside the M03 MVP.

## Annotation Format

COCO JSON annotations.

## Split

COCO provides official train and validation splits.

## Why Selected

COCO provides a strong general-purpose pretrained person detection
baseline and is used by common pretrained YOLO models.

## Limitations

COCO is not specifically designed for NEXORA CCTV environments.

It may not fully represent:

- Low-light CCTV
- Camera-specific perspectives
- Security-camera compression
- Long-distance persons
- Heavy occlusion
- NEXORA-specific restricted zones

---

# 2. CrowdHuman

## Dataset Name

CrowdHuman

## Source

CrowdHuman dataset.

## URL

https://www.crowdhuman.org/

## License

The applicable dataset license must be verified before use.

## Purpose

Crowded human detection.

## Classes Used

- person

## Why Selected

CrowdHuman is useful for crowded scenes and heavily overlapping
persons.

## Limitations

Crowded scenes may still differ from NEXORA's actual CCTV cameras.

---

# 3. WiderPerson

## Dataset Name

WiderPerson

## Source

WiderPerson dataset.

## URL

https://www.cbsr.ia.ac.cn/users/sfzhang/WiderPerson/

## License

The exact dataset license must be verified before redistribution
or other restricted use.

## Purpose

Person detection.

## Classes Used

Person-related annotations required for M03.

## Why Selected

Provides additional person detection diversity.

## Limitations

Dataset scenes may differ from the target NEXORA environment.

---

# 4. MOTChallenge

## Dataset Name

MOTChallenge

## Source

MOTChallenge.

## URL

https://motchallenge.net/

## Purpose

Multi-object tracking.

## Purpose in M03

Used as a reference for:

- Person tracking
- Track consistency
- Multiple-person scenarios
- Occlusion handling

## Important Note

M03 currently uses ByteTrack / BoT-SORT for tracking.

---

# 5. AI City Challenge

## Dataset Name

AI City Challenge datasets

## Source

AI City Challenge.

## URL

https://www.aicitychallenge.org/

## Purpose

Traffic and multi-camera computer vision research.

## M03 Relevance

Relevant to:

- Multi-camera tracking
- Person tracking
- Real-world surveillance conditions

## License

Dataset-specific access and license requirements must be checked.

---

# 6. NEXORA Custom CCTV Dataset

## Status

To be collected.

## Importance

This is the most important dataset for final M03 validation.

The dataset should represent the actual camera environments where
NEXORA will be demonstrated.

## Required Scenarios

The custom dataset should include:

- Normal authorized entry
- Potential unauthorized entry
- Person near zone boundary
- Person crossing boundary
- Person turning around
- Multiple people
- Crowded entrances
- Partial occlusion
- Low-light conditions
- Different camera angles
- Different distances
- Different backgrounds
- Different resolutions
- Motion blur
- Empty scenes
- False-positive situations

## Zone Annotations

Each camera should have its own zone configuration.

Do not reuse the same polygon coordinates across different cameras.

Example:

Camera 1:
polygon A

Camera 2:
polygon B

## Event Annotations

Where possible, record:

- Entry
- Exit
- Direction
- Zone
- Timestamp
- Loitering
- Boundary cases

---

# 7. Dataset Split

Do NOT randomly split adjacent CCTV frames.

Bad approach:

Frame 100 → Train
Frame 101 → Test
Frame 102 → Train

These frames can be nearly identical.

Preferred approach:

Camera/session A → Training
Camera/session B → Validation
Camera/session C → Testing

This reduces leakage between nearly identical frames.

---

# 8. Hard Negatives

Hard negatives should be deliberately collected.

Examples:

- People outside restricted zones
- People walking near boundaries
- Authorized activity during normal hours
- Empty restricted zones
- People entering and immediately leaving
- People partially visible
- People hidden behind objects

Hard negatives are important for reducing false alerts.

---

# 9. Annotation Format

For YOLO training, annotations should use YOLO format.

Example:

class_id center_x center_y width height

For M03 MVP:

0 = person

---

# 10. Data Quality

Check:

- Correct bounding boxes
- Correct class labels
- No duplicate images
- No corrupted frames
- No train/test leakage
- Correct camera/session separation
- Sufficient difficult-condition examples

---

# 11. Current Dataset Status

Baseline:

- COCO: available as pretrained-model source
- CrowdHuman: candidate
- WiderPerson: candidate
- MOTChallenge: tracking reference
- AI City Challenge: tracking reference
- NEXORA CCTV: pending collection

No final M03 accuracy or mAP should be reported until the model is
actually evaluated on a defined test set.