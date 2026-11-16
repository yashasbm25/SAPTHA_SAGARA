import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  Circle,
  CircleMarker,
  Polygon,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./MarineMap.css";

const DEFAULT_POINTS = {
  kandla: [23.002, 70.218],
  mundra: [22.738, 69.708],
  okha: [22.469, 69.072],
  dwarka: [22.244, 68.958],
  porbandar: [21.64, 69.596],
  veraval: [20.901, 70.371],
  diu: [20.715, 70.875],
  surat: [21.092, 72.625],
  dahanu: [19.968, 72.715],
  mumbai: [18.912, 72.826],
  alibag: [18.641, 72.868],
  ratnagiri: [17.001, 73.278],
  malvan: [16.059, 73.458],
  panaji: [15.4989, 73.818],
  goa: [15.4089, 73.7939],
  mormugao: [15.4089, 73.7939],
  karwar: [14.805, 74.114],
  gokarna: [14.518, 74.354],
  kumta: [14.518, 74.354],
  honnavar: [14.272, 74.426],
  bhatkal: [13.968, 74.525],
  kundapura: [13.635, 74.662],
  udupi: [13.348, 74.696],
  malpe: [13.348, 74.696],
  mangalore: [12.853, 74.8315],
  mangaluru: [12.853, 74.8315],
  kasaragod: [12.488, 74.978],
  kannur: [11.855, 75.374],
  thalassery: [11.748, 75.489],
  kozhikode: [11.166, 75.802],
  calicut: [11.166, 75.802],
  beypore: [11.166, 75.802],
  ponnani: [10.785, 75.915],
  kochi: [9.936, 76.258],
  cochin: [9.936, 76.258],
  alappuzha: [9.492, 76.318],
  kollam: [8.8785, 76.556],
  thiruvananthapuram: [8.378, 76.988],
  vizhinjam: [8.378, 76.988],
  colachel: [8.172, 77.252],
  kanyakumari: [8.095, 77.561],
  tuticorin: [8.794, 78.161],
  rameswaram: [9.282, 79.315],
  nagapattinam: [10.761, 79.849],
  karaikal: [10.915, 79.852],
  cuddalore: [11.715, 79.774],
  puducherry: [11.908, 79.829],
  chennai: [13.128, 80.298],
  krishnapatnam: [14.254, 80.128],
  machilipatnam: [16.152, 81.189],
  kakinada: [16.982, 82.281],
  visakhapatnam: [17.696, 83.301],
  vizag: [17.696, 83.301],
  gopalpur: [19.302, 84.965],
  puri: [19.798, 85.842],
  paradip: [20.265, 86.671],
  dhamra: [20.792, 86.965],
  digha: [21.635, 87.568],
  haldia: [21.795, 87.882],
  kavaratti: [10.566, 72.641],
  "port blair": [11.668, 92.736],
};

const PORT_SUGGESTIONS = [
  "Kandla", "Mundra", "Okha", "Dwarka", "Porbandar", "Veraval", "Diu",
  "Dahanu", "Mumbai", "Alibag", "Ratnagiri", "Malvan", "Panaji", "Goa",
  "Mormugao", "Karwar", "Gokarna", "Kumta", "Honnavar", "Bhatkal",
  "Kundapura", "Udupi", "Malpe", "Mangalore", "Kasaragod", "Kannur",
  "Thalassery", "Kozhikode", "Beypore", "Ponnani", "Kochi", "Alappuzha",
  "Kollam", "Vizhinjam", "Thiruvananthapuram", "Colachel", "Kanyakumari",
  "Tuticorin", "Rameswaram", "Nagapattinam", "Karaikal", "Cuddalore",
  "Puducherry", "Chennai", "Krishnapatnam", "Machilipatnam", "Kakinada",
  "Visakhapatnam", "Gopalpur", "Puri", "Paradip", "Dhamra", "Digha",
  "Haldia", "Kavaratti", "Port Blair"
];

const RESTRICTED_ZONES = [
  {
    name: "Demo Restricted Marine Zone",
    type: "Restricted Area",
    positions: [
      [11.95, 74.45],
      [11.95, 74.55],
      [12.05, 74.55],
      [12.05, 74.45],
    ],
  },
];

