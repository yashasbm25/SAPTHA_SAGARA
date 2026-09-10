# API REFERENCE

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication. Production deployment should add:
- OAuth2 with OpenID Connect
- API key rotation
- Rate limiting per user

## Endpoints

### Chat / Query

#### POST /api/chat
Send a natural language marine intelligence query.

**Request:**
```json
{
  "session_id": "session-123456",
  "user_message": "Is it safe to go fishing tomorrow?"
}
```

**Response:**
```json
{
  "session_id": "session-123456",
  "response": "MARINE INTELLIGENCE REPORT...",
  "risk_assessment": {
    "risk_score": 45.2,
    "risk_level": "MODERATE",
    "factors": [
      "Wave height: 2.5m - Score: 10",
      "Wind speed: 18 kph - Score: 10",
      "Rainfall: 5mm - Score: 5"
    ],
    "recommendation": "Proceed with caution...",
    "data_quality": "high",
    "sources": ["Open-Meteo", "INCOIS"],
    "timestamp": "2026-09-10T10:30:00Z",
    "evidence": {...}
  },
  "marine_data": [
    {"type": "weather", "data": {...}},
    {"type": "ocean", "data": {...}}
  ],
  "evidence": {
    "plan": {...},
    "data_sources": ["Open-Meteo API"],
    "timestamp": "2026-09-10T10:30:00Z"
  },
  "data_freshness": {
    "weather": "real-time",
    "ocean": "real-time",
    "timestamp": "2026-09-10T10:30:00Z"
  },
  "timestamp": "2026-09-10T10:30:00Z"
}
```

### Weather Data

#### GET /api/weather
Get weather forecast for a location.

**Query Parameters:**
- `lat` (float, default: 13.3386) - Latitude
- `lon` (float, default: 74.7421) - Longitude

**Response:**
```json
{
  "location": {"lat": 13.3386, "lon": 74.7421},
  "data": {
    "latitude": 13.3386,
    "longitude": 74.7421,
    "hourly": {
      "time": [...],
      "temperature_2m": [...],
      "windspeed_10m": [...],
      "precipitation": [...],
      "visibility": [...]
    },
    "daily": {...}
  }
}
```

### Ocean Conditions

#### GET /api/ocean
Get ocean/marine conditions.

**Query Parameters:**
- `lat` (float, default: 13.3386) - Latitude
- `lon` (float, default: 74.7421) - Longitude

**Response:**
```json
{
  "location": {"lat": 13.3386, "lon": 74.7421},
  "data": {
    "latitude": 13.3386,
    "longitude": 74.7421,
    "hourly": {
      "time": [...],
      "ocean_surface_wave_height": [...],
      "ocean_surface_wave_period": [...],
      "sea_surface_temperature": [...]
    },
    "daily": {...}
  }
}
```

### Risk Assessment

#### GET /api/risk
Calculate risk score from marine conditions.

**Query Parameters:**
- `wave_height` (float, default: 1.5) - Wave height in meters
- `wind_speed` (float, default: 10.0) - Wind speed in kph
- `rainfall` (float, default: 0.0) - Rainfall in mm

**Response:**
```json
{
  "risk_score": 45.2,
  "risk_level": "MODERATE",
  "factors": [
    "Wave height: 1.5m - Score: 0",
    "Wind speed: 10.0 kph - Score: 0",
    "Rainfall: 0.0mm - Score: 0"
  ],
  "recommendation": "Safe to operate. Monitor conditions regularly.",
  "data_quality": "high",
  "sources": ["Open-Meteo", "INCOIS"],
  "timestamp": "2026-09-10T10:30:00Z",
  "evidence": {...}
}
```

### System

#### GET /
Root endpoint - system info.

**Response:**
```json
{
  "message": "SAPTHA SAGARA - Agentic Marine Intelligence Platform",
  "version": "0.1.0",
  "docs": "/docs"
}
```

#### GET /health
Health check.

**Response:**
```json
{
  "status": "healthy"
}
```

#### GET /docs
Interactive API documentation (Swagger UI).

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error processing request"
}
```

## Risk Levels

| Level | Score | Recommendation |
|-------|-------|----------------|
| SAFE | 0-25 | Safe to operate. Monitor conditions regularly. |
| MODERATE | 26-50 | Proceed with caution. Consider staying near shore. |
| HIGH | 51-75 | High risk. Recommended to postpone operations. |
| CRITICAL | 76-100 | Critical conditions. Do not venture out. |

## Rate Limiting

Currently: No rate limiting (development mode)

Production recommendation:
- 100 requests/minute per IP
- 1000 requests/hour per authenticated user
- Queue large batch jobs

## Response Times

Typical latency:
- Chat query: 2-5 seconds
- Weather API: 500ms
- Ocean API: 500ms
- Risk calculation: <100ms

## Data Freshness

| Data | Freshness | Cache |
|------|-----------|-------|
| Weather | Real-time | 4 hours |
| Ocean | Real-time | 2 hours |
| PFZ | Daily | 24 hours |
| Alerts | Real-time | 1 hour |
