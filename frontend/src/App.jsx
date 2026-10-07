import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";
const WS_BASE_URL = "ws://127.0.0.1:8000";

// =============================================================
// HELPER FUNCTIONS
// =============================================================

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function firstValue(...values) {
  for (const value of values) {
    if (value !== undefined && value !== null && value !== "") {
      return value;
    }
  }
  return null;
}

// -------------------------------------------------------------
// Normalize Evidence
// -------------------------------------------------------------

function normalizeEvidence(item) {
  if (!isObject(item)) {
    return { frame: null, clip: null };
  }

  const evidence = isObject(item.evidence) ? item.evidence : {};

  const frame = firstValue(
    item.evidence_frame,
    item.evidence_frame_filename,
    item.frame_filename,
    item.frame,
    evidence.frame,
    evidence.frame_filename
  );

  const clip = firstValue(
    item.evidence_clip,
    item.evidence_clip_filename,
    item.clip_filename,
    item.clip,
    evidence.clip,
    evidence.clip_filename
  );

  return { frame, clip };
}

// -------------------------------------------------------------
// Normalize Incident
// -------------------------------------------------------------

function normalizeIncident(item, fallback = {}) {
  if (!isObject(item)) {
    return null;
  }

  const evidence = normalizeEvidence(item);

  return {
    ...item,
    incident_id: firstValue(item.incident_id, item.id, fallback.incident_id),
    title: firstValue(
      item.title,
      item.name,
      item.event_name,
      fallback.title,
      "Potential Unauthorized Access"
    ),
    event_type: firstValue(
      item.event_type,
      item.type,
      fallback.event_type,
      "INTRUSION"
    ),
    camera_id: firstValue(item.camera_id, fallback.camera_id, "CAM-01"),
    frame_id: firstValue(item.frame_id, item.frameId, fallback.frame_id),
    track_id: firstValue(item.track_id, item.trackId, fallback.track_id),
    severity: firstValue(item.severity, fallback.severity, "MEDIUM"),
    confidence: firstValue(item.confidence, fallback.confidence, 0),
    status: firstValue(
      item.status,
      item.review_status,
      item.review?.decision,
      fallback.status,
      "PENDING"
    ),
    timestamp: firstValue(
      item.timestamp,
      item.time,
      item.created_at,
      fallback.timestamp
    ),
    evidence,
  };
}

// -------------------------------------------------------------
// Recursively extract incident objects (UNCHANGED)
// -------------------------------------------------------------

function extractIncidents(data) {
  const found = [];

  const visit = (value, context = {}) => {
    if (!value) {
      return;
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        visit(item, context);
      }
      return;
    }

    if (!isObject(value)) {
      return;
    }

    const looksLikeIncident =
      value.incident_id ||
      value.incidentId ||
      value.title ||
      value.event_type ||
      value.eventType ||
      value.evidence ||
      value.severity;

    if (
      looksLikeIncident &&
      (value.incident_id ||
        value.incidentId ||
        value.evidence ||
        value.event_type ||
        value.title)
    ) {
      const incident = normalizeIncident(value, context);
      if (incident) {
        found.push(incident);
      }
    }

    const containers = [
      value.incidents,
      value.incident,
      value.new_incident,
      value.data?.incidents,
      value.result?.incidents,
      value.result?.incident,
      value.result?.results,
      value.results,
      value.all_results,
      value.frame_results,
      value.event_results,
    ];

    for (const container of containers) {
      if (container) {
        visit(container, context);
      }
    }

    if (Array.isArray(value.events) || Array.isArray(value.event_list)) {
      const eventArray = value.events || value.event_list || [];

      for (const event of eventArray) {
        if (!isObject(event)) {
          continue;
        }

        const possibleIncident = event.incident || event.incident_data || event;

        if (
          possibleIncident &&
          (possibleIncident.incident_id ||
            possibleIncident.event_type ||
            possibleIncident.evidence ||
            possibleIncident.severity)
        ) {
          const incident = normalizeIncident(possibleIncident, {
            camera_id: value.camera_id,
            frame_id: value.frame_id,
            track_id: possibleIncident.track_id || event.track_id,
          });

          if (incident) {
            found.push(incident);
          }
        }
      }
    }
  };

  visit(data);

  const unique = [];
  const seen = new Set();

  for (const incident of found) {
    const key =
      incident.incident_id ||
      `${incident.event_type}-${incident.camera_id}-${incident.frame_id}-${incident.track_id}-${incident.timestamp}`;

    if (!seen.has(key)) {
      seen.add(key);
      unique.push(incident);
    }
  }

  return unique;
}

// -------------------------------------------------------------
// EVENTS: normalize / key / extract / merge
// -------------------------------------------------------------

// Keys that hold event(s) inside a message or an incident.
const EVENT_KEYS = [
  "events",
  "event_list",
  "event",
  "event_data",
  "event_details",
];

