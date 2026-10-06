import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

const M03_VIDEO_PATH =
  "/Users/vijaykrishnajathare/Documents/NEXORA/ml/modules/module_03_intrusion/test_videos/test.mp4";

function App() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [activePage, setActivePage] = useState("dashboard");

  const [monitoring, setMonitoring] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [monitoringMessage, setMonitoringMessage] =
    useState("Camera ready");

  const [abortController, setAbortController] =
    useState(null);

  useEffect(() => {
    fetchIncidents();
  }, []);

  const fetchIncidents = async () => {
    setLoading(true);

    try {
      const healthResponse = await fetch(
        `${API_BASE_URL}/api/v1/health`
      );

      setBackendStatus(
        healthResponse.ok ? "Online" : "Offline"
      );

      const response = await fetch(
        `${API_BASE_URL}/api/v1/modules/module_03/incidents`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch incidents");
      }

      const data = await response.json();

      setIncidents(data.incidents || []);
    } catch (error) {
      console.error("Backend connection failed:", error);
      setBackendStatus("Offline");
      setIncidents([]);
    } finally {
      setLoading(false);
    }
  };

  /* =========================
   START CAMERA MONITORING
========================= */

const startMonitoring = async (videoRef) => {

  if (processing) {
    return;
  }

  if (backendStatus !== "Online") {
    setMonitoringMessage(
      "Backend is offline. Start FastAPI first."
    );
    return;
  }

  const controller = new AbortController();

  setAbortController(controller);
  setMonitoring(true);
  setProcessing(true);
  setMonitoringMessage(
    "M03 is analyzing the camera video..."
  );

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/modules/module_03/process`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        signal: controller.signal,
        body: JSON.stringify({
          video_path: M03_VIDEO_PATH,
          camera_id: "CAM-01",
          display: false,
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(
        () => ({})
      );

      throw new Error(
        errorData.detail ||
          "M03 processing failed"
      );
    }

    const data = await response.json();

    const detectedIncidents =
      data?.result?.incidents || [];

    setIncidents(detectedIncidents);

    setMonitoringMessage(
      `Monitoring completed • ${detectedIncidents.length} incidents detected`
    );

    setMonitoring(false);

  } catch (error) {

    if (error.name === "AbortError") {

      setMonitoringMessage(
        "Monitoring request cancelled"
      );

    } else {

      console.error(
        "M03 monitoring failed:",
        error
      );

      setMonitoringMessage(
        `Monitoring failed: ${error.message}`
      );
    }

    setMonitoring(false);

  } finally {

    setProcessing(false);
    setAbortController(null);
  }
};

  /* =========================
     STOP CAMERA MONITORING
  ========================= */

  const stopMonitoring = () => {
    if (abortController) {
      abortController.abort();
    }

    // Pause camera video
    if (videoRef?.current) {
      videoRef.current.pause();
    }

    setMonitoring(false);
    setProcessing(false);
    setMonitoringMessage(
      "Monitoring request stopped"
    );
    setAbortController(null);
  };

  const highSeverityCount = incidents.filter(
    (incident) => incident.severity === "HIGH"
  ).length;

  const mediumSeverityCount = incidents.filter(
    (incident) => incident.severity === "MEDIUM"
  ).length;

  const getEvidenceFrameUrl = (incident) => {
    if (!incident?.evidence?.frame) {
      return null;
    }

    const filename =
      incident.evidence.frame.split("/").pop();

    return `${API_BASE_URL}/api/v1/modules/module_03/evidence/frames/${filename}`;
  };

  const getEvidenceClipUrl = (incident) => {
    if (!incident?.evidence?.clip) {
      return null;
    }

    const filename =
      incident.evidence.clip.split("/").pop();

    return `${API_BASE_URL}/api/v1/modules/module_03/evidence/clips/${filename}`;
  };

  const formatDate = (timestamp) => {
    if (!timestamp) {
      return "Unknown time";
    }

    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const navigateTo = (page) => {
    setActivePage(page);
  };

  /* =========================
     SIDEBAR
  ========================= */

  const Sidebar = () => (
    <aside className="sidebar">

      <div className="logo">
        <div className="logo-mark">N</div>

        <div>
          <h1>NEXORA</h1>
          <span>Intelligent Monitoring</span>
        </div>
      </div>

      <nav>

        <button
          className={`nav-item ${
            activePage === "dashboard"
              ? "active"
              : ""
          }`}
          onClick={() =>
            navigateTo("dashboard")
          }
        >
          <span>▣</span>
          Dashboard
        </button>

        <button
          className={`nav-item ${
            activePage === "cameras"
              ? "active"
              : ""
          }`}
          onClick={() =>
            navigateTo("cameras")
          }
        >
          <span>◉</span>
          Cameras
        </button>

        <button
          className={`nav-item ${
            activePage === "incidents"
              ? "active"
              : ""
          }`}
          onClick={() =>
            navigateTo("incidents")
          }
        >
          <span>⚠</span>
          Incidents
        </button>

        <button
          className={`nav-item ${
            activePage === "events"
              ? "active"
              : ""
          }`}
          onClick={() =>
            navigateTo("events")
          }
        >
          <span>◫</span>
          Events
        </button>

        <button
          className={`nav-item ${
            activePage === "settings"
              ? "active"
              : ""
          }`}
          onClick={() =>
            navigateTo("settings")
          }
        >
          <span>⚙</span>
          Settings
        </button>

      </nav>

      <div className="sidebar-bottom">

        <div className="system-status">

          <span
            className={
              backendStatus === "Online"
                ? "status-dot online"
                : "status-dot offline"
            }
          ></span>

          <div>
            <strong>Backend</strong>
            <small>{backendStatus}</small>
          </div>

        </div>

      </div>

    </aside>
  );

  /* =========================
     HEADER
  ========================= */

  const PageHeader = ({
    title,
    subtitle,
  }) => (
    <header className="header">

      <div>
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>

      {activePage === "dashboard" && (
        <button
          className="refresh-button"
          onClick={fetchIncidents}
        >
          ↻ Refresh
        </button>
      )}

    </header>
  );

  /* =========================
     DASHBOARD
  ========================= */

  const DashboardPage = () => (
    <>
      <PageHeader
        title="Security Dashboard"
        subtitle="Real-time intelligent monitoring overview"
      />

      <section className="stats-grid">

        <div className="stat-card">
          <div className="stat-icon">◉</div>

          <div>
            <span>Active Cameras</span>
            <strong>1</strong>
            <small>Monitoring</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon warning">
            ⚠
          </div>

          <div>
            <span>Total Incidents</span>
            <strong>{incidents.length}</strong>
            <small>Detected by M03</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon danger">
            !
          </div>

          <div>
            <span>High Severity</span>
            <strong>
              {highSeverityCount}
            </strong>
            <small>Requires attention</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon medium">
            ◈
          </div>

          <div>
            <span>Medium Severity</span>
            <strong>
              {mediumSeverityCount}
            </strong>
            <small>Under review</small>
          </div>
        </div>

      </section>

      <section className="module-section">

        <div className="section-header">

          <div>
            <span className="section-label">
              ACTIVE MODULE
            </span>

            <h3>
              Intrusion & Unauthorized Access
              Monitoring
            </h3>
          </div>

          <span className="module-status">
            ● READY
          </span>

        </div>

        <div className="module-info">

          <div className="module-item">
            <span>Module</span>
            <strong>M03</strong>
          </div>

          <div className="module-item">
            <span>Detection</span>
            <strong>YOLO11n</strong>
          </div>

          <div className="module-item">
            <span>Tracking</span>
            <strong>ByteTrack</strong>
          </div>

          <div className="module-item">
            <span>Review</span>
            <strong>
              Human-in-the-loop
            </strong>
          </div>

        </div>

      </section>

      <IncidentsList
        title="Recent Incidents"
        limit={5}
      />
    </>
  );

  /* =========================
     INCIDENT LIST
  ========================= */

  const IncidentsList = ({
    title = "Incidents",
    limit = null,
  }) => {

    const displayedIncidents = limit
      ? incidents.slice(0, limit)
      : incidents;

    return (
      <section className="incidents-section">

        <div className="section-header">

          <div>
            <span className="section-label">
              SECURITY EVENTS
            </span>

            <h3>{title}</h3>
          </div>

          <span className="incident-count">
            {incidents.length} incidents
          </span>

        </div>

        {loading ? (

          <div className="empty-state">
            <div className="loader"></div>
            <p>Loading incidents...</p>
          </div>

        ) : incidents.length === 0 ? (

          <div className="empty-state">

            <div className="empty-icon">
              ✓
            </div>

            <h4>
              No incidents detected
            </h4>

            <p>
              Run the M03 video processing
              pipeline to generate incidents.
            </p>

          </div>

        ) : (

          <div className="incident-list">

            {displayedIncidents.map(
              (incident, index) => (

                <div
                  className="incident-card"
                  key={
                    incident.incident_id ||
                    index
                  }
                >

                  <div className="incident-main">

                    <div className="incident-icon">
                      ⚠
                    </div>

                    <div className="incident-details">

                      <div className="incident-title-row">

                        <h4>
                          {incident.title ||
                            incident.event_type ||
                            "Security Event"}
                        </h4>

                        <span
                          className={`severity ${
                            incident.severity?.toLowerCase() ||
                            "medium"
                          }`}
                        >
                          {incident.severity ||
                            "UNKNOWN"}
                        </span>

                      </div>

                      <div className="incident-meta">

                        <span>
                          Camera:{" "}
                          {incident.camera_id ||
                            "CAM-01"}
                        </span>

                        <span>
                          Status:{" "}
                          {incident.status ||
                            "PENDING"}
                        </span>

                        {incident.zone_name && (
                          <span>
                            Zone:{" "}
                            {incident.zone_name}
                          </span>
                        )}

                        {incident.confidence !==
                          undefined && (
                          <span>
                            Confidence:{" "}
                            {(
                              incident.confidence *
                              100
                            ).toFixed(1)}
                            %
                          </span>
                        )}

                      </div>

                    </div>

                  </div>

                  <div className="incident-right">

                    <span className="pending">
                      {incident.status ||
                        "PENDING"}
                    </span>

                    <small>
                      {formatDate(
                        incident.timestamp ||
                          incident.created_at
                      )}
                    </small>

                    <button
                      className="evidence-button"
                      onClick={() =>
                        setSelectedIncident(
                          incident
                        )
                      }
                    >
                      View Evidence
                    </button>

                  </div>

                </div>

              )
            )}

          </div>

        )}

      </section>
    );
  };

/* =========================
   CAMERAS PAGE
========================= */

const CamerasPage = () => {
  const videoRef = useRef(null);

  useEffect(() => {
    if (!monitoring || !videoRef.current) {
      return;
    }

    videoRef.current.currentTime = 0;

    videoRef.current
      .play()
      .catch((error) => {
        console.error(
          "Video playback failed:",
          error
        );
      });
  }, [monitoring]);

  return (
    <>
      <PageHeader
        title="Cameras"
        subtitle="Connected monitoring cameras"
      />

      <section className="page-card">

        <div className="camera-card">

          <div className="camera-preview">

            <video
              ref={videoRef}
              className="camera-video"
              src={`${API_BASE_URL}/api/v1/modules/module_03/annotated-video`}
              muted
              loop
              playsInline
              preload = "auto"
            />

            <span
              className={`live-badge ${
                monitoring
                  ? "monitoring-badge"
                  : ""
              }`}
            >
              ●{" "}
              {monitoring
                ? "MONITORING"
                : "READY"}
            </span>

          </div>

          <div className="camera-info">

            <div>
              <span>Camera ID</span>
              <strong>CAM-01</strong>
            </div>

            <div>
              <span>Source</span>
              <strong>M03 Test Video</strong>
            </div>

            <div>
              <span>Detection</span>
              <strong>YOLO11n</strong>
            </div>

            <div>
              <span>Tracking</span>
              <strong>ByteTrack</strong>
            </div>

          </div>

          <div className="camera-control">

            <div className="camera-status-row">

              <span
                className={
                  monitoring
                    ? "camera-online"
                    : "camera-ready"
                }
              >
                ●{" "}
                {monitoring
                  ? "M03 monitoring in progress"
                  : "Camera ready"}
              </span>

              <span>
                {incidents.length} incidents
              </span>

            </div>

            <div className="camera-message">
              {monitoringMessage}
            </div>

            <div className="camera-buttons">

              {!monitoring ? (

                <button
                  className="start-monitoring-button"
                  onClick={() => startMonitoring(videoRef)}
                  disabled={processing}
                >
                  ▶ Start Monitoring
                </button>

              ) : (

                <button
                  className="stop-monitoring-button"
                  onClick={() => stopMonitoring(videoRef)}
                >
                  ■ Stop Monitoring
                </button>

              )}

              <button
                className="camera-refresh-button"
                onClick={fetchIncidents}
                disabled={processing}
              >
                ↻ Refresh Results
              </button>

            </div>

            {processing && (
              <div className="processing-bar">

                <div className="processing-spinner"></div>

                <span>
                  YOLO11n + ByteTrack are processing
                  the video...
                </span>

              </div>
            )}

          </div>

        </div>

      </section>
    </>
  );
};
  /* =========================
     INCIDENTS PAGE
  ========================= */

  const IncidentsPage = () => (
    <>
      <PageHeader
        title="Incidents"
        subtitle="Review detected security incidents"
      />

      <IncidentsList title="All Incidents" />
    </>
  );

  /* =========================
     EVENTS PAGE
  ========================= */

  const EventsPage = () => (
    <>
      <PageHeader
        title="Events"
        subtitle="Security events generated by Module 03"
      />

      <section className="page-card">

        {incidents.length === 0 ? (

          <div className="empty-state">
            <div className="empty-icon">
              ◫
            </div>

            <h4>
              No events available
            </h4>

            <p>
              Process a video using Module 03
              to generate security events.
            </p>
          </div>

        ) : (

          <div className="event-list">

            {incidents.map(
              (incident, index) => (

                <div
                  className="event-row"
                  key={
                    incident.incident_id ||
                    index
                  }
                >

                  <div className="event-icon">
                    ◫
                  </div>

                  <div className="event-info">

                    <strong>
                      {incident.event_type ||
                        "Security Event"}
                    </strong>

                    <span>
                      Camera:{" "}
                      {incident.camera_id ||
                        "CAM-01"}
                    </span>

                  </div>

                  <div className="event-meta">

                    <span
                      className={`severity ${
                        incident.severity?.toLowerCase() ||
                        "medium"
                      }`}
                    >
                      {incident.severity ||
                        "UNKNOWN"}
                    </span>

                    <small>
                      {formatDate(
                        incident.timestamp ||
                          incident.created_at
                      )}
                    </small>

                  </div>

                </div>

              )
            )}

          </div>

        )}

      </section>
    </>
  );

  /* =========================
     SETTINGS PAGE
  ========================= */

  const SettingsPage = () => (
    <>
      <PageHeader
        title="Settings"
        subtitle="NEXORA system and module configuration"
      />

      <section className="settings-grid">

        <div className="settings-card">

          <span className="section-label">
            SYSTEM
          </span>

          <h3>Backend Connection</h3>

          <div className="setting-row">
            <span>API Status</span>

            <strong
              className={
                backendStatus === "Online"
                  ? "setting-online"
                  : "setting-offline"
              }
            >
              ● {backendStatus}
            </strong>
          </div>

          <div className="setting-row">
            <span>API URL</span>
            <strong>
              {API_BASE_URL}
            </strong>
          </div>

        </div>

        <div className="settings-card">

          <span className="section-label">
            MODULE 03
          </span>

          <h3>
            Intrusion Monitoring
          </h3>

          <div className="setting-row">
            <span>Detection Model</span>
            <strong>YOLO11n</strong>
          </div>

          <div className="setting-row">
            <span>Tracker</span>
            <strong>ByteTrack</strong>
          </div>

          <div className="setting-row">
            <span>Review Mode</span>
            <strong>
              Human-in-the-loop
            </strong>
          </div>

          <div className="setting-row">
            <span>Incident Status</span>
            <strong>PENDING</strong>
          </div>

        </div>

      </section>
    </>
  );

  /* =========================
     PAGE SELECTOR
  ========================= */

  const renderPage = () => {

    switch (activePage) {

      case "cameras":
        return <CamerasPage />;

      case "incidents":
        return <IncidentsPage />;

      case "events":
        return <EventsPage />;

      case "settings":
        return <SettingsPage />;

      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="app">

      <Sidebar />

      <main className="main">

        {renderPage()}

        <footer>

          <span>
            NEXORA v1.0.0
          </span>

          <span>
            Module 03 • Intrusion Monitoring
          </span>

        </footer>

      </main>

      {/* =========================
          EVIDENCE MODAL
      ========================= */}

      {selectedIncident && (

        <div
          className="modal-overlay"
          onClick={() =>
            setSelectedIncident(null)
          }
        >

          <div
            className="evidence-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <div className="modal-header">

              <div>

                <span className="section-label">
                  INCIDENT EVIDENCE
                </span>

                <h3>
                  {selectedIncident.title ||
                    selectedIncident.event_type ||
                    "Security Incident"}
                </h3>

              </div>

              <button
                className="modal-close"
                onClick={() =>
                  setSelectedIncident(null)
                }
              >
                ×
              </button>

            </div>

            <div className="evidence-content">

              <div className="evidence-image-container">

                {getEvidenceFrameUrl(
                  selectedIncident
                ) ? (

                  <img
                    src={getEvidenceFrameUrl(
                      selectedIncident
                    )}
                    alt="Incident evidence"
                    className="evidence-image"
                  />

                ) : (

                  <div className="evidence-placeholder">
                    No evidence frame available
                  </div>

                )}

              </div>

              <div className="evidence-details">

                <div className="detail-row">
                  <span>Incident ID</span>

                  <strong>
                    {selectedIncident.incident_id}
                  </strong>
                </div>

                <div className="detail-row">
                  <span>Event Type</span>

                  <strong>
                    {selectedIncident.event_type}
                  </strong>
                </div>

                <div className="detail-row">
                  <span>Severity</span>

                  <strong
                    className={`severity-text ${
                      selectedIncident.severity?.toLowerCase()
                    }`}
                  >
                    {selectedIncident.severity}
                  </strong>
                </div>

                <div className="detail-row">
                  <span>Camera</span>

                  <strong>
                    {selectedIncident.camera_id}
                  </strong>
                </div>

                <div className="detail-row">
                  <span>Zone</span>

                  <strong>
                    {selectedIncident.zone_name ||
                      "N/A"}
                  </strong>
                </div>

                <div className="detail-row">
                  <span>Track ID</span>

                  <strong>
                    {selectedIncident.track_id ??
                      "N/A"}
                  </strong>
                </div>

                <div className="detail-row">
                  <span>Confidence</span>

                  <strong>
                    {selectedIncident.confidence !==
                    undefined
                      ? `${(
                          selectedIncident.confidence *
                          100
                        ).toFixed(2)}%`
                      : "N/A"}
                  </strong>
                </div>

                <div className="detail-row">
                  <span>Status</span>

                  <strong>
                    {selectedIncident.status ||
                      "PENDING"}
                  </strong>
                </div>

                {selectedIncident.direction && (
                  <div className="detail-row">

                    <span>Direction</span>

                    <strong>
                      {selectedIncident.direction}
                    </strong>

                  </div>
                )}

                <div className="detail-row">

                  <span>Detected At</span>

                  <strong>
                    {formatDate(
                      selectedIncident.timestamp
                    )}
                  </strong>

                </div>

                {getEvidenceClipUrl(
                  selectedIncident
                ) && (

                  <a
                    className="clip-button"
                    href={getEvidenceClipUrl(
                      selectedIncident
                    )}
                    target="_blank"
                    rel="noreferrer"
                  >
                    ▶ Open Evidence Clip
                  </a>

                )}

              </div>

            </div>

            <div className="modal-footer">

              <span>
                Human review required
              </span>

              <button
                onClick={() =>
                  setSelectedIncident(null)
                }
              >
                Close
              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}

export default App;