function parseCoordinateString(value) {
  if (!value || typeof value !== "string") return null;
  const match = value
    .trim()
    .match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);
  if (!match) return null;
  const lat = Number(match[1]);
  const lon = Number(match[2]);
  return Number.isFinite(lat) && Number.isFinite(lon) ? [lat, lon] : null;
}

function resolveEndpoint(inputText, routeEndpointObj, fallback) {
  const parsedCoord = parseCoordinateString(inputText);
  if (parsedCoord) return parsedCoord;

  const key = String(inputText || "")
    .toLowerCase()
    .split(",")[0]
    .trim();

  if (
    routeEndpointObj?.latitude != null &&
    routeEndpointObj?.longitude != null &&
    String(routeEndpointObj.name || "")
      .toLowerCase()
      .includes(key)
  ) {
    return [
      Number(routeEndpointObj.latitude),
      Number(routeEndpointObj.longitude),
    ];
  }

  if (DEFAULT_POINTS[key]) {
    return DEFAULT_POINTS[key];
  }

  if (
    routeEndpointObj?.latitude != null &&
    routeEndpointObj?.longitude != null
  ) {
    return [
      Number(routeEndpointObj.latitude),
      Number(routeEndpointObj.longitude),
    ];
  }

  return fallback;
}

function createIcon(color) {
  return L.divIcon({
    className: "marine-map-marker",
    html: `<div style="
      width: 14px;
      height: 14px;
      background: ${color};
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 0 8px rgba(0,0,0,0.45);
    "></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

const originIcon = createIcon("#16a878");
const destinationIcon = createIcon("#ef8354");
const queryPinIcon = createIcon("#f4b942");

function formatValue(value, suffix = "") {
  if (value === null || value === undefined || value === "") {
    return "Unavailable";
  }
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "Unavailable";
  }
  return `${number.toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  })}${suffix}`;
}

function MapBounds({ boundsKey, points }) {
  const map = useMap();

  useEffect(() => {
    if (!points || !points.length) return;
    const bounds = L.latLngBounds(points);
    if (bounds.isValid()) {
      map.fitBounds(bounds, {
        padding: [45, 45],
        maxZoom: 8,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, boundsKey]);

  return null;
}

function MapClickSelector({ clickMode, onMapPointPicked }) {
  const map = useMap();

  useEffect(() => {
    const container = map.getContainer();
    container.style.cursor = clickMode ? "crosshair" : "";
    return () => {
      container.style.cursor = "";
    };
  }, [map, clickMode]);

  useMapEvents({
    click(e) {
      if (!clickMode) return;
      const coordString = `${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`;
      onMapPointPicked(clickMode, coordString);
    },
  });

  return null;
}

export default function MarineMap({
  origin = "Mangalore",
  destination = "Goa",
  routeData = null,
  pfzData = null,
  locationData = null,
  advisoryData = null,
  onOriginChange,
  onDestinationChange,
  onPlanRoute,
  routeLoading = false,
  routeError = "",
}) {
  // "route" = only PFZs along the active route | "all" = all live PFZs across India | "none" = hidden
  const [pfzDisplayMode, setPfzDisplayMode] = useState("route");
  const [showRestricted, setShowRestricted] = useState(true);
  const [clickMode, setClickMode] = useState("");

  const originPoint = resolveEndpoint(
    origin,
    routeData?.origin,
    DEFAULT_POINTS.mangalore
  );
  const destinationPoint = resolveEndpoint(
    destination,
    routeData?.destination,
    DEFAULT_POINTS.goa
  );

  const waypointPoints = Array.isArray(routeData?.waypoints)
    ? routeData.waypoints
      .filter(
        (point) =>
          Number.isFinite(Number(point.latitude)) &&
          Number.isFinite(Number(point.longitude))
      )
      .map((point) => [Number(point.latitude), Number(point.longitude)])
    : [];

  const displayedRoute =
    waypointPoints.length > 1
      ? waypointPoints
      : routeData
        ? [originPoint, destinationPoint]
        : [];

  // Route-specific PFZs vs All Live India PFZs
  const corridorPfzZones = Array.isArray(routeData?.pfz?.zones)
    ? routeData.pfz.zones
    : Array.isArray(pfzData?.zones)
      ? pfzData.zones
      : [];

  const allAvailablePfzZones = Array.isArray(pfzData?.all_zones)
    ? pfzData.all_zones
    : Array.isArray(routeData?.pfz?.all_zones)
      ? routeData.pfz.all_zones
      : corridorPfzZones;

  const displayedPfzZones =
    pfzDisplayMode === "none"
      ? []
      : pfzDisplayMode === "all"
        ? allAvailablePfzZones
        : corridorPfzZones;

  const mapPoints =
    displayedRoute.length > 1
      ? displayedRoute
      : locationData?.latitude != null
        ? [[Number(locationData.latitude), Number(locationData.longitude)]]
        : [originPoint, destinationPoint];

  const boundsKey = `${originPoint.join(",")}|${destinationPoint.join(",")}|${waypointPoints.length}`;

  const routeRiskLevel = routeData?.route_risk?.risk_level || "LOW";
  const routeLineColor =
    routeRiskLevel === "EXTREME" || routeRiskLevel === "HIGH"
      ? "#ef5350"
      : routeRiskLevel === "MODERATE"
        ? "#f4b942"
        : "#168bd2";

  function handleMapPointPicked(mode, coordString) {
    setClickMode("");
    if (mode === "origin") {
      onOriginChange?.(coordString);
      onPlanRoute?.(null, coordString, destination);
    } else if (mode === "destination") {
      onDestinationChange?.(coordString);
      onPlanRoute?.(null, origin, coordString);
    }
  }

  return (
    <div className="marine-map-panel">
      <div className="marine-map-heading">
        <div>
          <p className="marine-map-eyebrow">
            PAN-INDIA MARITIME GIS, ROUTE CORRIDOR &amp; LIVE PFZ OVERLAY
          </p>
          <p className="marine-map-subtitle">
            Toggle between PFZ thermal/chlorophyll fronts along your active
            route ({corridorPfzZones.length}), all live pan-India PFZ sectors (
            {allAvailablePfzZones.length}), or hide PFZs.
          </p>
        </div>

        <div className="marine-map-live-tag">
          <span className="marine-map-live-dot" />
          {corridorPfzZones.length} Route PFZs · {allAvailablePfzZones.length}{" "}
          Total Live PFZs
        </div>
      </div>

      {/* Universal Indian Port Autocomplete Datalist */}
      <datalist id="indian-ports-list">
        {PORT_SUGGESTIONS.map((portName) => (
          <option key={portName} value={portName} />
        ))}
      </datalist>

      {onOriginChange && onDestinationChange && onPlanRoute && (
        <form
          className="marine-route-form"
          onSubmit={(e) => onPlanRoute(e, origin, destination)}
        >
          <label>
            Origin Port, City, or Coordinate (Any Indian Location)
            <input
              list="indian-ports-list"
              value={origin}
              onChange={(e) => onOriginChange(e.target.value)}
              placeholder="e.g. Kannur, Chennai, Veraval, or lat, lon"
            />
          </label>

          <label>
            Destination Port, City, or Coordinate
            <input
              list="indian-ports-list"
              value={destination}
              onChange={(e) => onDestinationChange(e.target.value)}
              placeholder="e.g. Mangalore, Goa, Paradip, or lat, lon"
            />
          </label>

          <button type="submit" disabled={routeLoading}>
            {routeLoading ? "Calculating..." : "Update Map Route"}
          </button>
        </form>
      )}

      {/* 3-Way PFZ Toggle + Map Layer & Click Mode Toolbar */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "8px",
          marginBottom: "14px",
          alignItems: "center",
        }}
      >
        <div
          style={{
            display: "inline-flex",
            background: "#081523",
            padding: "3px",
            borderRadius: "9px",
            border: "1px solid #2a4258",
            gap: "4px",
          }}
        >
          <button
            type="button"
            onClick={() => setPfzDisplayMode("route")}
            style={{
              padding: "6px 11px",
              fontSize: "11px",
              borderRadius: "6px",
              background:
                pfzDisplayMode === "route" ? "#16a878" : "transparent",
              color: pfzDisplayMode === "route" ? "#041f18" : "#9eb3c8",
            }}
          >
            Route PFZs Only ({corridorPfzZones.length})
          </button>

          <button
            type="button"
            onClick={() => setPfzDisplayMode("all")}
            style={{
              padding: "6px 11px",
              fontSize: "11px",
              borderRadius: "6px",
              background: pfzDisplayMode === "all" ? "#0284c7" : "transparent",
              color: pfzDisplayMode === "all" ? "#ffffff" : "#9eb3c8",
            }}
          >
            All Live PFZs ({allAvailablePfzZones.length})
          </button>

          <button
            type="button"
            onClick={() => setPfzDisplayMode("none")}
            style={{
              padding: "6px 11px",
              fontSize: "11px",
              borderRadius: "6px",
              background: pfzDisplayMode === "none" ? "#334155" : "transparent",
              color: pfzDisplayMode === "none" ? "#f8fafc" : "#9eb3c8",
            }}
          >
            No PFZs
          </button>
        </div>

        <button
          type="button"
          onClick={() => setShowRestricted((v) => !v)}
          style={{
            padding: "7px 12px",
            fontSize: "11px",
            background: showRestricted ? "#ef5350" : "#10263a",
            color: showRestricted ? "#fff" : "#9eb3c8",
            border: "1px solid #2a4258",
          }}
        >
          {showRestricted ? "✓ Restricted Zones" : "Show Restricted Zones"}
        </button>

        <button
          type="button"
          onClick={() =>
            setClickMode((m) => (m === "origin" ? "" : "origin"))
          }
          style={{
            padding: "7px 12px",
            fontSize: "11px",
            background: clickMode === "origin" ? "#43d5e8" : "#10263a",
            color: clickMode === "origin" ? "#031923" : "#9eb3c8",
            border: "1px solid #2a4258",
          }}
        >
          {clickMode === "origin"
            ? "📍 Click Map to Set Origin (Cancel)"
            : "Pick Origin on Map"}
        </button>

        <button
          type="button"
          onClick={() =>
            setClickMode((m) => (m === "destination" ? "" : "destination"))
          }
          style={{
            padding: "7px 12px",
            fontSize: "11px",
            background: clickMode === "destination" ? "#ef8354" : "#10263a",
            color: clickMode === "destination" ? "#031923" : "#9eb3c8",
            border: "1px solid #2a4258",
          }}
        >
          {clickMode === "destination"
            ? "📍 Click Map to Set Destination (Cancel)"
            : "Pick Destination on Map"}
        </button>
      </div>

      {clickMode && (
        <div
          style={{
            marginBottom: "12px",
            padding: "10px 14px",
            borderRadius: "8px",
            background: "rgba(67, 213, 232, 0.12)",
            border: "1px solid rgba(67, 213, 232, 0.35)",
            color: "#a9edf4",
            fontSize: "12px",
          }}
        >
          <strong>Map Selection Active:</strong> Click any point on the ocean or
          coastline below to set your{" "}
          <strong>{clickMode === "origin" ? "Origin" : "Destination"}</strong>{" "}
          and automatically calculate the route.
        </div>
      )}

      {routeError && <div className="marine-map-error">{routeError}</div>}

      <div className="marine-map-canvas">
        <MapContainer
          center={[13.3, 74.5]}
          zoom={6}
          scrollWheelZoom={true}
          className="marine-leaflet-map"
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapBounds boundsKey={boundsKey} points={mapPoints} />
          <MapClickSelector
            clickMode={clickMode}
            onMapPointPicked={handleMapPointPicked}
          />

          {/* Queried Location Marker */}
          {locationData?.latitude != null &&
            locationData?.longitude != null && (
              <Marker
                position={[
                  Number(locationData.latitude),
                  Number(locationData.longitude),
                ]}
                icon={queryPinIcon}
              >
                <Popup>
                  <strong>Active Query Focus</strong>
                  <br />
                  {locationData.name}
                  {advisoryData && (
                    <>
                      <br />
                      <strong>Fishing Status:</strong> {advisoryData.status} (
                      {advisoryData.risk_level} RISK)
                    </>
                  )}
                </Popup>
              </Marker>
            )}

          {/* Origin Marker */}
          <Marker position={originPoint} icon={originIcon}>
            <Popup>
              <strong>Origin</strong>
              <br />
              {routeData?.origin?.name || origin}
              <br />
              <small>
                {originPoint[0].toFixed(4)}, {originPoint[1].toFixed(4)}
              </small>
            </Popup>
          </Marker>

          {/* Destination Marker */}
          <Marker position={destinationPoint} icon={destinationIcon}>
            <Popup>
              <strong>Destination</strong>
              <br />
              {routeData?.destination?.name || destination}
              <br />
              <small>
                {destinationPoint[0].toFixed(4)},{" "}
                {destinationPoint[1].toFixed(4)}
              </small>
            </Popup>
          </Marker>

          {/* Live PFZ Zones (Controlled by 3-Way Toggle: Route Only | All Live | None) */}
          {displayedPfzZones.map((zone) => {
            const isCorridor = zone.on_route !== false;
            const strokeColor = isCorridor ? "#00c896" : "#38bdf8";
            const fillColor = isCorridor ? "#00e6ac" : "#38bdf8";
            return (
              <div key={zone.zone_id}>
                <Circle
                  center={[Number(zone.lat), Number(zone.lon)]}
                  radius={(zone.radius_km || 18) * 1000}
                  pathOptions={{
                    color: strokeColor,
                    weight: isCorridor ? 2.5 : 1.5,
                    fillColor: fillColor,
                    fillOpacity: isCorridor ? 0.25 : 0.15,
                    dashArray: isCorridor ? undefined : "4 4",
                  }}
                />
                <CircleMarker
                  center={[Number(zone.lat), Number(zone.lon)]}
                  radius={isCorridor ? 6 : 5}
                  pathOptions={{
                    color: "#ffffff",
                    weight: 2,
                    fillColor: isCorridor ? "#00a87e" : "#0284c7",
                    fillOpacity: 1,
                  }}
                >
                  <Popup>
                    <strong>
                      {zone.zone_id} · {zone.sector}
                    </strong>
                    <br />
                    <span
                      style={{
                        display: "inline-block",
                        margin: "3px 0",
                        padding: "2px 6px",
                        borderRadius: "4px",
                        fontSize: "10px",
                        fontWeight: 700,
                        background: isCorridor ? "#d1fae5" : "#e0f2fe",
                        color: isCorridor ? "#065f46" : "#075985",
                      }}
                    >
                      {isCorridor
                        ? "ON ACTIVE ROUTE CORRIDOR"
                        : "PAN-INDIA LIVE PFZ SECTOR"}
                    </span>
                    <br />
                    <strong>Target Species:</strong>{" "}
                    {zone.species || "Pelagic Shoals, Mackerel, Sardine"}
                    <br />
                    <strong>Depth:</strong> {zone.depth_m} m ·{" "}
                    <strong>Confidence:</strong> {zone.confidence || "ACTIVE"}
                    {zone.sst_c != null && (
                      <>
                        <br />
                        <strong>Live Sea Surface Temp (SST):</strong>{" "}
                        {zone.sst_c} °C
                      </>
                    )}
                    {zone.chlorophyll_mg_m3 != null && (
                      <>
                        <br />
                        <strong>Chlorophyll-a:</strong>{" "}
                        {zone.chlorophyll_mg_m3} mg/m³ (
                        {zone.bloom_status || "ACTIVE"})
                      </>
                    )}
                    {zone.wave_height_m != null && (
                      <>
                        <br />
                        <strong>Live Wave Height:</strong> {zone.wave_height_m}{" "}
                        m
                      </>
                    )}
                    {zone.current_velocity_kmh != null && (
                      <>
                        <br />
                        <strong>Ocean Current Drift:</strong>{" "}
                        {zone.current_velocity_kmh} km/h
                      </>
                    )}
                    {zone.distance_from_route_km != null && (
                      <>
                        <br />
                        <strong>Distance from Route:</strong>{" "}
                        {zone.distance_from_route_km} km
                      </>
                    )}
                    <br />
                    <strong>Drifted Coordinates:</strong> {zone.lat}, {zone.lon}
                    {onDestinationChange && (
                      <div style={{ marginTop: "8px" }}>
                        <button
                          type="button"
                          onClick={() => {
                            const coordStr = `${zone.lat}, ${zone.lon}`;
                            onDestinationChange(coordStr);
                            onPlanRoute?.(null, origin, coordStr);
                          }}
                          style={{
                            padding: "5px 10px",
                            fontSize: "11px",
                            background: "#0d8f83",
                            color: "#fff",
                            border: "none",
                            borderRadius: "5px",
                            cursor: "pointer",
                          }}
                        >
                          Set PFZ as Route Destination
                        </button>
                      </div>
                    )}
                  </Popup>
                </CircleMarker>
              </div>
            );
          })}

          {/* Restricted Marine Zones Layer */}
          {showRestricted &&
            RESTRICTED_ZONES.map((rz, idx) => (
              <Polygon
                key={idx}
                positions={rz.positions}
                pathOptions={{
                  color: "#ff4d4d",
                  weight: 2,
                  fillColor: "#ff4d4d",
                  fillOpacity: 0.28,
                }}
              >
                <Popup>
                  <strong>{rz.name}</strong>
                  <br />
                  Type: {rz.type}
                  <br />
                  <em>Fishing and transit prohibited in this zone.</em>
                </Popup>
              </Polygon>
            ))}

          {/* Sea Route Polyline */}
          {displayedRoute.length > 1 && (
            <Polyline
              positions={displayedRoute}
              pathOptions={{
                color: routeLineColor,
                weight: 4,
                opacity: 0.92,
              }}
            />
          )}

          {/* Route Waypoint Markers */}
          {waypointPoints.map((point, index) => {
            const wpMeta = routeData?.waypoints?.[index];
            return (
              <CircleMarker
                key={`${point[0]}-${point[1]}-${index}`}
                center={point}
                radius={4}
                pathOptions={{
                  color: "#ffffff",
                  weight: 1.5,
                  fillColor: wpMeta?.restricted ? "#ff4d4d" : routeLineColor,
                  fillOpacity: 1,
                }}
              >
                <Popup>
                  <strong>Waypoint {index + 1}</strong>
                  <br />
                  Latitude: {point[0].toFixed(5)}
                  <br />
                  Longitude: {point[1].toFixed(5)}
                  {wpMeta?.cumulative_km != null && (
                    <>
                      <br />
                      Distance from Origin: {wpMeta.cumulative_km} km
                    </>
                  )}
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>

      {routeData && (
        <div className="marine-route-result">
          <div>
            <span>Estimated sea-route distance</span>
            <strong>{formatValue(routeData.route_distance_km, " km")}</strong>
          </div>

          {routeData.route_distance_nm != null && (
            <div>
              <span>Nautical distance</span>
              <strong>{formatValue(routeData.route_distance_nm, " NM")}</strong>
            </div>
          )}

          <div>
            <span>Straight-line distance</span>
            <strong>
              {formatValue(routeData.straight_line_distance_km, " km")}
            </strong>
          </div>

          {routeData.estimated_duration_hours != null && (
            <div>
              <span>Est. vessel transit (12 kn)</span>
              <strong>
                {formatValue(routeData.estimated_duration_hours, " hrs")}
              </strong>
            </div>
          )}

          <div>
            <span>Route risk status</span>
            <strong>
              {routeData.route_risk?.risk_level || "LOW"} (
              {routeData.route_risk?.recommendation || "FAVORABLE"})
            </strong>
          </div>

          <div>
            <span>PFZs along route / Total</span>
            <strong>
              {corridorPfzZones.length} / {allAvailablePfzZones.length}
            </strong>
          </div>
        </div>
      )}

      <div className="marine-map-legend">
        <span>
          <i className="legend-origin" />
          Origin Harbour
        </span>
        <span>
          <i className="legend-destination" />
          Destination
        </span>
        <span>
          <i className="legend-waypoint" />
          Sea-route waypoints
        </span>
        <span>
          <i style={{ background: "#00c896" }} />
          Route Corridor PFZ (SST + Chl-a)
        </span>
        <span>
          <i style={{ background: "#38bdf8" }} />
          Pan-India Live PFZ Sector
        </span>
        <span>
          <i style={{ background: "#ff4d4d" }} />
          Restricted Marine Zone
        </span>
      </div>

      <div className="marine-map-safety-note">
        <strong>Navigation limitation</strong>
        <p>
          This route and PFZ overlay is a decision-support visualization
          estimate, not a certified navigational chart. Verify against official
          INCOIS/IMD advisories, bathymetry, and local port clearances before
          operating a vessel.
        </p>
      </div>
    </div>
  );
}