// Keys that may contain nested messages/incidents/results to walk into.
const CONTAINER_KEYS = [
  "data",
  "payload",
  "result",
  "results",
  "all_results",
  "frame_results",
  "event_results",
  "incidents",
  "incident",
  "new_incident",
];

function normalizeEvent(raw, context = {}) {
  // Widened on purpose: the real backend key for the frame number is
  // unconfirmed (no access to the backend source). This checks every
  // plausible key, including one level of nesting, before falling back
  // to context or "-". Narrow this list once the real key is confirmed.
  const nestedFrameSource = isObject(raw.frame) ? raw.frame : {};

  const frame_id = firstValue(
    raw.frame_id,
    raw.frameId,
    raw.frame_number,
    raw.frameNumber,
    raw.frame_index,
    raw.frameIndex,
    raw.frame_no,
    raw.frameNo,
    typeof raw.frame === "number" || typeof raw.frame === "string"
      ? raw.frame
      : null,
    nestedFrameSource.id,
    nestedFrameSource.frame_id,
    nestedFrameSource.number,
    nestedFrameSource.index,
    context.frame_id
  );

  return {
    ...raw,
    event_id: firstValue(raw.event_id, raw.eventId, raw.id),
    event_type: firstValue(
      raw.event_type,
      raw.eventType,
      raw.type,
      "INTRUSION_EVENT"
    ),
    camera_id: firstValue(raw.camera_id, context.camera_id, "CAM-01"),
    frame_id,
    track_id: firstValue(raw.track_id, raw.trackId, context.track_id),
    timestamp: firstValue(raw.timestamp, raw.time, context.timestamp),
  };
}

// One dedupe key used everywhere (extract, fetch, websocket state merge).
function getEventKey(event) {
  if (event.event_id !== undefined && event.event_id !== null) {
    return `id:${event.event_id}`;
  }
  return `k:${event.event_type}-${event.camera_id}-${event.frame_id}-${event.track_id}-${event.timestamp ?? ""}`;
}

function extractEvents(data) {
  const found = [];

  // Items directly under an event key: arrays of events or a single event.
  const collect = (value, context) => {
    if (Array.isArray(value)) {
      for (const item of value) {
        collect(item, context);
      }
      return;
    }
    if (!isObject(value)) {
      return; // ignores numeric counts such as frame.events = 3
    }
    found.push(normalizeEvent(value, context));
  };

  const visit = (value, context = {}, depth = 0) => {
    if (!value || depth > 6) {
      return;
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        visit(item, context, depth + 1);
      }
      return;
    }

    if (!isObject(value)) {
      return;
    }

    const isIncident = Boolean(value.incident_id || value.incidentId);

    const ctx = {
      camera_id: firstValue(value.camera_id, context.camera_id),
      frame_id: firstValue(
        value.frame_id,
        value.frameId,
        value.frame_number,
        value.frameNumber,
        value.frame_index,
        value.frameIndex,
        typeof value.frame === "number" || typeof value.frame === "string"
          ? value.frame
          : null,
        context.frame_id
      ),
      track_id: firstValue(value.track_id, value.trackId, context.track_id),
      timestamp: firstValue(value.timestamp, context.timestamp),
    };

    // Events stored under known keys (message level or inside an incident).
    for (const key of EVENT_KEYS) {
      if (value[key]) {
        collect(value[key], ctx);
      }
    }

    // A bare event object (not an incident).
    if (
      !isIncident &&
      (value.event_id || value.eventId || value.event_type || value.eventType)
    ) {
      found.push(normalizeEvent(value, context));
    }

    // Walk into nested containers.
    for (const key of CONTAINER_KEYS) {
      if (value[key]) {
        visit(value[key], ctx, depth + 1);
      }
    }
  };

  visit(data);

  const unique = [];
  const seen = new Set();

  for (const event of found) {
    const key = getEventKey(event);
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(event);
    }
  }

  return unique;
}

// Fallback ONLY: when a message carries incidents but no event objects,
// derive one event row per incident so the Events tab is not blank.
// The incident's own frame_id is tried first (confirmed to exist on the
// incident objects); the rest are safety-net fallbacks in case the real
// backend key differs or the value is nested one level inside the
// incident (e.g. incident.event.frame_id).
function eventsFromIncidents(incidents) {
  return incidents.map((incident) => {
    const nested =
      (isObject(incident.event) && incident.event) ||
      (isObject(incident.event_data) && incident.event_data) ||
      (isObject(incident.source_event) && incident.source_event) ||
      {};

    const frame_id = firstValue(
      incident.frame_id,
      incident.frameId,
      incident.frame_number,
      incident.frameNumber,
      incident.frame,
      nested.frame_id,
      nested.frameId,
      nested.frame_number,
      nested.frame
    );

    return {
      event_id: firstValue(
        incident.event_id,
        incident.source_event_id,
        incident.incident_id ? `incident-${incident.incident_id}` : null
      ),
      event_type: incident.event_type,
      camera_id: incident.camera_id,
      frame_id,
      track_id: incident.track_id,
      timestamp: incident.timestamp,
      severity: incident.severity,
      derived: true,
    };
  });
}

