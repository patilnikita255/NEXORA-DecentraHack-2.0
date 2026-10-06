import sys
from pathlib import Path
from datetime import datetime


class IncidentManager:
    """
    Converts validated NEXORA M03 events into incidents
    and manages human review decisions.

    Flow:

        Event
          ↓
        Incident
          ↓
        Human Review
          ↓
        CONFIRM / DISMISS / UNCERTAIN / ESCALATE
    """

    REVIEW_DECISIONS = {
        "CONFIRM",
        "DISMISS",
        "UNCERTAIN",
        "ESCALATE",
    }

    STATUS_MAP = {
        "CONFIRM": "CONFIRMED",
        "DISMISS": "DISMISSED",
        "UNCERTAIN": "UNCERTAIN",
        "ESCALATE": "PENDING",
    }

    EVENT_TITLES = {
        "POTENTIAL_UNAUTHORIZED_ZONE_ENTRY": (
            "Potential Unauthorized Zone Entry"
        ),
        "TRIPWIRE_CROSSED": (
            "Restricted Area Tripwire Crossed"
        ),
        "LOITERING": (
            "Loitering in Restricted Zone"
        ),
    }

    def __init__(self):
        self.incidents = {}

    # ==========================================================
    # INCIDENT CREATION
    # ==========================================================

    def create_incident(self, event):
        """
        Convert a validated event into a NEXORA incident.

        The original event is not modified.
        """

        if not isinstance(event, dict):
            raise ValueError(
                "Event must be a dictionary."
            )

        required_event_fields = {
            "event_id",
            "module",
            "event_type",
            "camera_id",
            "timestamp",
            "severity",
            "confidence",
            "status",
        }

        missing_fields = (
            required_event_fields
            - event.keys()
        )

        if missing_fields:
            raise ValueError(
                "Event is missing required fields: "
                + ", ".join(
                    sorted(missing_fields)
                )
            )

        event_id = str(
            event["event_id"]
        )

        incident_id = self._create_incident_id(
            event_id
        )

        title = self.EVENT_TITLES.get(
            event["event_type"],
            "M03 Security Monitoring Incident",
        )

        incident = {
            "incident_id": incident_id,
            "module": event["module"],
            "title": title,
            "event_type": event["event_type"],
            "camera_id": event["camera_id"],
            "timestamp": event["timestamp"],
            "severity": event["severity"],
            "confidence": event["confidence"],
            "status": "PENDING",
            "evidence": self._copy_evidence(
                event
            ),
            "review": {
                "decision": None,
                "reviewer_id": None,
                "reviewed_at": None,
            },
        }

        # Preserve useful M03 context when available.
        if "track_id" in event:
            incident["track_id"] = event[
                "track_id"
            ]

        if "zone_name" in event:
            incident["zone_name"] = event[
                "zone_name"
            ]

        if "direction" in event:
            incident["direction"] = event[
                "direction"
            ]

        self.incidents[incident_id] = incident

        return incident

    # ==========================================================
    # HUMAN REVIEW
    # ==========================================================

    def review_incident(
        self,
        incident_id,
        decision,
        reviewer_id,
        reviewed_at=None,
    ):
        """
        Apply a human review decision.

        Supported decisions:

        CONFIRM
        DISMISS
        UNCERTAIN
        ESCALATE
        """

        if incident_id not in self.incidents:
            raise KeyError(
                f"Incident not found: {incident_id}"
            )

        if decision not in self.REVIEW_DECISIONS:
            raise ValueError(
                "Invalid review decision. "
                "Expected one of: "
                + ", ".join(
                    sorted(
                        self.REVIEW_DECISIONS
                    )
                )
            )

        if not reviewer_id:
            raise ValueError(
                "reviewer_id is required."
            )

        if reviewed_at is None:
            reviewed_at = datetime.now().isoformat()

        incident = self.incidents[
            incident_id
        ]

        incident["status"] = self.STATUS_MAP[
            decision
        ]

        incident["review"] = {
            "decision": decision,
            "reviewer_id": str(
                reviewer_id
            ),
            "reviewed_at": reviewed_at,
        }

        return incident

    # ==========================================================
    # GET INCIDENT
    # ==========================================================

    def get_incident(self, incident_id):
        """
        Return one incident.
        """

        return self.incidents.get(
            incident_id
        )

    # ==========================================================
    # GET ALL INCIDENTS
    # ==========================================================

    def get_all_incidents(self):
        """
        Return all incidents.
        """

        return list(
            self.incidents.values()
        )

    # ==========================================================
    # HELPERS
    # ==========================================================

    @staticmethod
    def _create_incident_id(event_id):
        """
        Convert:

            EVT-CAM-001-25-19

        into:

            INC-CAM-001-25-19
        """

        if event_id.startswith("EVT-"):
            return (
                "INC-"
                + event_id[4:]
            )

        return (
            "INC-"
            + event_id
        )

    @staticmethod
    def _copy_evidence(event):
        """
        Copy evidence information from the event.

        Evidence is optional because an event may be
        generated before the evidence clip is finalized.
        """

        evidence = event.get(
            "evidence"
        )

        if not evidence:
            return {
                "frame": None,
                "clip": None,
            }

        return {
            "frame": evidence.get(
                "frame"
            ),
            "clip": evidence.get(
                "clip"
            ),
        }
