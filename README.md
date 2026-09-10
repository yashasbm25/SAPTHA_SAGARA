# SAPTHA SAGARA - Agentic Marine Intelligence Platform

## Overview

SAPTHA SAGARA is an intelligent conversational marine decision-support platform that combines agentic AI, satellite Earth observation, oceanographic data, and weather intelligence to provide actionable marine insights to fishermen, researchers, coastal authorities, and maritime users.

## Quick Start

```bash
git clone https://github.com/yashasbm25/SAPTHA_SAGARA.git
cd SAPTHA_SAGARA
cp .env.example .env
docker-compose up --build
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Architecture

USER → CONVERSATIONAL LAYER → MASTER PLANNER → SPECIALIZED AGENTS → DATA PROVIDERS → RISK ENGINE → RESPONSE

## Tech Stack

**Backend:** Python, FastAPI, LangGraph, PostgreSQL+PostGIS, Redis
**Frontend:** React, TypeScript, Tailwind, MapLibre GL
**Data:** INCOIS, IMD, Open-Meteo, MOSDAC

## Demo Queries

1. "Is it safe to go fishing tomorrow from Mangalore?"
2. "Where is the nearest productive fishing zone?"
3. "Show tide, weather and sea conditions at my location"
4. "Are there cyclone or lightning alerts?"
5. Same queries in Kannada, Hindi, Tamil, Telugu, Malayalam

## Key Features

✅ Conversational Interface
✅ Master Planner with Task Decomposition
✅ Multi-Agent System (Weather, Ocean, PFZ, Geospatial, Risk, Routes)
✅ Real Data Integration
✅ Deterministic Risk Engine
✅ Route Optimization
✅ Evidence & Traceability
✅ Interactive Dashboard
✅ Multilingual Support
✅ Data Freshness Tracking
✅ Failure Resilience

## Documentation

- Architecture: `docs/ARCHITECTURE.md`
- API Reference: `docs/API.md`
- Deployment: `docs/DEPLOYMENT.md`
- Contributing: `CONTRIBUTING.md`

## Disclaimer

This is a decision-support tool. Always verify critical safety information with official sources.