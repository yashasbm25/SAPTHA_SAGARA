
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import MarineMap from "./MarineMap.jsx";
import {
  Anchor,
  Activity,
  ArrowRight,
  Bot,
  CheckCircle2,
  ChevronRight,
  Compass,
  LoaderCircle,
  MapPin,
  Navigation,
  RefreshCw,
  Route,
  Send,
  ShieldAlert,
  Waves,
  Wind,
  CloudSun,
  Gauge,
  Clock3,
  AlertTriangle,
  Menu,
  X,
} from "lucide-react";

const API = "";

function formatValue(value, unit = "") {
  if (value === undefined || value === null || value === "") return "—";

  const number = Number(value);

  return Number.isFinite(number)
    ? `${number.toLocaleString("en-IN", {
        maximumFractionDigits: 2,
      })}${unit}`
    : `${value}${unit}`;
}

function formatTimestamp(value) {
  if (!value) return "Awaiting query";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

/**
 * Clean Markdown returned by the AI.
 * Handles escaped headings/bold markers and removes the
 * accidental "svgResponse received" text if it appears in the report.
 */
function cleanReportMarkdown(value) {
  if (typeof value !== "string" || !value.trim()) {
    return "The API returned data without a summary.";
  }

  return value
    .replace(/\\([#*_])/g, "$1")
    .replace(/svgResponse received/gi, "")
    .trim();
}

/**
 * Render the AI report as formatted Markdown instead of raw text.
 */
function MarineReport({ summary }) {
  const markdown = cleanReportMarkdown(summary);

  return (
    <div className="summary-text">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h2 className="report-title">{children}</h2>
          ),
          h2: ({ children }) => (
            <h3 className="report-heading">{children}</h3>
          ),
          h3: ({ children }) => (
            <h4 className="report-subheading">{children}</h4>
          ),
          h4: ({ children }) => (
            <h4 className="report-subheading">{children}</h4>
          ),
          p: ({ children }) => (
            <p className="report-paragraph">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="report-list">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="report-list">{children}</ol>
          ),
          li: ({ children }) => <li>{children}</li>,
          strong: ({ children }) => <strong>{children}</strong>,
          blockquote: ({ children }) => (
            <blockquote className="report-blockquote">
              {children}
            </blockquote>
          ),
          a: ({ children, href }) => (
            <a href={href} target="_blank" rel="noreferrer">
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="report-table-wrap">
              <table className="report-table">{children}</table>
            </div>
          ),
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, unit = "", note }) {
  return (
    <article className="metric-card">
      <div className="metric-top">
        <span className="metric-icon">
          <Icon size={19} />
        </span>
        <span className="metric-label">{label}</span>
      </div>

      <div className="metric-value">
        {value}
        <span>{unit}</span>
      </div>

      <p className="metric-note">{note}</p>
    </article>
  );
}

function App() {
  const [apiStatus, setApiStatus] = useState("checking");

  const [query, setQuery] = useState(
    "Check current marine conditions near Mangalore, including weather, wind, waves, and fishing advisories."
  );

  const [marineResult, setMarineResult] = useState(null);
  const [marineLoading, setMarineLoading] = useState(false);
  const [marineError, setMarineError] = useState("");

  const [origin, setOrigin] = useState("Mangalore");
  const [destination, setDestination] = useState("Goa");
  const [routeResult, setRouteResult] = useState(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  async function checkBackend() {
    setApiStatus("checking");

    try {
      const response = await fetch(`${API}/health`);

      if (!response.ok) {
        throw new Error("Backend health check failed");
      }

      setApiStatus("online");
    } catch {
      setApiStatus("offline");
    }
  }

  useEffect(() => {
    checkBackend();
  }, []);

  async function submitMarineQuery(event) {
    event.preventDefault();

    if (query.trim().length < 2) {
      setMarineError("Enter a marine query first.");
      return;
    }

    setMarineLoading(true);
    setMarineError("");
    setMarineResult(null);

    try {
      const response = await fetch(`${API}/api/marine/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query.trim(),
        }),
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(
          payload.detail ||
            payload.error ||
            "Marine query failed."
        );
      }

      if (
        payload.success === false ||
        payload.data?.success === false
      ) {
        throw new Error(
          payload.data?.error ||
            payload.error ||
            "The query could not be completed."
        );
      }

      setMarineResult(payload.data ?? payload);
    } catch (error) {
      setMarineError(
        `${error.message} Check that the backend is running on port 8000.`
      );
    } finally {
      setMarineLoading(false);
    }
  }

  async function submitRoute(event) {
    event.preventDefault();

    if (!origin.trim() || !destination.trim()) {
      setRouteError("Enter both an origin and a destination.");
      return;
    }

    setRouteLoading(true);
    setRouteError("");
    setRouteResult(null);

    try {
      const response = await fetch(`${API}/api/route/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          origin: origin.trim(),
          destination: destination.trim(),
        }),
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(
          payload.detail ||
            payload.error ||
            "Route planning failed."
        );
      }

      if (
        payload.success === false ||
        payload.data?.success === false
      ) {
        throw new Error(
          payload.data?.error ||
            payload.error ||
            "The route could not be planned."
        );
      }

      setRouteResult(payload.data ?? payload);
    } catch (error) {
      setRouteError(
        `${error.message} Check that the backend is running on port 8000.`
      );
    } finally {
      setRouteLoading(false);
    }
  }

  const weather = marineResult?.weather;
  const weatherCurrent = weather?.current ?? {};
  const weatherUnits = weather?.units ?? {};

  const marine = marineResult?.marine_conditions;
  const marineCurrent = marine?.current ?? {};
  const marineUnits = marine?.units ?? {};

  const location = marineResult?.location;

  const routeDistance = routeResult?.straight_line_distance_km;
  const routeSeaDistance = routeResult?.route_distance_km;
  const routePoints = routeResult?.waypoints ?? [];

  function scrollTo(id) {
    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });

    setMobileMenuOpen(false);
  }

  return (
    <div className="app-shell">
      <aside
        className={`sidebar ${
          mobileMenuOpen ? "sidebar-open" : ""
        }`}
      >
        <div className="brand">
          <div className="brand-mark">
            <Waves size={27} />
          </div>

          <div>
            <div className="brand-name">SAPTHA SAGARA</div>
            <div className="brand-subtitle">
              MARINE INTELLIGENCE
            </div>
          </div>

          <button
            className="mobile-close icon-button"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <div className="nav-section-label">WORKSPACE</div>

        <nav className="sidebar-nav">
          <button
            className="nav-item active"
            onClick={() => scrollTo("overview")}
          >
            <Activity size={18} /> Overview
          </button>

          <button
            className="nav-item"
            onClick={() => scrollTo("intelligence")}
          >
            <Bot size={18} /> Marine intelligence
          </button>

          <button
            className="nav-item"
            onClick={() => scrollTo("route-planner")}
          >
            <Route size={18} /> Route planner
          </button>

          <button
            className="nav-item"
            onClick={() => scrollTo("marine-map-section")}
          >
            <MapPin size={18} /> Marine map
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <div className="connection-heading">
              <span className={`status-dot ${apiStatus}`} />
              <span>Backend connection</span>
            </div>

            <p>
              {apiStatus === "online"
                ? "API responding"
                : apiStatus === "checking"
                  ? "Checking API..."
                  : "API unavailable"}
            </p>

            <button
              className="connection-refresh"
              onClick={checkBackend}
            >
              <RefreshCw size={13} /> Check connection
            </button>
          </div>

          <div className="sidebar-footer">
            <Anchor size={14} /> Built for smarter marine decisions
          </div>
        </div>
      </aside>

      {mobileMenuOpen && (
        <button
          className="mobile-overlay"
          onClick={() => setMobileMenuOpen(false)}
          aria-label="Close navigation"
        />
      )}

      <main className="main-content">
        <header className="topbar">
          <button
            className="mobile-menu icon-button"
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={22} />
          </button>

          <div className="breadcrumb">
            <span>Workspace</span>
            <ChevronRight size={15} />
            <strong>Overview</strong>
          </div>

          <div className="topbar-right">
            <span className="environment-tag">DEVELOPMENT</span>

            <span className={`top-status ${apiStatus}`}>
              <span className={`status-dot ${apiStatus}`} />

              {apiStatus === "online"
                ? "System online"
                : apiStatus === "checking"
                  ? "Connecting"
                  : "Offline"}
            </span>
          </div>
        </header>

        <div className="page-content" id="overview">
          <section className="welcome-row">
            <div>
              <div className="eyebrow">
                <span /> MARITIME SITUATIONAL AWARENESS
              </div>

              <h1>
                Marine intelligence,
                <br />
                <span>at a glance.</span>
              </h1>

              <p className="welcome-description">
                Explore marine conditions, query your AI assistant,
                and evaluate geographic routes from one workspace.
              </p>
            </div>

            <div className="welcome-art" aria-hidden="true">
              <div className="orbit orbit-one" />
              <div className="orbit orbit-two" />
              <div className="globe">
                <Waves size={57} strokeWidth={1.1} />
              </div>
              <span className="orbit-dot dot-one" />
              <span className="orbit-dot dot-two" />
              <span className="orbit-dot dot-three" />
            </div>
          </section>

          <section className="section-block">
            <div className="section-heading">
              <div>
                <div className="section-kicker">CONDITIONS</div>
                <h2>Marine snapshot</h2>
              </div>

              <span className="data-chip">
                <Clock3 size={14} />
                {formatTimestamp(marineResult?.generated_at)}
              </span>
            </div>

            <div className="metrics-grid">
              <MetricCard
                icon={CloudSun}
                label="Air temperature"
                value={formatValue(weatherCurrent.temperature_2m)}
                unit={
                  weatherCurrent.temperature_2m != null
                    ? ` ${weatherUnits.temperature_2m ?? "°C"}`
                    : ""
                }
                note={
                  weather?.available
                    ? "Weather feed available"
                    : "Run a query to load"
                }
              />

              <MetricCard
                icon={Wind}
                label="Wind speed"
                value={formatValue(weatherCurrent.wind_speed_10m)}
                unit={
                  weatherCurrent.wind_speed_10m != null
                    ? ` ${weatherUnits.wind_speed_10m ?? "km/h"}`
                    : ""
                }
                note={
                  weatherCurrent.wind_direction_10m != null
                    ? `Direction: ${weatherCurrent.wind_direction_10m}°`
                    : "Wind direction unavailable"
                }
              />

              <MetricCard
                icon={Waves}
                label="Wave height"
                value={formatValue(marineCurrent.wave_height)}
                unit={
                  marineCurrent.wave_height != null
                    ? ` ${marineUnits.wave_height ?? "m"}`
                    : ""
                }
                note={
                  marine?.available
                    ? "Marine feed available"
                    : "Run a query to load"
                }
              />

              <MetricCard
                icon={Gauge}
                label="Wind gusts"
                value={formatValue(weatherCurrent.wind_gusts_10m)}
                unit={
                  weatherCurrent.wind_gusts_10m != null
                    ? ` ${weatherUnits.wind_gusts_10m ?? "km/h"}`
                    : ""
                }
                note={
                  marineCurrent.wave_period != null
                    ? `Wave period: ${marineCurrent.wave_period} ${
                        marineUnits.wave_period ?? "s"
                      }`
                    : "Wave period unavailable"
                }
              />
            </div>

            {location && (
              <div className="location-line">
                <MapPin size={15} />
                <span>Showing results for</span>
                <strong>{location.name}</strong>
              </div>
            )}
          </section>

          <section className="section-block" id="intelligence">
            <div className="section-heading">
              <div>
                <div className="section-kicker">AI ASSISTANT</div>
                <h2>Ask the ocean</h2>

                <p className="section-description">
                  Ask a marine question and retrieve available weather
                  and wave data.
                </p>
              </div>

              <div className="ai-badge">
                <Bot size={16} /> Marine AI
              </div>
            </div>

            <div className="query-layout">
              <form
                className="query-card"
                onSubmit={submitMarineQuery}
              >
                <label htmlFor="marine-query">
                  What would you like to know?
                </label>

                <textarea
                  id="marine-query"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Ask about marine weather, wind, waves or coastal conditions..."
                  rows={4}
                />

                <div className="query-footer">
                  <span>
                    Use a location in your question for better results.
                  </span>

                  <button
                    className="primary-button"
                    type="submit"
                    disabled={marineLoading}
                  >
                    {marineLoading ? (
                      <>
                        <LoaderCircle className="spin" size={17} />
                        Analyzing
                      </>
                    ) : (
                      <>
                        <Send size={16} />
                        Analyze query
                      </>
                    )}
                  </button>
                </div>

                <div className="suggestion-row">
                  <span>Try:</span>

                  <button
                    type="button"
                    onClick={() =>
                      setQuery(
                        "Check wind and wave conditions near Mangalore."
                      )
                    }
                  >
                    Wind &amp; waves
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      setQuery(
                        "What marine conditions should I review before a fishing trip near Karwar?"
                      )
                    }
                  >
                    Fishing conditions
                  </button>
                </div>
              </form>

              <aside className="assistant-card">
                <div className="assistant-orb">
                  <Waves size={27} />
                </div>

                <h3>Your marine co-pilot</h3>

                <p>
                  Submit a question to combine retrieved data with an
                  AI-generated explanation when the AI service is available.
                </p>

                <div className="assistant-feature">
                  <CheckCircle2 size={16} /> Evidence-aware responses
                </div>

                <div className="assistant-feature">
                  <CheckCircle2 size={16} /> Weather and marine data
                </div>

                <div className="assistant-feature">
                  <ShieldAlert size={16} /> Safety limitations disclosed
                </div>
              </aside>
            </div>

            {marineError && (
              <div className="error-panel">
                <AlertTriangle size={19} />
                <div>
                  <strong>Marine query failed</strong>
                  <p>{marineError}</p>
                </div>
              </div>
            )}

            {marineResult && (
              <div className="result-card">
                <div className="result-header">
                  <div>
                    <div className="section-kicker">QUERY RESULT</div>
                    <h3>Marine intelligence report</h3>
                  </div>

                  <span className="success-tag">
                    <CheckCircle2 size={14} /> Response received
                  </span>
                </div>

                <MarineReport summary={marineResult.summary} />

                <div className="source-grid">
                  <div className="source-item">
                    <span
                      className={`status-dot ${
                        weather?.available ? "online" : "offline"
                      }`}
                    />

                    <div>
                      <strong>Weather</strong>
                      <small>
                        {weather?.source || "Source not reported"}
                      </small>
                    </div>

                    <span className="source-state">
                      {weather?.available ? "Available" : "Unavailable"}
                    </span>
                  </div>

                  <div className="source-item">
                    <span
                      className={`status-dot ${
                        marine?.available ? "online" : "offline"
                      }`}
                    />

                    <div>
                      <strong>Marine</strong>
                      <small>
                        {marine?.source || "Source not reported"}
                      </small>
                    </div>

                    <span className="source-state">
                      {marine?.available ? "Available" : "Unavailable"}
                    </span>
                  </div>
                </div>

                {Array.isArray(marineResult.limitations) &&
                  marineResult.limitations.length > 0 && (
                    <div className="limitations-box">
                      <strong>
                        <ShieldAlert size={16} /> Important limitations
                      </strong>

                      <ul>
                        {marineResult.limitations.map((item, index) => (
                          <li key={index}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
              </div>
            )}
          </section>

          <section className="section-block" id="route-planner">
            <div className="section-heading">
              <div>
                <div className="section-kicker">GEOGRAPHIC ANALYSIS</div>
                <h2>Route planner</h2>

                <p className="section-description">
                  Compare straight-line distance with the generated
                  sea-route visualization.
                </p>
              </div>

              <div className="route-badge">
                <Navigation size={16} /> Route tools
              </div>
            </div>

            <form className="route-form" onSubmit={submitRoute}>
              <div className="route-input-group">
                <label htmlFor="origin">Origin</label>

                <div className="input-with-icon">
                  <MapPin size={17} />

                  <input
                    id="origin"
                    value={origin}
                    onChange={(event) => setOrigin(event.target.value)}
                    placeholder="e.g. Mangalore"
                    required
                  />
                </div>
              </div>

              <div className="route-arrow">
                <ArrowRight size={20} />
              </div>

              <div className="route-input-group">
                <label htmlFor="destination">Destination</label>

                <div className="input-with-icon">
                  <Navigation size={17} />

                  <input
                    id="destination"
                    value={destination}
                    onChange={(event) =>
                      setDestination(event.target.value)
                    }
                    placeholder="e.g. Goa"
                    required
                  />
                </div>
              </div>

              <button
                className="primary-button route-submit"
                type="submit"
                disabled={routeLoading}
              >
                {routeLoading ? (
                  <>
                    <LoaderCircle className="spin" size={17} />
                    Planning
                  </>
                ) : (
                  <>
                    <Compass size={17} />
                    Plan route
                  </>
                )}
              </button>
            </form>

            {routeError && (
              <div className="error-panel">
                <AlertTriangle size={19} />
                <div>
                  <strong>Route planning failed</strong>
                  <p>{routeError}</p>
                </div>
              </div>
            )}

            {routeResult && (
              <div className="route-result">
                <div className="route-result-top">
                  <div>
                    <span className="section-kicker">ROUTE ESTIMATE</span>

                    <h3>
                      {origin} <ArrowRight size={18} /> {destination}
                    </h3>
                  </div>

                  <div className="distance-box">
                    <span>STRAIGHT-LINE DISTANCE</span>
                    <strong>{formatValue(routeDistance, " km")}</strong>
                  </div>
                </div>

                {routeSeaDistance != null && (
                  <div className="distance-box">
                    <span>SEA-ROUTE VISUALIZATION ESTIMATE</span>
                    <strong>
                      {formatValue(routeSeaDistance, " km")}
                    </strong>
                  </div>
                )}

                <div className="route-endpoints">
                  <div className="endpoint">
                    <span className="endpoint-dot start-dot" />

                    <div>
                      <small>ORIGIN</small>
                      <strong>
                        {routeResult.origin?.name || origin}
                      </strong>

                      <span>
                        {routeResult.origin?.latitude},{" "}
                        {routeResult.origin?.longitude}
                      </span>
                    </div>
                  </div>

                  <div className="endpoint-connector" />

                  <div className="endpoint">
                    <span className="endpoint-dot end-dot" />

                    <div>
                      <small>DESTINATION</small>
                      <strong>
                        {routeResult.destination?.name || destination}
                      </strong>

                      <span>
                        {routeResult.destination?.latitude},{" "}
                        {routeResult.destination?.longitude}
                      </span>
                    </div>
                  </div>
                </div>

                {routePoints.length > 0 && (
                  <details className="waypoints-details">
                    <summary>
                      View {routePoints.length} generated waypoints
                      <ChevronRight size={16} />
                    </summary>

                    <div className="waypoint-table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>#</th>
                            <th>Latitude</th>
                            <th>Longitude</th>
                          </tr>
                        </thead>

                        <tbody>
                          {routePoints.map((point, index) => (
                            <tr key={point.sequence ?? index}>
                              <td>{point.sequence ?? index + 1}</td>
                              <td>{point.latitude}</td>
                              <td>{point.longitude}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                )}

                <div className="route-warning">
                  <AlertTriangle size={18} />

                  <div>
                    <strong>Not for operational navigation</strong>

                    <p>
                      {routeResult.route_type ||
                        "Geographic route estimate"}
                      . The route is not certified for navigation and is
                      not verified against official nautical charts, depth,
                      shipping restrictions, currents, or current marine
                      warnings. Do not use it to navigate a vessel.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </section>

          <section
            className="section-block"
            id="marine-map-section"
          >
            <div className="section-heading">
              <div>
                <div className="section-kicker">LIVE GEOGRAPHIC VIEW</div>
                <h2>Marine operations map</h2>

                <p className="section-description">
                  Explore coastal locations and view the generated route estimate.
                </p>
              </div>
            </div>

            <MarineMap
              origin={origin}
              destination={destination}
              routeData={routeResult}
              onOriginChange={setOrigin}
              onDestinationChange={setDestination}
              onPlanRoute={submitRoute}
              routeLoading={routeLoading}
              routeError={routeError}
            />
          </section>

          <footer className="page-footer">
            <div className="footer-brand">
              <Waves size={17} /> SAPTHA SAGARA
            </div>

            <span>
              Marine intelligence prototype · Verify safety information
              with official authorities.
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}

export default App;
