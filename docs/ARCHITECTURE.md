# ARCHITECTURE.md - SAPTHA SAGARA

## System Architecture

```
┌─────────────────────┐
│   USER (Web UI)     │
└──────────┬──────────┘
           │
    ┌──────▼──────┐
    │  Frontend   │
    │  React App  │
    └──────┬──────┘
           │ HTTP/REST
    ┌──────▼──────────────┐
    │    FastAPI Server   │
    │  :8000/api/chat     │
    └──────┬──────────────┘
           │
    ┌──────▼──────────────────────┐
    │   Master Planner (LangGraph) │
    │   - Intent Detection         │
    │   - Task Decomposition       │
    │   - Orchestration            │
    └──────┬──────────────────────┘
           │
  ┌────────┼────────┬───────────┬────────────┐
  │        │        │           │            │
  ▼        ▼        ▼           ▼            ▼
┌──────┐ ┌────┐ ┌─────┐ ┌───────────┐ ┌──────┐
│Wthr  │ │OCN │ │ PFZ │ │Geospatial │ │Route │
│Agent │ │Agnt│ │Agent│ │   Engine  │ │Agent │
└──┬───┘ └─┬──┘ └─┬───┘ └────┬──────┘ └──┬───┘
   │       │      │          │           │
   └───────┼──────┼──────────┼───────────┘
           │      │          │
     ┌─────▼──────▼──────────▼───┐
     │  Data Provider Adapters   │
     │ ┌──────────────────────┐  │
     │ │Open-Meteo (Weather)  │  │
     │ │INCOIS (Ocean/PFZ)    │  │
     │ │IMD (Alerts)          │  │
     │ │MOSDAC (Satellite)    │  │
     │ └──────────────────────┘  │
     └─────┬──────────────────────┘
           │
     ┌─────▼──────────┐
     │ Risk Engine    │
     │ (Deterministic)│
     └─────┬──────────┘
           │
     ┌─────▼──────────────┐
     │ Evidence Layer     │
     │ (Data Fusion)      │
     └─────┬──────────────┘
           │
     ┌─────▼──────────┐
     │ Response       │
     │ Formatting     │
     └─────┬──────────┘
           │
     ┌─────▼──────────────────────┐
     │  Frontend Display           ���
     │ - Chat History              │
     │ - Risk Assessment Card      │
     │ - Map with Layers           │
     │ - Evidence Panel            │
     └─────────────────────────────┘
```

## Components

### 1. Conversational Layer (Frontend)
- React 18 + TypeScript
- Real-time chat interface
- Interactive map (MapLibre GL)
- Marine conditions panel

### 2. Master Planner (Backend)
- LangGraph orchestration
- Intent detection via LLM
- Task decomposition
- Agent coordination

### 3. Specialized Agents

**Weather Agent**
- Fetches weather forecasts
- Wind, temperature, precipitation
- Visibility, lightning alerts

**Ocean Agent**
- Sea surface temperature
- Wave height, period, swell
- Currents, tides
- Ocean state forecasts

**PFZ Agent**
- Productive fishing zone data
- Distance calculations
- SST and chlorophyll correlation
- Zone ranking

**Geospatial Engine**
- PostGIS integration
- Distance calculations
- Point-in-polygon tests
- Nearest neighbor queries
- EEZ/MPA checks

**Risk Engine**
- Deterministic scoring algorithm
- Wave height assessment (40 pts)
- Wind assessment (30 pts)
- Rainfall assessment (15 pts)
- Alert scoring (15 pts)
- Total: 0-100 scale

**Route Intelligence**
- Multi-criteria path optimization
- Hazard mapping
- Restricted area avoidance
- Route risk scoring

### 4. Data Providers

**OpenMeteoProvider**
- Free, no auth required
- Weather forecasts
- Marine conditions (waves, SST)

**INCOISProvider** (Placeholder)
- PFZ data
- Ocean state
- Tides
- Marine advisories

**IMDProvider** (Placeholder)
- Weather alerts
- Cyclone warnings
- Severe weather

