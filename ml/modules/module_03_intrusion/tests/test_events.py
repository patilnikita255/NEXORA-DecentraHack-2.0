
import sys
from pathlib import Path
from datetime import datetime

MODULE_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(MODULE_ROOT)
)

from rules.event_rules import IntrusionRuleEngine


def load_test_config():
    return {
        "event": {
            "minimum_frames": 2,
            "loitering_seconds": 30,
            "cooldown_seconds": 10,
        },
        "schedule": {
            "enabled": True,
            "restricted_start": "22:00",
            "restricted_end": "06:00",
        },
        "zones": {
            "restricted_zones": [
                {
                    "name": "LAB-RESTRICTED",
                    "polygon": [
                        [100, 100],
                        [500, 100],
                        [500, 500],
                        [100, 500],
                    ],
                }
            ],
            "tripwires": [],
        },
    }


def create_detection(
    frame_id=1,
    track_id=19,
    confidence=0.91,
    bbox=None,
):
    if bbox is None:
        bbox = {
            "x1": 200,
            "y1": 200,
            "x2": 300,
            "y2": 450,
        }

    return {
        "module": "module_03_intrusion",
        "camera_id": "CAM-001",
        "frame_id": frame_id,
        "timestamp": "2026-10-02T23:14:00+00:00",
        "track_id": track_id,
        "class_name": "person",
        "confidence": confidence,
        "bbox": bbox,
    }


def test_no_event_for_detection_outside_zone():
    config = load_test_config()

    engine = IntrusionRuleEngine(config)

    detection = create_detection(
        bbox={
            "x1": 600,
            "y1": 600,
            "x2": 650,
            "y2": 700,
        }
    )

    current_time = datetime(
        2026,
        10,
        2,
        23,
        14,
    )

    events = engine.check_detection(
        detection,
        current_time,
    )

    assert events == []


def test_event_after_person_enters_restricted_zone():
    config = load_test_config()

    engine = IntrusionRuleEngine(config)

    current_time = datetime(
        2026,
        10,
        2,
        23,
        14,
    )

    detection_1 = create_detection(
        frame_id=1
    )

    detection_2 = create_detection(
        frame_id=2
    )

    events_1 = engine.check_detection(
        detection_1,
        current_time,
    )

    events_2 = engine.check_detection(
        detection_2,
        current_time,
    )

    assert events_1 == []

    assert len(events_2) >= 1

    assert any(
        event["event_type"]
        == "POTENTIAL_UNAUTHORIZED_ZONE_ENTRY"
        for event in events_2
    )


def test_event_contains_required_fields():
    config = load_test_config()

    engine = IntrusionRuleEngine(config)

    current_time = datetime(
        2026,
        10,
        2,
        23,
        14,
    )

    engine.check_detection(
        create_detection(frame_id=1),
        current_time,
    )

    events = engine.check_detection(
        create_detection(frame_id=2),
        current_time,
    )

    if events:
        event = events[0]

        required_fields = {
            "event_id",
            "module",
            "event_type",
            "camera_id",
            "track_id",
            "timestamp",
            "confidence",
            "severity",
            "status",
        }

        assert required_fields.issubset(
            event.keys()
        )


def test_schedule_outside_restricted_hours():
    config = load_test_config()

    engine = IntrusionRuleEngine(config)

    current_time = datetime(
        2026,
        10,
        2,
        14,
        0,
    )

    engine.check_detection(
        create_detection(frame_id=1),
        current_time,
    )

    events = engine.check_detection(
        create_detection(frame_id=2),
        current_time,
    )

    intrusion_events = [
        event
        for event in events
        if event["event_type"]
        == "POTENTIAL_UNAUTHORIZED_ZONE_ENTRY"
    ]

    assert intrusion_events == []


def test_loitering_event():
    config = load_test_config()

    engine = IntrusionRuleEngine(config)

    start_time = datetime(
        2026,
        10,
        2,
        23,
        14,
        0,
    )

    engine.check_detection(
        create_detection(frame_id=1),
        start_time,
    )

    later_time = datetime(
        2026,
        10,
        2,
        23,
        14,
        31,
    )

    events = engine.check_detection(
        create_detection(frame_id=2),
        later_time,
    )

    loitering_events = [
        event
        for event in events
        if event["event_type"]
        == "LOITERING"
    ]

    assert len(loitering_events) >= 1


def test_restricted_hours_generates_event():
    config = load_test_config()

    engine = IntrusionRuleEngine(config)

    current_time = datetime(
        2026,
        10,
        2,
        23,
        14,
    )

    engine.check_detection(
        create_detection(frame_id=1),
        current_time,
    )

    events = engine.check_detection(
        create_detection(frame_id=2),
        current_time,
    )

    intrusion_events = [
        event
        for event in events
        if event["event_type"]
        == "POTENTIAL_UNAUTHORIZED_ZONE_ENTRY"
    ]

    assert len(intrusion_events) >= 1

    assert (
        intrusion_events[0]["severity"]
        == "HIGH"
    )


def test_allowed_hours_does_not_generate_event():
    config = load_test_config()

    engine = IntrusionRuleEngine(config)

    current_time = datetime(
        2026,
        10,
        2,
        14,
        0,
    )

    engine.check_detection(
        create_detection(frame_id=1),
        current_time,
    )

    events = engine.check_detection(
        create_detection(frame_id=2),
        current_time,
    )

    intrusion_events = [
        event
        for event in events
        if event["event_type"]
        == "POTENTIAL_UNAUTHORIZED_ZONE_ENTRY"
    ]

    assert intrusion_events == []


def test_overnight_restricted_hours_generates_event():
    config = load_test_config()

    engine = IntrusionRuleEngine(config)

    current_time = datetime(
        2026,
        10,
        3,
        2,
        0,
    )

    engine.check_detection(
        create_detection(frame_id=1),
        current_time,
    )

    events = engine.check_detection(
        create_detection(frame_id=2),
        current_time,
    )

    intrusion_events = [
        event
        for event in events
        if event["event_type"]
        == "POTENTIAL_UNAUTHORIZED_ZONE_ENTRY"
    ]

    assert len(intrusion_events) >= 1