// Merge incoming events into existing ones.
// - Empty incoming NEVER clears existing events.
// - Real events replace previously derived (fallback) ones.
// - Same key = updated in place (no duplicates).
function mergeEvents(previous, incoming, fallback = []) {
  let toAdd = incoming;

  if (toAdd.length === 0) {
    // Only skip the fallback if we already have REAL (non-derived) events.
    // Derived placeholders already stored are allowed to be refreshed by a
    // later, possibly better-informed fallback (e.g. once frame_id is found).
    const previousHasReal = previous.some((event) => !event.derived);

    if (fallback.length === 0 || previousHasReal) {
      return previous;
    }
    toAdd = fallback;
  }

  const hasReal = toAdd.some((event) => !event.derived);
  const base = hasReal ? previous.filter((event) => !event.derived) : previous;

  const map = new Map();
  for (const event of [...base, ...toAdd]) {
    const key = getEventKey(event);
    const existing = map.get(key);

    if (!existing) {
      map.set(key, event);
      continue;
    }

    // Merge field by field: a null/undefined incoming value never
    // overwrites a previously known-good value for the same field.
    const merged = { ...existing };
    for (const [field, value] of Object.entries(event)) {
      if (value !== null && value !== undefined && value !== "") {
        merged[field] = value;
      }
    }
    map.set(key, merged);
  }

  return Array.from(map.values()).slice(-500);
}

// =============================================================
// MAIN APP
// =============================================================

