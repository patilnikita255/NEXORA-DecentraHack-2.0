import sys
from pathlib import Path

import pytest

MODULE_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(MODULE_ROOT)
)

from rules.incident_manager import (
    IncidentManager,
)


def create_event(
    event_id="EVT-CAM-001-25-19",
    event_type="POTENTIAL_UNAUTHORIZED_ZONE_ENTRY",
):
    return {
        "event_id": event_id,
        "module": "module_03_intrusion",
        "event_type": event_type,
        "camera_id": "CAM-001",
        "track_id": 19,
        "timestamp": "2026-10-05T23:14:00",
        "confidence": 0.91,
        "severity": "HIGH",
        "status": "PENDING",
        "zone_name": "Restricted Zone 1",
        "evidence": {
            "frame": "evidence/frames/EVT-CAM-001-25-19.jpg",
            "clip": "evidence/clips/EVT-CAM-001-25-19.mp4",
        },
    }


def test_create_incident_from_event():
    manager = IncidentManager()

    event = create_event()

    incident = manager.create_incident(
        event
    )

    assert (
        incident["incident_id"]
        == "INC-CAM-001-25-19"
    )

    assert (
        incident["module"]
        == "module_03_intrusion"
    )

    assert (
        incident["event_type"]
        == "POTENTIAL_UNAUTHORIZED_ZONE_ENTRY"
    )

    assert (
        incident["camera_id"]
        == "CAM-001"
    )

    assert (
        incident["track_id"]
        == 19
    )

    assert (
        incident["zone_name"]
        == "Restricted Zone 1"
    )

    assert (
        incident["status"]
        == "PENDING"
    )


def test_incident_contains_required_fields():
    manager = IncidentManager()

    incident = manager.create_incident(
        create_event()
    )

    required_fields = {
        "incident_id",
        "module",
        "title",
        "event_type",
        "camera_id",
        "timestamp",
        "severity",
        "confidence",
        "status",
        "evidence",
        "review",
    }

    assert required_fields.issubset(
        incident.keys()
    )


def test_incident_contains_review_structure():
    manager = IncidentManager()

    incident = manager.create_incident(
        create_event()
    )

    assert incident["review"] == {
        "decision": None,
        "reviewer_id": None,
        "reviewed_at": None,
    }


def test_incident_copies_evidence():
    manager = IncidentManager()

    incident = manager.create_incident(
        create_event()
    )

    assert (
        incident["evidence"]["frame"]
        == "evidence/frames/EVT-CAM-001-25-19.jpg"
    )

    assert (
        incident["evidence"]["clip"]
        == "evidence/clips/EVT-CAM-001-25-19.mp4"
    )


def test_incident_without_evidence():
    manager = IncidentManager()

    event = create_event()

    event.pop("evidence")

    incident = manager.create_incident(
        event
    )

    assert incident["evidence"] == {
        "frame": None,
        "clip": None,
    }


def test_confirm_incident():
    manager = IncidentManager()

    incident = manager.create_incident(
        create_event()
    )

    updated = manager.review_incident(
        incident_id=incident["incident_id"],
        decision="CONFIRM",
        reviewer_id="reviewer-001",
        reviewed_at="2026-10-05T23:20:00",
    )

    assert (
        updated["status"]
        == "CONFIRMED"
    )

    assert (
        updated["review"]["decision"]
        == "CONFIRM"
    )

    assert (
        updated["review"]["reviewer_id"]
        == "reviewer-001"
    )

    assert (
        updated["review"]["reviewed_at"]
        == "2026-10-05T23:20:00"
    )


def test_dismiss_incident():
    manager = IncidentManager()

    incident = manager.create_incident(
        create_event()
    )

    updated = manager.review_incident(
        incident_id=incident["incident_id"],
        decision="DISMISS",
        reviewer_id="reviewer-002",
        reviewed_at="2026-10-05T23:21:00",
    )

    assert (
        updated["status"]
        == "DISMISSED"
    )

    assert (
        updated["review"]["decision"]
        == "DISMISS"
    )


def test_uncertain_incident():
    manager = IncidentManager()

    incident = manager.create_incident(
        create_event()
    )

    updated = manager.review_incident(
        incident_id=incident["incident_id"],
        decision="UNCERTAIN",
        reviewer_id="reviewer-003",
        reviewed_at="2026-10-05T23:22:00",
    )

    assert (
        updated["status"]
        == "UNCERTAIN"
    )

    assert (
        updated["review"]["decision"]
        == "UNCERTAIN"
    )


def test_escalate_incident():
    manager = IncidentManager()

    incident = manager.create_incident(
        create_event()
    )

    updated = manager.review_incident(
        incident_id=incident["incident_id"],
        decision="ESCALATE",
        reviewer_id="reviewer-004",
        reviewed_at="2026-10-05T23:23:00",
    )

    assert (
        updated["status"]
        == "PENDING"
    )

    assert (
        updated["review"]["decision"]
        == "ESCALATE"
    )


def test_invalid_review_decision():
    manager = IncidentManager()

    incident = manager.create_incident(
        create_event()
    )

    with pytest.raises(
        ValueError,
        match="Invalid review decision",
    ):
        manager.review_incident(
            incident_id=incident["incident_id"],
            decision="INVALID",
            reviewer_id="reviewer-001",
        )


def test_review_requires_reviewer():
    manager = IncidentManager()

    incident = manager.create_incident(
        create_event()
    )

    with pytest.raises(
        ValueError,
        match="reviewer_id is required",
    ):
        manager.review_incident(
            incident_id=incident["incident_id"],
            decision="CONFIRM",
            reviewer_id="",
        )


def test_review_unknown_incident():
    manager = IncidentManager()

    with pytest.raises(
        KeyError,
        match="Incident not found",
    ):
        manager.review_incident(
            incident_id="INC-UNKNOWN",
            decision="CONFIRM",
            reviewer_id="reviewer-001",
        )


def test_missing_event_fields_are_rejected():
    manager = IncidentManager()

    event = create_event()

    del event["camera_id"]

    with pytest.raises(
        ValueError,
        match="missing required fields",
    ):
        manager.create_incident(event)


def test_get_incident():
    manager = IncidentManager()

    incident = manager.create_incident(
        create_event()
    )

    retrieved = manager.get_incident(
        incident["incident_id"]
    )

    assert retrieved == incident


def test_get_all_incidents():
    manager = IncidentManager()

    incident_1 = manager.create_incident(
        create_event(
            event_id="EVT-CAM-001-25-19"
        )
    )

    incident_2 = manager.create_incident(
        create_event(
            event_id="EVT-CAM-002-40-21",
            event_type="TRIPWIRE_CROSSED",
        )
    )

    incidents = (
        manager.get_all_incidents()
    )

    assert len(incidents) == 2

    assert incident_1 in incidents
    assert incident_2 in incidents