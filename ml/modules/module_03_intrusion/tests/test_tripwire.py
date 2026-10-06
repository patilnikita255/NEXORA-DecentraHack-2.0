import sys
from pathlib import Path
from datetime import datetime

MODULE_ROOT = Path(__file__).resolve().parents[1]

if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from rules.event_rules import IntrusionRuleEngine


def create_config():
    return {
        "zones": {
            "restricted_zones": [],
            "tripwires": [
                {
                    "name": "Main Entrance Tripwire",
                    "line": [
                        [100, 100],
                        [300, 100]
                    ]
                }
            ]
        },
        "schedule": {
            "enabled": False,
            "restricted_start": "22:00",
            "restricted_end": "06:00"
        },
        "event": {
            "minimum_frames": 5,
            "loitering_seconds": 30,
            "cooldown_seconds": 10
        }
    }


def create_detection(
    frame_id,
    track_id,
    x1,
    y1,
    x2,
    y2
):
    return {
        "module": "module_03_intrusion",
        "camera_id": "CAM-TEST",
        "frame_id": frame_id,
        "timestamp": "2026-10-04T12:00:00+00:00",
        "track_id": track_id,
        "class_name": "person",
        "confidence": 0.90,
        "bbox": {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        }
    }


# ==========================================================
# BASIC TRIPWIRE TESTS
# ==========================================================

def test_tripwire_crossing_a_to_b():

    engine = IntrusionRuleEngine(
        create_config()
    )

    previous = create_detection(
        1,
        1,
        120,
        50,
        160,
        90
    )

    current = create_detection(
        2,
        1,
        220,
        110,
        260,
        130
    )

    events = engine.check_tripwires(
        previous,
        current,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            1
        )
    )

    assert len(events) == 1

    assert (
        events[0]["event_type"]
        == "TRIPWIRE_CROSSED"
    )

    assert (
        events[0]["direction"]
        == "A_TO_B"
    )


def test_tripwire_crossing_b_to_a():

    engine = IntrusionRuleEngine(
        create_config()
    )

    previous = create_detection(
        1,
        2,
        220,
        110,
        260,
        130
    )

    current = create_detection(
        2,
        2,
        120,
        50,
        160,
        90
    )

    events = engine.check_tripwires(
        previous,
        current,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            1
        )
    )

    assert len(events) == 1

    assert (
        events[0]["event_type"]
        == "TRIPWIRE_CROSSED"
    )

    assert (
        events[0]["direction"]
        == "B_TO_A"
    )


def test_no_tripwire_crossing():

    engine = IntrusionRuleEngine(
        create_config()
    )

    previous = create_detection(
        1,
        3,
        120,
        150,
        160,
        180
    )

    current = create_detection(
        2,
        3,
        220,
        150,
        260,
        180
    )

    events = engine.check_tripwires(
        previous,
        current,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            1
        )
    )

    assert len(events) == 0


def test_missing_previous_detection():

    engine = IntrusionRuleEngine(
        create_config()
    )

    current = create_detection(
        2,
        4,
        220,
        110,
        260,
        130
    )

    events = engine.check_tripwires(
        None,
        current,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            1
        )
    )

    assert len(events) == 0


# ==========================================================
# STANDARD EVENT FORMAT
# ==========================================================

def test_tripwire_event_contains_standard_fields():

    engine = IntrusionRuleEngine(
        create_config()
    )

    previous = create_detection(
        10,
        5,
        120,
        50,
        160,
        90
    )

    current = create_detection(
        11,
        5,
        220,
        110,
        260,
        130
    )

    events = engine.check_tripwires(
        previous,
        current,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            1
        )
    )

    assert len(events) == 1

    event = events[0]

    assert (
        event["module"]
        == "module_03_intrusion"
    )

    assert (
        event["camera_id"]
        == "CAM-TEST"
    )

    assert (
        event["track_id"]
        == 5
    )

    assert (
        event["status"]
        == "PENDING"
    )

    assert (
        event["severity"]
        == "HIGH"
    )

    assert (
        event["event_type"]
        == "TRIPWIRE_CROSSED"
    )

    assert event["direction"] in [
        "A_TO_B",
        "B_TO_A",
        "UNKNOWN"
    ]


# ==========================================================
# COOLDOWN / DEDUPLICATION TESTS
# ==========================================================

def test_tripwire_cooldown_blocks_duplicate_event():

    engine = IntrusionRuleEngine(
        create_config()
    )

    # First crossing
    previous = create_detection(
        1,
        10,
        120,
        50,
        160,
        90
    )

    current = create_detection(
        2,
        10,
        220,
        110,
        260,
        130
    )

    first_events = engine.check_tripwires(
        previous,
        current,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            1
        )
    )

    assert len(first_events) == 1

    # Same person crosses again after only 5 seconds.
    #
    # Configured cooldown = 10 seconds.
    #
    # Therefore this event must be blocked.

    second_previous = create_detection(
        3,
        10,
        220,
        110,
        260,
        130
    )

    second_current = create_detection(
        4,
        10,
        120,
        50,
        160,
        90
    )

    second_events = engine.check_tripwires(
        second_previous,
        second_current,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            6
        )
    )

    assert len(second_events) == 0


def test_tripwire_allows_event_after_cooldown():

    engine = IntrusionRuleEngine(
        create_config()
    )

    # First crossing
    previous = create_detection(
        1,
        11,
        120,
        50,
        160,
        90
    )

    current = create_detection(
        2,
        11,
        220,
        110,
        260,
        130
    )

    first_events = engine.check_tripwires(
        previous,
        current,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            1
        )
    )

    assert len(first_events) == 1

    # Same person crosses again after 11 seconds.
    #
    # Cooldown = 10 seconds.
    #
    # Therefore the second event is allowed.

    second_previous = create_detection(
        3,
        11,
        220,
        110,
        260,
        130
    )

    second_current = create_detection(
        4,
        11,
        120,
        50,
        160,
        90
    )

    second_events = engine.check_tripwires(
        second_previous,
        second_current,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            12
        )
    )

    assert len(second_events) == 1

    assert (
        second_events[0]["event_type"]
        == "TRIPWIRE_CROSSED"
    )


def test_different_tracks_have_independent_cooldowns():

    engine = IntrusionRuleEngine(
        create_config()
    )

    # ------------------------------------------------------
    # Track 20 crosses
    # ------------------------------------------------------

    previous_20 = create_detection(
        1,
        20,
        120,
        50,
        160,
        90
    )

    current_20 = create_detection(
        2,
        20,
        220,
        110,
        260,
        130
    )

    events_20 = engine.check_tripwires(
        previous_20,
        current_20,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            1
        )
    )

    assert len(events_20) == 1

    # ------------------------------------------------------
    # Track 21 crosses immediately afterward
    # ------------------------------------------------------
    #
    # Track 21 is a different person.
    #
    # Therefore Track 20's cooldown must NOT block
    # Track 21's event.

    previous_21 = create_detection(
        3,
        21,
        120,
        50,
        160,
        90
    )

    current_21 = create_detection(
        4,
        21,
        220,
        110,
        260,
        130
    )

    events_21 = engine.check_tripwires(
        previous_21,
        current_21,
        datetime(
            2026,
            10,
            4,
            12,
            0,
            2
        )
    )

    assert len(events_21) == 1

    assert (
        events_21[0]["track_id"]
        == 21
    )

