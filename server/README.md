# LifeOS Server

## Overview

LifeOS Server is the backend foundation for a personal IRL system that continuously ingests, understands, and stores real-life context from video, audio, and interactions. The system enables memory recall, automation, and smart agents through semantic search and intelligent automation triggers.

## Tech Stack

- **FastAPI** – High-performance async API server
- **Asyncio** – Non-blocking tasks for video/audio processing
- **Redis + Redis Queue** – Caching & job queuing for processing pipelines
- **S3** – Long-term video and transcript storage
- **Qdrant** – Vector database for semantic search
- **TwelveLabs** – Video-to-text summarization API
- **OpenAI API** – Context understanding and automation routing
- **BetterAuth** – Authentication
- **Docker** – Containerization

## Project Structure

```
server/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Environment variables and app config
│   │   └── connections.py      # Redis, Qdrant, and S3 connection configs
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py     # Authentication endpoints
│   │   │   │   ├── media.py    # Video/audio upload & processing
│   │   │   │   ├── memory.py   # Memory search & retrieval
│   │   │   │   ├── automation.py # Automation triggers & actions
│   │   │   │   └── summary.py  # Daily summaries & analytics
│   │   │   └── router.py       # API router configuration
│   │   └── dependencies.py     # Shared dependencies & middleware
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # Authentication & authorization
│   │   ├── exceptions.py       # Custom exception handlers
│   │   └── logging.py          # Logging configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User model
│   │   ├── media.py            # Video/audio metadata models
│   │   ├── memory.py           # Memory/transcript models
│   │   ├── automation.py       # Automation rule models
│   │   └── summary.py          # Summary models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── media.py            # Media upload/response schemas
│   │   ├── memory.py           # Memory query/response schemas
│   │   ├── automation.py       # Automation schemas
│   │   └── summary.py          # Summary schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── media_processor.py  # Video/audio processing pipeline
│   │   ├── summarizer.py       # TwelveLabs integration
│   │   ├── vector_store.py     # Qdrant operations
│   │   ├── automation_engine.py # LLM-based automation triggers
│   │   ├── storage.py          # S3 operations
│   │   └── queue.py            # Redis Queue management
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── media_worker.py     # Async video processing worker
│   │   ├── summary_worker.py   # Summary generation worker
│   │   └── automation_worker.py # Automation trigger worker
│   └── utils/
│       ├── __init__.py
│       ├── file_handlers.py    # File upload/download utilities
│       ├── validators.py       # Input validation utilities
│       └── helpers.py          # General utility functions
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Test configuration & fixtures
│   ├── test_api/
│   │   ├── test_auth.py
│   │   ├── test_media.py
│   │   ├── test_memory.py
│   │   └── test_automation.py
│   ├── test_services/
│   │   ├── test_media_processor.py
│   │   ├── test_summarizer.py
│   │   └── test_vector_store.py
│   └── test_workers/
│       ├── test_media_worker.py
│       └── test_summary_worker.py
├── docker/
│   ├── Dockerfile              # Production Docker image
│   ├── docker-compose.yml      # Local development setup
│   └── docker-compose.prod.yml # Production deployment
├── scripts/
│   ├── setup.sh                # Environment setup script
│   ├── init_qdrant.py          # Vector database initialization
│   └── seed_data.py            # Sample data seeding
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── .env.example               # Environment variables template
├── .gitignore
└── README.md                  # This file
```

## Key Components

### 1. Media Processing Pipeline
- **Upload**: Video/audio files uploaded via API
- **Processing**: Async workers process media using TwelveLabs
- **Storage**: Raw files stored in S3, metadata in Redis
- **Vectorization**: Summaries embedded into Qdrant for semantic search

### 2. Memory System
- **Ingestion**: Continuous processing of real-life context
- **Storage**: Metadata in Redis, vectors in Qdrant, files in S3
- **Retrieval**: Semantic search over memory using LLM queries
- **Recall**: Context-aware memory retrieval with metadata

### 3. Automation Engine
- **Triggers**: LLM analysis of memory context
- **Actions**: Integration with external services (Google Calendar, Notion)
- **Routing**: Smart tool selection based on context
- **Execution**: Async automation execution with status tracking

### 4. API Layer
- **RESTful**: FastAPI-based REST endpoints
- **Async**: Non-blocking request handling
- **Auth**: BetterAuth integration for user management
- **Validation**: Pydantic schemas for request/response validation

## Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Redis
- S3-compatible storage
- TwelveLabs API key
- OpenAI API key

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure variables
3. Run `docker-compose up -d` for local development
4. Install dependencies: `pip install -r requirements.txt`
5. Initialize vector database: `python scripts/init_qdrant.py`
6. Start the server: `uvicorn app.main:app --reload`

### Environment Variables

```bash
# Redis
REDIS_URL=redis://localhost:6379

# S3 Storage
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=lifeos-media

# APIs
TWELVELABS_API_KEY=your_twelve_labs_key
OPENAI_API_KEY=your_openai_key

# Vector Database
QDRANT_URL=http://localhost:6333

# Auth
BETTERAUTH_SECRET=your_auth_secret
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout

### Media Processing
- `POST /api/v1/media/upload` - Upload video/audio file
- `GET /api/v1/media/{media_id}` - Get media metadata
- `GET /api/v1/media/{media_id}/status` - Get processing status

### Memory Search
- `POST /api/v1/memory/search` - Semantic memory search
- `GET /api/v1/memory/recent` - Recent memories
- `GET /api/v1/memory/{memory_id}` - Get specific memory

### Automations
- `POST /api/v1/automation/trigger` - Trigger automation
- `GET /api/v1/automation/rules` - List automation rules
- `POST /api/v1/automation/rules` - Create automation rule

### Summaries
- `GET /api/v1/summary/daily` - Get daily summary
- `GET /api/v1/summary/weekly` - Get weekly summary

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black app/ tests/
isort app/ tests/
```

### Type Checking
```bash
mypy app/
```

## Deployment

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Setup
1. Configure production environment variables
2. Set up SSL certificates
3. Configure reverse proxy (nginx)
4. Set up monitoring and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Add your license information here] 