**MOSDACProvider** (Placeholder)
- Satellite Earth observation
- Environmental products

### 5. Data Fusion & Normalization

All data normalized to common schema:
```python
{
  "source": "INCOIS",
  "parameter": "wave_height",
  "value": 2.4,
  "unit": "m",
  "location": {"lat": 13.34, "lon": 74.74},
  "forecast_time": "2026-09-10T10:00:00Z",
  "retrieved_at": "2026-09-10T09:15:00Z",
  "quality": "high",
  "confidence": 0.95
}
```

### 6. Evidence System

Every response includes:
- Data sources used
- Calculations performed
- Agent involvement
- Risk methodology
- Data freshness
- Confidence levels

## Database Schema (PostgreSQL + PostGIS)

```sql
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY,
  user_id VARCHAR,
  location GEOMETRY(Point, 4326),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE chat_messages (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES chat_sessions,
  user_message TEXT,
  assistant_response TEXT,
  risk_assessment JSONB,
  marine_data JSONB,
  created_at TIMESTAMP
);

CREATE TABLE pfz_data (
  pfz_id VARCHAR PRIMARY KEY,
  name VARCHAR,
  geometry GEOMETRY(Polygon, 4326),
  sst_optimal NUMRANGE,
  species TEXT[],
  last_updated TIMESTAMP
);

CREATE TABLE marine_alerts (
  id UUID PRIMARY KEY,
  alert_type VARCHAR,
  severity VARCHAR,
  region GEOMETRY(Polygon, 4326),
  issued_at TIMESTAMP,
  expires_at TIMESTAMP
);
```

## Data Flow

1. **Query Reception**
   - User sends natural language query
   - Frontend sends to `/api/chat`

2. **Planning**
   - Master Planner analyzes query
   - Identifies intent (safety, PFZ discovery, etc)
   - Creates task list
   - Determines parallel vs sequential execution

3. **Data Gathering** (Parallel)
   - Weather Agent → Open-Meteo
   - Ocean Agent → Open-Meteo
   - PFZ Agent → INCOIS
   - Alert Agent → IMD
   - Geospatial lookups → PostGIS

4. **Data Fusion**
   - Normalize all data to common schema
   - Merge related observations
   - Calculate aggregate metrics

5. **Risk Assessment**
   - Deterministic algorithm
   - Score each factor
   - Sum weighted components
   - Determine risk level
   - Generate recommendation

6. **Evidence Compilation**
   - Track all sources
   - Document calculations
   - Record data freshness
   - Timestamp results

7. **Response Formatting**
   - Generate natural language summary
   - Highlight key metrics
   - Include recommendations
   - Add disclaimer for safety data

8. **Frontend Display**
   - Chat message
   - Risk card with color coding
   - Map updates with relevant layers
   - Evidence panel for drilling down

## Failure Handling

### Provider Failure
- Attempt fallback providers
- Reduce confidence score
- Mark data as stale
- Continue with partial data
- Report unavailable data to user

### Critical Data Missing
- Do NOT claim safety
- Return uncertainty message
- Suggest retry or manual verification
- Log incident for monitoring

### Graceful Degradation
```
Ideal: Weather + Ocean + PFZ + Alerts + Geospatial
Good:  Weather + Ocean + Alerts
Okay:  Weather + Alerts
Bad:   Only weather or only alerts
Fail:  No data available
```

## Performance Considerations

1. **Concurrency**
   - Agents run in parallel
   - FastAPI handles async requests
   - Redis caching for frequent queries

2. **Caching**
   - Weather forecasts (4 hours)
   - Ocean conditions (2 hours)
   - PFZ data (24 hours)
   - Alerts (1 hour)

3. **Optimization**
   - PostGIS spatial indexing
   - Database query optimization
   - Response compression
   - Lazy loading for maps

## Security

- API keys in environment variables
- Input validation (Pydantic)
- Rate limiting on endpoints
- CORS configured for frontend
- No sensitive data in logs
- HTTPS in production