function App() {
  // =========================================================
  // GLOBAL STATE
  // =========================================================

  const [activePage, setActivePage] = useState("cctv");
  const [backendStatus, setBackendStatus] = useState("checking");
  const [incidents, setIncidents] = useState([]);
  const [events, setEvents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);

  // =========================================================
  // UPLOAD STATE
  // =========================================================

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadId, setUploadId] = useState(null);
  const [uploadedVideoPath, setUploadedVideoPath] = useState(null);
  const [uploading, setUploading] = useState(false);

  // =========================================================
  // MONITORING
  // =========================================================

  const [monitoring, setMonitoring] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [monitoringMessage, setMonitoringMessage] = useState(
    "Select a CCTV video to begin."
  );

  // =========================================================
  // LIVE FRAME
  // =========================================================

  const [streamImage, setStreamImage] = useState("");
  const [streamStats, setStreamStats] = useState({
    frameId: 0,
    detections: 0,
    events: 0,
    fps: 0,
  });

  // =========================================================
  // REFS
  // =========================================================

  const fileInputRef = useRef(null);
  const websocketRef = useRef(null);

  // =========================================================
  // EVENT STATE HELPER (merge only, never clears)
  // =========================================================

  const addEvents = (incoming, fallback = []) => {
    if (
      (!incoming || incoming.length === 0) &&
      (!fallback || fallback.length === 0)
    ) {
      return;
    }
    setEvents((previous) => mergeEvents(previous, incoming || [], fallback));
  };

  // =========================================================
  // BACKEND HEALTH
  // =========================================================

  const checkBackend = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);

      if (!response.ok) {
        throw new Error("Backend unavailable");
      }

      setBackendStatus("online");
    } catch (error) {
      console.error("Backend health error:", error);
      setBackendStatus("offline");
    }
  };

  // =========================================================
  // FETCH INCIDENTS + RESULTS
  // =========================================================

  const fetchIncidents = async () => {
    try {
      const responses = await Promise.allSettled([
        fetch(`${API_BASE_URL}/api/v1/modules/module_03/incidents`),
        fetch(`${API_BASE_URL}/api/v1/modules/module_03/results`),
      ]);

      let allIncidents = [];
      let allEvents = [];

      for (const result of responses) {
        if (result.status !== "fulfilled" || !result.value.ok) {
          continue;
        }

        const data = await result.value.json();

        allIncidents.push(...extractIncidents(data));
        allEvents.push(...extractEvents(data));
      }

      // Remove duplicate incidents
      const incidentMap = new Map();

      for (const incident of allIncidents) {
        const key =
          incident.incident_id ||
          `${incident.event_type}-${incident.camera_id}-${incident.frame_id}-${incident.track_id}`;

        if (!incidentMap.has(key)) {
          incidentMap.set(key, incident);
        }
      }

      const finalIncidents = Array.from(incidentMap.values());

      if (finalIncidents.length > 0) {
        setIncidents(finalIncidents);
      }

      // Events: merge, never overwrite with an empty result
      addEvents(allEvents, eventsFromIncidents(finalIncidents));
    } catch (error) {
      console.error("Fetch incidents error:", error);
    }
  };

  // =========================================================
  // INITIAL LOAD
  // =========================================================

  useEffect(() => {
    checkBackend();
    fetchIncidents();

    const interval = setInterval(() => {
      checkBackend();
    }, 10000);

    return () => {
      clearInterval(interval);

      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, []);

  // =========================================================
  // FILE SELECT
  // =========================================================

  const handleFileSelect = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
    setUploadId(null);
    setUploadedVideoPath(null);
    setStreamImage("");
    setStreamStats({ frameId: 0, detections: 0, events: 0, fps: 0 });
    setIncidents([]);
    setEvents([]);
    setMonitoringMessage(`Selected video: ${file.name}.`);
  };

  // =========================================================
  // UPLOAD
  // =========================================================

  const uploadVideo = async () => {
    if (!selectedFile) {
      alert("Please choose a CCTV video first.");
      return null;
    }

    if (uploading) {
      return null;
    }

    try {
      setUploading(true);
      setMonitoringMessage(`Uploading ${selectedFile.name}...`);

      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/modules/module_03/upload`,
        { method: "POST", body: formData }
      );

      const data = await response.json();

      if (!response.ok || data.status !== "success") {
        throw new Error(data?.message || "Video upload failed.");
      }

      setUploadId(data.upload_id);
      setUploadedVideoPath(data.video_path || null);
      setMonitoringMessage("Video uploaded successfully. Ready to monitor.");

      return data.upload_id;
    } catch (error) {
      console.error("Upload error:", error);
      setMonitoringMessage(`Upload failed: ${error.message}`);
      alert(`Video upload failed.\n\n${error.message}`);
      return null;
    } finally {
      setUploading(false);
    }
  };

  // =========================================================
  // START MONITORING
  // =========================================================

  const startMonitoring = async () => {
    if (monitoring) {
      return;
    }

    if (!selectedFile) {
      alert("Please choose a CCTV video first.");
      return;
    }

    try {
      let activeUploadId = uploadId;

      if (!activeUploadId) {
        activeUploadId = await uploadVideo();

        if (!activeUploadId) {
          return;
        }
      }

      setMonitoring(true);
      setProcessing(true);
      setStreamImage("");
      setStreamStats({ frameId: 0, detections: 0, events: 0, fps: 0 });
      setIncidents([]);
      setEvents([]);
      setMonitoringMessage("Connecting to CCTV processing stream...");

      if (websocketRef.current) {
        websocketRef.current.close();
      }

      const ws = new WebSocket(
        `${WS_BASE_URL}/api/v1/modules/module_03/stream`
      );

      websocketRef.current = ws;

      // ---------------------------------------------------
      // OPEN
      // ---------------------------------------------------

      ws.onopen = () => {
        setMonitoringMessage("CCTV connected. YOLO11n analysis started...");

        ws.send(
          JSON.stringify({
            upload_id: activeUploadId,
            camera_id: "CAM-01",
          })
        );
      };

      // ---------------------------------------------------
      // MESSAGE
      // ---------------------------------------------------

      ws.onmessage = async (message) => {
        try {
          const data = JSON.parse(message.data);

          // STARTED
          if (data.type === "started") {
            setMonitoring(true);
            setProcessing(true);
            return;
          }

          // FRAME
          if (data.type === "frame") {
            if (data.image) {
              setStreamImage(`data:image/jpeg;base64,${data.image}`);
            }

            setStreamStats({
              frameId: firstValue(data.frame_id, data.frameId, 0),
              detections: firstValue(
                data.detections,
                data.detection_count,
                0
              ),
              events: firstValue(data.events, data.event_count, 0),
              fps: firstValue(data.fps, 0),
            });

            const frameIncidents = extractIncidents(data);
            const frameEvents = extractEvents(data);

            addEvents(frameEvents, eventsFromIncidents(frameIncidents));

            if (frameIncidents.length > 0) {
              setIncidents((previous) => {
                const map = new Map();

                for (const incident of [...previous, ...frameIncidents]) {
                  const key =
                    incident.incident_id ||
                    `${incident.event_type}-${incident.frame_id}-${incident.track_id}`;

                  map.set(key, incident);
                }

                return Array.from(map.values());
              });
            }

            return;
          }

          // INCIDENT
          if (data.type === "incident" || data.type === "new_incident") {
            const extracted = extractIncidents(data);

            // Events embedded in / alongside the incident message
            addEvents(extractEvents(data), eventsFromIncidents(extracted));

            if (extracted.length > 0) {
              setIncidents((previous) => {
                const map = new Map();

                for (const incident of [...previous, ...extracted]) {
                  const key =
                    incident.incident_id ||
                    `${incident.event_type}-${incident.frame_id}-${incident.track_id}`;

                  map.set(key, incident);
                }

                return Array.from(map.values());
              });
            }

            return;
          }

          // COMPLETE
          if (data.type === "complete") {
            if (Array.isArray(data.incidents) && data.incidents[0]) {
              // TEMP diagnostic — remove once frame_id is confirmed.
              console.log("RAW INCIDENT[0]:", data.incidents[0]);
            }

            const completedIncidents = extractIncidents(data);
            const completedEvents = extractEvents(data);

            if (completedIncidents.length > 0) {
              setIncidents(completedIncidents);
            }

            // Merge only: an empty/absent event array never wipes events.
            addEvents(completedEvents, eventsFromIncidents(completedIncidents));

            setProcessing(false);
            setMonitoring(false);

            setMonitoringMessage(
              `Processing completed. ${completedIncidents.length} incident(s) detected.`
            );

            // Give backend a moment to finish writing evidence.
            setTimeout(() => {
              fetchIncidents();
            }, 1000);

            return;
          }

          // ERROR
          if (data.type === "error") {
            console.error("Backend error:", data);

            setProcessing(false);
            setMonitoring(false);
            setMonitoringMessage(data.message || "CCTV processing failed.");

            alert(data.message || "CCTV processing failed.");
          }
        } catch (error) {
          console.error("WS parse error:", error);
        }
      };

      // ---------------------------------------------------
      // ERROR
      // ---------------------------------------------------

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);

        setProcessing(false);
        setMonitoring(false);
        setMonitoringMessage("Unable to connect to CCTV processing stream.");
      };

      // ---------------------------------------------------
      // CLOSE
      // ---------------------------------------------------

      ws.onclose = () => {
        websocketRef.current = null;
      };
    } catch (error) {
      console.error("Start monitoring error:", error);

      setProcessing(false);
      setMonitoring(false);
    }
  };

  // =========================================================
  // STOP
  // =========================================================

  const stopMonitoring = () => {
    if (websocketRef.current) {
      try {
        websocketRef.current.send(JSON.stringify({ action: "stop" }));
      } catch (error) {
        console.log(error);
      }

      websocketRef.current.close();
      websocketRef.current = null;
    }

    setMonitoring(false);
    setProcessing(false);
    setMonitoringMessage("Monitoring stopped.");
  };

  // =========================================================
  // CLEAR
  // =========================================================

  const clearVideo = () => {
    stopMonitoring();

    setSelectedFile(null);
    setUploadId(null);
    setUploadedVideoPath(null);
    setStreamImage("");
    setStreamStats({ frameId: 0, detections: 0, events: 0, fps: 0 });
    setIncidents([]);
    setEvents([]);
    setMonitoringMessage("Select a CCTV video to begin.");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // =========================================================
  // EVIDENCE URLS
  // =========================================================

  const getEvidenceFrameUrl = (filename) => {
    if (!filename) {
      return null;
    }

    let cleanPath = String(filename);
    cleanPath = cleanPath.replace(/^.*?evidence[\\/]/, "evidence/");
    const filenameOnly = cleanPath.split(/[\\/]/).pop();

    return `${API_BASE_URL}/api/v1/modules/module_03/evidence/frames/${encodeURIComponent(
      filenameOnly
    )}`;
  };

  const getEvidenceClipUrl = (filename) => {
    if (!filename) {
      return null;
    }

    let cleanPath = String(filename);
    cleanPath = cleanPath.replace(/^.*?evidence[\\/]/, "evidence/");
    const filenameOnly = cleanPath.split(/[\\/]/).pop();

    return `${API_BASE_URL}/api/v1/modules/module_03/evidence/clips/${encodeURIComponent(
      filenameOnly
    )}`;
  };

  // =========================================================
  // NAVIGATION
  // =========================================================

  const navigationItems = [
    { id: "dashboard", icon: "▦", label: "Dashboard" },
    { id: "cctv", icon: "▣", label: "CCTV Monitoring" },
    { id: "incidents", icon: "⚠", label: "Incidents" },
    { id: "events", icon: "◉", label: "Events" },
    { id: "evidence", icon: "▤", label: "Evidence" },
    { id: "settings", icon: "⚙", label: "Settings" },
  ];

  // =========================================================
  // DASHBOARD
  // =========================================================

  const renderDashboard = () => {
    const highCount = incidents.filter(
      (item) => String(item.severity || "").toUpperCase() === "HIGH"
    ).length;

    const mediumCount = incidents.filter(
      (item) => String(item.severity || "").toUpperCase() === "MEDIUM"
    ).length;

    const pendingCount = incidents.filter(
      (item) => String(item.status || "PENDING").toUpperCase() === "PENDING"
    ).length;

    return (
      <>
        <div className="header">
          <div>
            <h2>Dashboard</h2>
            <p>NEXORA Security Intelligence</p>
          </div>

          <button
            className="refresh-button"
            onClick={() => {
              checkBackend();
              fetchIncidents();
            }}
          >
            Refresh
          </button>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">◉</div>
            <div>
              <span>Total Incidents</span>
              <strong>{incidents.length}</strong>
              <small>Module 03</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon danger">!</div>
            <div>
              <span>High Severity</span>
              <strong>{highCount}</strong>
              <small>Requires attention</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon warning">⚠</div>
            <div>
              <span>Medium Severity</span>
              <strong>{mediumCount}</strong>
              <small>Monitoring required</small>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon medium">◌</div>
            <div>
              <span>Pending Review</span>
              <strong>{pendingCount}</strong>
              <small>Human verification</small>
            </div>
          </div>
        </div>

        <div className="module-section">
          <div className="section-header">
            <div>
              <div className="section-label">ACTIVE MODULE</div>
              <h3>Intrusion & Unauthorized Access Monitoring</h3>
            </div>

            <span className="module-status">● ONLINE</span>
          </div>

          <div className="module-info">
            <div className="module-item">
              <span>MODULE</span>
              <strong>Module 03</strong>
            </div>

            <div className="module-item">
              <span>MODEL</span>
              <strong>YOLO11n</strong>
            </div>

            <div className="module-item">
              <span>TRACKING</span>
              <strong>ByteTrack</strong>
            </div>

            <div className="module-item">
              <span>STATUS</span>
              <strong>
                {backendStatus === "online"
                  ? "Backend Online"
                  : "Backend Offline"}
              </strong>
            </div>
          </div>
        </div>

        <IncidentsList incidents={incidents} onSelect={setSelectedIncident} />
      </>
    );
  };

  // =========================================================
  // CCTV
  // =========================================================

  const renderCCTV = () => {
    return (
      <>
        <div className="header">
          <div>
            <h2>CCTV Monitoring</h2>
            <p>
              Upload CCTV footage for YOLO11n, ByteTrack and intrusion
              analysis.
            </p>
          </div>

          <button
            className="refresh-button"
            onClick={() => {
              checkBackend();
              fetchIncidents();
            }}
          >
            Refresh
          </button>
        </div>

        <div className="page-card camera-card">
          <div className="camera-preview">
            {streamImage ? (
              <>
                <img
                  src={streamImage}
                  alt="Processed CCTV frame"
                  className="camera-video"
                />

                {monitoring && (
                  <div className="live-badge monitoring-badge">
                    ● PROCESSING
                  </div>
                )}
              </>
            ) : (
              <div className="camera-placeholder">
                <span className="camera-large-icon">📹</span>
                <strong>CCTV Monitoring</strong>
                <small>Upload a video to begin analysis</small>
              </div>
            )}
          </div>

          <div className="camera-control">
            <div className="camera-status-row">
              <span>CCTV Video</span>

              <span
                className={
                  monitoring
                    ? "camera-ready"
                    : selectedFile
                    ? "camera-ready"
                    : "camera-online"
                }
              >
                {monitoring
                  ? "Monitoring"
                  : selectedFile
                  ? "Video Selected"
                  : "Waiting for Video"}
              </span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                flexWrap: "wrap",
                marginBottom: "14px",
              }}
            >
              <button
                type="button"
                className="camera-refresh-button"
                onClick={() => fileInputRef.current?.click()}
                disabled={monitoring}
              >
                📁 Choose CCTV Video
              </button>

              <input
                ref={fileInputRef}
                type="file"
                accept="video/*,.mp4,.avi,.mov,.mkv"
                onChange={handleFileSelect}
                style={{ display: "none" }}
              />

              {selectedFile && (
                <span style={{ color: "#cbd5e1", fontSize: "13px" }}>
                  {selectedFile.name}
                </span>
              )}
            </div>

            {selectedFile && (
              <div className="camera-message">
                <strong>Selected video:</strong> {selectedFile.name}
                <br />
                <span style={{ color: "#737986", fontSize: "12px" }}>
                  Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </span>

                {uploadId && (
                  <>
                    <br />
                    <span style={{ color: "#4ade80", fontSize: "12px" }}>
                      ✓ Uploaded to backend
                    </span>
                  </>
                )}
              </div>
            )}

            <div className="camera-message">{monitoringMessage}</div>

            <div className="camera-buttons">
              <button
                type="button"
                className="camera-refresh-button"
                onClick={uploadVideo}
                disabled={!selectedFile || uploading || monitoring}
              >
                {uploading
                  ? "⏳ Uploading..."
                  : uploadId
                  ? "✓ Uploaded"
                  : "⬆ Upload Video"}
              </button>

              <button
                type="button"
                className="start-monitoring-button"
                onClick={startMonitoring}
                disabled={!selectedFile || monitoring || uploading}
              >
                ▶ Start Monitoring
              </button>

              <button
                type="button"
                className="stop-monitoring-button"
                onClick={stopMonitoring}
                disabled={!monitoring}
              >
                ■ Stop Monitoring
              </button>

              <button
                type="button"
                className="camera-refresh-button"
                onClick={clearVideo}
                disabled={monitoring || uploading}
              >
                Clear
              </button>
            </div>

            {processing && (
              <div className="processing-bar">
                <div className="processing-spinner" />

                <span>
                  Processing frame {streamStats.frameId}... YOLO11n + ByteTrack
                  + intrusion rules
                </span>
              </div>
            )}
          </div>

          <div className="camera-info">
            <div>
              <span>Current Frame</span>
              <strong>{streamStats.frameId}</strong>
            </div>

            <div>
              <span>Persons Detected</span>
              <strong>{streamStats.detections}</strong>
            </div>

            <div>
              <span>Events</span>
              <strong>{events.length}</strong>
            </div>

            <div>
              <span>Incidents</span>
              <strong>{incidents.length}</strong>
            </div>
          </div>
        </div>

        <IncidentsList incidents={incidents} onSelect={setSelectedIncident} />
      </>
    );
  };

  // =========================================================
  // INCIDENTS
  // =========================================================

  const renderIncidents = () => (
    <>
      <div className="header">
        <div>
          <h2>Incidents</h2>
          <p>Intrusion incidents detected by Module 03.</p>
        </div>

        <button className="refresh-button" onClick={fetchIncidents}>
          Refresh
        </button>
      </div>

      <IncidentsList incidents={incidents} onSelect={setSelectedIncident} />
    </>
  );

  // =========================================================
  // EVENTS
  // =========================================================

  const renderEvents = () => (
    <>
      <div className="header">
        <div>
          <h2>Events</h2>
          <p>Events generated during CCTV analysis.</p>
        </div>

        <button className="refresh-button" onClick={fetchIncidents}>
          Refresh
        </button>
      </div>

      <div className="page-card">
        {events.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">◉</div>
            <h4>No events yet</h4>
            <p>Start CCTV monitoring to generate events.</p>
          </div>
        ) : (
          <div className="event-list">
            {events
              .slice()
              .reverse()
              .map((event, index) => (
                <div
                  className="event-row"
                  key={`${getEventKey(event)}-${index}`}
                >
                  <div className="event-icon">⚠</div>

                  <div className="event-info">
                    <strong>{event.event_type}</strong>
                    <span>Camera: {event.camera_id}</span>
                  </div>

                  <div className="event-meta">
                    <small>Frame {event.frame_id ?? "-"}</small>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </>
  );

  // =========================================================
  // EVIDENCE
  // =========================================================

  const renderEvidence = () => {
    const evidenceIncidents = incidents.filter((incident) => {
      const evidence = normalizeEvidence(incident);
      return evidence.frame || evidence.clip;
    });

    return (
      <>
        <div className="header">
          <div>
            <h2>Evidence</h2>
            <p>Evidence generated from detected incidents.</p>
          </div>

          <button className="refresh-button" onClick={fetchIncidents}>
            Refresh
          </button>
        </div>

        <div className="page-card">
          {evidenceIncidents.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">▤</div>
              <h4>No evidence yet</h4>
              <p>Evidence will appear here after an incident is detected.</p>
            </div>
          ) : (
            <div className="incident-list">
              {evidenceIncidents.map((incident, index) => (
                <div
                  className="incident-card"
                  key={incident.incident_id || index}
                >
                  <div className="incident-main">
                    <div className="incident-icon">⚠</div>

                    <div>
                      <div className="incident-title-row">
                        <h4>{incident.title}</h4>
                      </div>

                      <div className="incident-meta">
                        <span>{incident.camera_id}</span>
                        <span>Frame {incident.frame_id ?? "-"}</span>
                      </div>
                    </div>
                  </div>

                  <div className="incident-right">
                    <button
                      className="evidence-button"
                      onClick={() => setSelectedIncident(incident)}
                    >
                      View Evidence
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </>
    );
  };

  // =========================================================
  // SETTINGS
  // =========================================================

  const renderSettings = () => (
    <>
      <div className="header">
        <div>
          <h2>Settings</h2>
          <p>Module 03 configuration.</p>
        </div>
      </div>

      <div className="settings-grid">
        <div className="settings-card">
          <div className="section-label">SYSTEM</div>
          <h3>Backend</h3>

          <div className="setting-row">
            <span>API Status</span>
            <strong>{backendStatus.toUpperCase()}</strong>
          </div>

          <div className="setting-row">
            <span>API</span>
            <strong>FastAPI</strong>
          </div>

          <div className="setting-row">
            <span>Module</span>
            <strong>Module 03 v1.0.0</strong>
          </div>
        </div>

        <div className="settings-card">
          <div className="section-label">AI PIPELINE</div>
          <h3>Detection</h3>

          <div className="setting-row">
            <span>Detector</span>
            <strong>YOLO11n</strong>
          </div>

          <div className="setting-row">
            <span>Tracker</span>
            <strong>ByteTrack</strong>
          </div>

          <div className="setting-row">
            <span>Rules</span>
            <strong>Zone / Tripwire / Loitering</strong>
          </div>
        </div>
      </div>
    </>
  );

  // =========================================================
  // ROUTER
  // =========================================================

  const renderPage = () => {
    switch (activePage) {
      case "dashboard":
        return renderDashboard();
      case "cctv":
        return renderCCTV();
      case "incidents":
        return renderIncidents();
      case "events":
        return renderEvents();
      case "evidence":
        return renderEvidence();
      case "settings":
        return renderSettings();
      default:
        return renderCCTV();
    }
  };

  // =========================================================
  // MAIN UI
  // =========================================================

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-mark">N</div>

          <div>
            <h1>NEXORA</h1>
            <span>Security Intelligence</span>
          </div>
        </div>

        <nav>
          {navigationItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${activePage === item.id ? "active" : ""}`}
              onClick={() => setActivePage(item.id)}
            >
              <span>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span
              className={`status-dot ${
                backendStatus === "online" ? "online" : "offline"
              }`}
            />

            <div>
              <strong>
                Backend{" "}
                {backendStatus === "online"
                  ? "Online"
                  : backendStatus === "checking"
                  ? "Checking..."
                  : "Offline"}
              </strong>

              <small>Module 03 v1.0.0</small>
            </div>
          </div>
        </div>
      </aside>

      <main className="main">
        {renderPage()}

        <footer>
          <span>NEXORA Security Intelligence</span>
          <span>Module 03 • Intrusion Monitoring</span>
        </footer>
      </main>

      {selectedIncident && (
        <EvidenceModal
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
          getFrameUrl={getEvidenceFrameUrl}
          getClipUrl={getEvidenceClipUrl}
        />
      )}
    </div>
  );
}

