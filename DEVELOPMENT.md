# DEVELOPMENT GUIDE

## Setup

```bash
cd backend
pip install -r requirements.txt

cd ../frontend
npm install
```

## Running Locally

### Backend
```bash
cd backend
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm run dev
```

## Running with Docker

```bash
docker-compose up --build
```

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## API Documentation

Once backend is running, visit: http://localhost:8000/docs

## Environment Setup

Copy `.env.example` to `.env` and configure:
- OPENAI_API_KEY: Your OpenAI API key
- DATABASE_URL: PostgreSQL connection string
- REDIS_URL: Redis connection string

## Project Structure

- `backend/app/` - FastAPI application
- `backend/app/agents/` - LangGraph agents
- `backend/app/providers/` - Data provider adapters
- `backend/app/services/` - Business logic (risk engine, etc)
- `backend/app/schemas/` - Pydantic models
- `backend/app/api/` - API routes
- `frontend/src/` - React TypeScript application
- `frontend/src/components/` - React components

## Key Endpoints

- `POST /api/chat` - Send marine intelligence query
- `GET /api/weather` - Get weather forecast
- `GET /api/ocean` - Get ocean conditions
- `GET /api/risk` - Calculate risk score

## Demo Queries

1. "Is it safe to go fishing tomorrow morning from Mangalore?"
2. "Where is the nearest productive fishing zone?"
3. "Show me tide, weather and sea conditions at my location"
4. "Are there cyclone or lightning alerts?"
5. "Find the safest route to the nearest PFZ"

## Contributing

1. Create feature branch from `dev`
2. Make changes
3. Run tests
4. Push and create PR
5. Merge to `dev` after review
