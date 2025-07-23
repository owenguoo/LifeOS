# LifeOS
> A multi-modal MCP layer for real life — built on a continuous video feed, semantic search and natural language video understanding.  

## Overview

LifeOS is the foundational layer for smart glasses, providing context and automations on top of your real-life experiences. It leverages video/audio ingestion, semantic search, and automation triggers to help you recall memories, automate tasks, and interact with your life data.

## Architecture

<img width="6000" height="3000" alt="lifeos system diagram" src="https://github.com/user-attachments/assets/acd420cb-edff-4159-872e-bf18a76a4df7" />

### Deployment
```
┌───────────────┐    ┌────────────────────┐    ┌────────────────────┐
│   Frontend    │    │   Web API Service  │    │  Local Video       │
│   (Next.js)   │◄──►│   (FastAPI)        │◄──►│  Processing        │
└───────────────┘    └────────────────────┘    └────────────────────┘
                             │
                             ▼
                      ┌────────────────────┐
                      │  External APIs     │
                      │  (Qdrant, S3,      │
                      │   TwelveLabs, etc) │
                      └────────────────────┘
```

- **Frontend**: Mobile-first Next.js app, Tailwind CSS, Framer Motion
- **Backend**: FastAPI server, Docker, Asyncio, Redis Queue 
- **External Services**: Qdrant (vector DB), S3 (raw video storage), Supabase, TwelveLabs (summarization + embedding), OpenAI

## Key Features

- **Continuous Context Capture**: Ingests video/audio, summarizes, and embeds into a vector DB.
- **Semantic Memory Search**: Natural language search over your life memories.
- **Agentic Automations**: LLMs trigger actions (e.g., add calendar events) based on context.
- **Extensible Integrations**: Foundational layer provides context and an automation pipeline to integrate external tools like Google Calendar and internal features like highlights clipping.

## Frontend

- **Bottom navigation**: Chatbot, Highlights, Recent Activity, Automations.
- **Semantic search bar**: Find relevant videos and context with natural language.
- **Customizable dashboard widgets** (e.g., time, summary of day).
- **Chatbot**: Query your life memory and trigger automations.

See [`docs/frontend_vision.md`](docs/frontend_vision.md) for full design philosophy.

## Backend

- **Continuous video feed**: Uses OpenCV and PyAudio to feed 10 second clips to the pipeline. 
- **Media processing pipeline**: Async workers process and summarize video/audio, store in S3, embed in Qdrant.
- **Memory system**: Ingests, stores, and retrieves memories with semantic search.
- **Automation engine**: LLM-based triggers for external integrations.
- **RESTful API**: Auth, media, memory, automation, and summary endpoints.

See [`server/README.md`](server/README.md) for backend details.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker
- Redis
- AWS S3
- TwelveLabs API key
- OpenAI API key

### Backend

```bash
# Clone the repository
git clone https://github.com/owenguoo/LifeOS.git
cd LifeOS/server

# Copy and configure environment variables
cp env.example .env

# Start services (Qdrant, Redis, server)
docker-compose up -d

# Install dependencies (if running locally)
pip install -r requirements.txt
```

### Local Video Processing

```bash
cd LifeOS/server
pip install -r requirements.txt
python main.py both
```

### Frontend

```bash
cd LifeOS/client/lifeos
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` – Register
- `POST /api/v1/auth/login` – Login
- `POST /api/v1/auth/logout` – Logout

### Media
- `POST /api/v1/media/upload` – Upload video/audio
- `GET /api/v1/media/{media_id}` – Get metadata
- `GET /api/v1/media/{media_id}/status` – Processing status

### Memory
- `POST /api/v1/memory/search` – Semantic search
- `GET /api/v1/memory/recent` – Recent memories
- `GET /api/v1/memory/{memory_id}` – Get memory

### Automations
- `POST /api/v1/automation/trigger` – Trigger automation
- `GET /api/v1/automation/rules` – List rules
- `POST /api/v1/automation/rules` – Create rule

### Summaries
- `GET /api/v1/summary/daily` – Daily summary
- `GET /api/v1/summary/weekly` – Weekly summary

### Chatbot
- `POST /api/v1/memory/chatbot` – Natural language memory search