// =============================================================
// INCIDENT LIST
// =============================================================

function IncidentsList({ incidents, onSelect }) {
  return (
    <section className="incidents-section">
      <div className="section-header">
        <div>
          <div className="section-label">MODULE 03</div>
          <h3>Detected Incidents</h3>
        </div>

        <span className="incident-count">{incidents.length} incidents</span>
      </div>

      {incidents.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📺</div>
          <h4>No incidents detected yet.</h4>
          <p>Start CCTV monitoring to generate incidents.</p>
        </div>
      ) : (
        <div className="incident-list">
          {incidents.map((incident, index) => {
            const severity = String(incident.severity || "MEDIUM").toLowerCase();

            return (
              <div className="incident-card" key={incident.incident_id || index}>
                <div className="incident-main">
                  <div className="incident-icon">⚠</div>

                  <div>
                    <div className="incident-title-row">
                      <h4>{incident.title}</h4>

                      <span className={`severity ${severity}`}>
                        {severity.toUpperCase()}
                      </span>
                    </div>

                    <div className="incident-meta">
                      <span>Camera: {incident.camera_id}</span>
                      <span>Frame: {incident.frame_id ?? "-"}</span>
                      <span>Track: {incident.track_id ?? "N/A"}</span>
                    </div>
                  </div>
                </div>

                <div className="incident-right">
                  <span className="pending">
                    {String(incident.status || "PENDING").toUpperCase()}
                  </span>

                  <button
                    className="evidence-button"
                    onClick={() => onSelect(incident)}
                  >
                    View
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

// =============================================================
// EVIDENCE MODAL
// =============================================================

function EvidenceModal({ incident, onClose, getFrameUrl, getClipUrl }) {
  const evidence = normalizeEvidence(incident);
  const frameUrl = getFrameUrl(evidence.frame);
  const clipUrl = getClipUrl(evidence.clip);
  const severity = String(incident.severity || "MEDIUM").toLowerCase();

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="evidence-modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="section-label">INCIDENT EVIDENCE</div>
            <h3>{incident.title}</h3>
          </div>

          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="evidence-content">
          <div className="evidence-image-container">
            {frameUrl ? (
              <img
                src={frameUrl}
                alt="Incident evidence"
                className="evidence-image"
                onError={(event) => {
                  console.error("Evidence frame failed:", frameUrl);
                  event.currentTarget.style.display = "none";
                }}
              />
            ) : (
              <div className="evidence-placeholder">
                <h4>No evidence frame</h4>
                <p>
                  This incident does not contain an evidence-frame reference.
                </p>
              </div>
            )}
          </div>

          <div className="evidence-details">
            <div className="detail-row">
              <span>Severity</span>
              <strong className={`severity-text ${severity}`}>
                {severity.toUpperCase()}
              </strong>
            </div>

            <div className="detail-row">
              <span>Status</span>
              <strong>{String(incident.status || "PENDING").toUpperCase()}</strong>
            </div>

            <div className="detail-row">
              <span>Camera</span>
              <strong>{incident.camera_id}</strong>
            </div>

            <div className="detail-row">
              <span>Frame</span>
              <strong>{incident.frame_id ?? "-"}</strong>
            </div>

            <div className="detail-row">
              <span>Track ID</span>
              <strong>{incident.track_id ?? "N/A"}</strong>
            </div>

            <div className="detail-row">
              <span>Confidence</span>
              <strong>
                {incident.confidence
                  ? `${(Number(incident.confidence) * 100).toFixed(1)}%`
                  : "-"}
              </strong>
            </div>

            {incident.zone_name && (
              <div className="detail-row">
                <span>Zone</span>
                <strong>{incident.zone_name}</strong>
              </div>
            )}

            {evidence.frame && (
              <div className="detail-row">
                <span>Evidence Frame</span>
                <strong style={{ fontSize: "11px", wordBreak: "break-all" }}>
                  {evidence.frame}
                </strong>
              </div>
            )}

            {clipUrl && (
              <a
                href={clipUrl}
                target="_blank"
                rel="noreferrer"
                className="clip-button"
              >
                ▶ Open Evidence Clip
              </a>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <span>Human review required before final confirmation.</span>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

export default App;
