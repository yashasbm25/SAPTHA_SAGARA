# SAPTHA SAGARA
## Agentic Marine Intelligence Platform

### Overview

SAPTHA SAGARA is an intelligent conversational marine decision-support platform that combines agentic AI, satellite Earth observation, oceanographic data, and weather intelligence to provide actionable marine insights to fishermen, researchers, coastal authorities, and maritime users.

### Core Mission

Deliver real-time, evidence-based marine safety assessments and optimal fishing zone recommendations through natural language conversation.

### Architecture

```
USER QUERY
    ↓
CONVERSATIONAL LAYER
    ↓
MASTER PLANNER (LangGraph)
    ↓
[Weather | Ocean | PFZ | Geospatial | Risk | Route] AGENTS
    ↓
DATA PROVIDERS (INCOIS, IMD, Open-Meteo, MOSDAC)
    ↓
DATA FUSION & NORMALIZATION
    ↓
RISK ENGINE (Deterministic Scoring)
    ↓
EVIDENCE VERIFICATION
    ↓
EXPLAINABLE RESPONSE + MAP
```

### Tech Stack

**Backend:**
- Python 3.11
- FastAPI
- LangGraph (Agent Orchestration)
- Pydantic (Data Validation)
- PostgreSQL + PostGIS (Geospatial Database)
- Redis (Caching)
- GeoPandas, Shapely (GIS Operations)

**Frontend:**
- React 18 + TypeScript
- Vite
- Tailwind CSS
- MapLibre GL JS
- TanStack Query

**Data Sources:**
- INCOIS (PFZ, Ocean State, Tides)
- IMD (Weather, Cyclone Alerts)
- Open-Meteo (Weather, Marine Forecasts)
- MOSDAC (Satellite Data)

### Quick Start

```bash
# Clone repository
git clone https://github.com/yashasbm25/SAPTHA_SAGARA.git
cd SAPTHA_SAGARA

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up --build

# Access platform
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Demo Queries

1. **Safety Assessment**: "Is it safe to go fishing tomorrow morning from Mangalore?"
2. **PFZ Discovery**: "Where is the nearest productive fishing zone?"
3. **Conditions Report**: "Show me tide, weather and sea conditions at my location."
4. **Alert Check**: "Are there cyclone or lightning alerts in my region?"
5. **Route Planning**: "Find the safest route to the nearest suitable PFZ."
6. **Multi-turn**: "What about next week?" (remembers context)
7. **Multilingual**: Same queries in Kannada, Hindi, Tamil, Telugu, Malayalam

### Project Structure

```
backend/
├── app/
│   ├── agents/              # LangGraph agents
│   ├── tools/               # Tool definitions
│   ├── providers/           # Data provider adapters
│   ├── services/            # Business logic
│   ├── schemas/             # Pydantic models
│   ├── database/            # ORM and migrations
│   ├── api/                 # FastAPI routes
│   └── main.py              # Application entry
├── tests/                   # Unit and integration tests
├── requirements.txt         # Python dependencies
└── docker-entrypoint.sh

frontend/
├── src/
│   ├── components/          # React components
│   ├── pages/               # Page layouts
│   ├── services/            # API client
│   ├── hooks/               # Custom React hooks
│   ├── types/               # TypeScript types
│   ├── styles/              # Global styles
│   └── App.tsx
├── package.json
└── Dockerfile

data/
├── sample/                  # Sample datasets
├── pfz/                     # PFZ boundaries
├── boundaries/              # EEZ, MPA
└── ocean/                   # Ocean state samples

docs/                        # Architecture, API, deployment docs
```

### Key Features

✅ **Conversational Interface** - Natural language queries in English + Indian languages
✅ **Master Planner** - Intelligent task decomposition and orchestration
✅ **Multi-Agent System** - Specialized agents for weather, ocean, PFZ, geospatial, risk, routes
✅ **Real Data Integration** - INCOIS, IMD, Open-Meteo, MOSDAC adapters
✅ **Geospatial Intelligence** - PostGIS-powered distance, intersection, geofencing
✅ **Deterministic Risk Engine** - Configurable thresholds, evidence-based scoring
✅ **Route Optimization** - Multi-criteria route analysis with hazard mapping
✅ **Evidence System** - Full traceability from query → data → recommendation
✅ **Interactive Dashboard** - Map layers, chat history, marine alerts panel
✅ **Multilingual Support** - Auto-detect and respond in user's language
✅ **Data Freshness Tracking** - Age and quality metrics for all observations
✅ **Failure Resilience** - Graceful degradation with fallback providers

### API Endpoints

**Chat**
- `POST /chat` - Send query, receive response with evidence
- `GET /chat/{session_id}` - Retrieve conversation history

**Marine Data**
- `GET /weather/forecast` - Weather forecast
- `GET /ocean/conditions` - Sea conditions
- `GET /pfz` - Productive fishing zones
- `GET /alerts/cyclone` - Cyclone warnings
- `GET /alerts/lightning` - Lightning alerts

**Geospatial**
- `POST /geospatial/distance` - Calculate distance
- `POST /geospatial/nearest-pfz` - Find nearest PFZ
- `POST /geospatial/intersection` - Check area intersection

**Routes**
- `POST /routes/optimize` - Generate optimal marine routes
- `GET /routes/{route_id}` - Retrieve route details

### Configuration

**Risk Thresholds** (configurable in backend/app/config/risk.py):
```python
RISK_LEVELS = {
    'SAFE': {'wave_height_max': 1.5, 'wind_max': 15},
    'MODERATE': {'wave_height_max': 3.0, 'wind_max': 25},
    'HIGH': {'wave_height_max': 5.0, 'wind_max': 40},
    'CRITICAL': {'wave_height_max': 999, 'wind_max': 999}
}
```

**Providers** - Each provider is configurable via environment variables and can be swapped without code changes.

### Development

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install

# Run tests
pytest backend/tests -v

# Run linter
flake8 backend/app --max-line-length=100

# Database migrations
alembic upgrade head
```

### Deployment

See `docs/DEPLOYMENT.md` for:
- Docker Compose (development)
- Kubernetes manifests (production)
- Environment configuration
- Database setup
- API scaling

### Documentation

- **Architecture**: `docs/ARCHITECTURE.md`
- **API Reference**: `docs/API.md` (also available at `/docs` on running server)
- **Data Schema**: `docs/DATA_SCHEMA.md`
- **Agent Workflow**: `docs/AGENTS.md`
- **Deployment**: `docs/DEPLOYMENT.md`
- **Contributing**: `CONTRIBUTING.md`

### License

MIT

### Contributors

- Yasha S BM (@yashasbm25)

### Support

For issues, feature requests, or questions:
1. Check existing issues
2. Create a detailed GitHub issue
3. Include environment, error logs, and reproduction steps

### Disclaimer

This platform is a decision-support tool. It does not replace:
- Official marine weather warnings
- Navigation charts and certified systems
- Professional maritime expertise
- Coast Guard or harbor authority directives

Always verify critical safety information with official sources.
