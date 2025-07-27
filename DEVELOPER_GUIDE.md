# LifeOS Developer Guide

## Overview

LifeOS is a personal life management system that captures, processes, and analyzes video data to provide intelligent insights about daily activities. The system consists of a Next.js frontend and a FastAPI backend with real-time video processing capabilities.

## Architecture

### Tech Stack

**Frontend:**
- Next.js 15.4.2 with App Router
- React 19.1.0 with TypeScript
- Tailwind CSS v4 for styling
- Framer Motion for animations
- Axios for API communication

**Backend:**
- FastAPI with Python
- Redis for async task queues
- Qdrant for vector embeddings
- Supabase (PostgreSQL) for metadata
- TwelveLabs API for video analysis
- OpenAI API for text processing
- AWS S3 for file storage

## Project Structure

```
LifeOS/
├── client/          # Next.js Frontend
│   ├── src/
│   │   ├── app/            # Next.js App Router pages
│   │   ├── components/     # Reusable UI components
│   │   ├── contexts/       # React contexts
│   │   ├── hooks/          # Custom React hooks
│   │   ├── config/         # Configuration management
│   │   └── lib/            # Utilities and constants
│   └── public/             # Static assets
│
└── server/                 # Python Backend
    ├── app/                # FastAPI application
    │   ├── api/v1/         # API endpoints
    │   ├── core/           # Core utilities
    │   ├── models/         # Data models
    │   ├── services/       # Business logic
    │   └── config/         # Configuration
    ├── automations/        # Background automations
    ├── video_processing/   # Video processing pipeline
    ├── video_queue/        # Queue management
    └── database/           # Database clients
```

## Key Features

### 🎥 Video System
- Real-time camera capture (720p @ 10 FPS)
- 10-second video segments
- Async processing with Redis queues
- TwelveLabs integration for video analysis
- S3 storage with pre-signed URLs

### 🔍 Semantic Search
- Vector embeddings via TwelveLabs
- Qdrant vector database
- Natural language memory search
- AI-powered chatbot interface

### 📊 Highlights & Insights
- Automated highlight detection
- Daily recap generation
- Recent events analysis
- Interactive video gallery

### 🔐 Authentication
- JWT-based authentication
- Token management with auto-refresh
- Protected routes and API endpoints

## Getting Started

### Prerequisites
```bash
# Required services
- Redis server
- Qdrant vector database
- Supabase account
- AWS S3 bucket
- TwelveLabs API key
- OpenAI API key
```

### Environment Setup

**Frontend (.env.local):**
```env
NEXT_PUBLIC_API_HOST=http://localhost:8000
NEXT_PUBLIC_ENV=development
NEXT_PUBLIC_ENABLE_VIDEO_SYSTEM=true
NEXT_PUBLIC_ENABLE_HIGHLIGHTS=true
NEXT_PUBLIC_ENABLE_CHAT=true
```

**Backend (.env):**
```env
# API Keys
TWELVELABS_API_KEY=your_twelvelabs_key
OPENAI_API_KEY=your_openai_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
QDRANT_URL=http://localhost:6333

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=lifeos-media

# Video Settings
CAMERA_INDEX=0
VIDEO_FPS=10
VIDEO_WIDTH=1280
VIDEO_HEIGHT=720
SEGMENT_DURATION=10

# Workers
NUM_WORKERS=3
WORKER_BATCH_SIZE=5

# Auth
JWT_SECRET=your_jwt_secret
```

### Installation

**Frontend:**
```bash
cd client/lifeos
npm install
npm run dev  # Starts on http://localhost:3000
```

**Backend:**
```bash
cd server
pip install -r requirements.txt
python main.py  # Starts FastAPI on http://localhost:8000
```

## Development Guidelines

### Frontend Patterns

**Component Structure:**
- Use functional components with TypeScript
- Implement custom hooks for reusable logic
- Follow the existing glass morphism design system
- Use Framer Motion for consistent animations

**State Management:**
- React Context for global state (auth, theme)
- Local useState for component state
- Custom hooks for complex logic

**API Communication:**
- Use the centralized axios instance from AuthContext
- Import endpoints from `@/lib/constants`
- Implement proper error handling with `@/lib/errors`

### Backend Patterns

**Service Layer:**
- Extend `BaseService` for common functionality
- Use dependency injection for database connections
- Implement proper error handling and logging

**API Endpoints:**
- Follow RESTful conventions
- Use Pydantic models for validation
- Return consistent response formats
- Include proper HTTP status codes

**Database Operations:**
- Use async/await for all database operations
- Implement connection pooling
- Handle database errors gracefully

## API Documentation

### Authentication Endpoints
```
POST /api/v1/auth/register   # User registration
POST /api/v1/auth/login      # User login
GET  /api/v1/auth/me         # Get current user
```

### Video System Endpoints
```
POST /api/v1/system/start    # Start video capture
GET  /api/v1/system/status   # Get system status
POST /api/v1/system/stop     # Stop video capture
POST /api/v1/system/end      # End video system
```

### Memory & Search Endpoints
```
POST /api/v1/memory/search   # Search memories
POST /api/v1/memory/chatbot  # Chatbot interaction
POST /api/v1/memory/create   # Create memory
```

### Video Management
```
GET    /api/v1/videos/       # List all videos
GET    /api/v1/videos/{id}   # Get specific video
DELETE /api/v1/videos/{id}   # Delete video
```

### Insights & Highlights
```
GET /api/v1/insights/daily_recap     # Get daily recap
GET /api/v1/insights/recent_events   # Get recent events
GET /api/v1/highlights/list          # List highlights
```

## Video Processing Pipeline

1. **Capture**: Real-time camera feed captured in 10-second segments
2. **Queue**: Segments added to Redis processing queue
3. **Upload**: Parallel upload to TwelveLabs and S3
4. **Analysis**: TwelveLabs generates embeddings and metadata
5. **Storage**: Metadata stored in Supabase, embeddings in Qdrant
6. **Indexing**: Vector indexing for semantic search

## Testing

### Frontend Testing
```bash
cd client/lifeos
npm run test        # Run tests
npm run test:watch  # Watch mode
npm run type-check  # TypeScript checking
```

### Backend Testing
```bash
cd server
pytest tests/       # Run all tests
pytest tests/test_qdrant.py  # Specific test
```

## Deployment

### Frontend Deployment
```bash
npm run build       # Production build
npm run start       # Production server
```

### Backend Deployment
```bash
# Using Docker
docker build -t lifeos-server .
docker run -p 8000:8000 lifeos-server

# Using Docker Compose
docker-compose up -d
```

## Performance Considerations

### Frontend Optimization
- Use React.memo for expensive components
- Implement proper loading states
- Optimize image loading with next/image
- Use Framer Motion's `layoutId` for smooth transitions

### Backend Optimization
- Use Redis for caching frequently accessed data
- Implement connection pooling for database connections
- Use async/await for I/O operations
- Monitor queue performance with Redis metrics

## Troubleshooting

### Common Issues

**Video System Not Starting:**
- Check camera permissions
- Verify camera index in environment variables
- Ensure Redis server is running

**Search Not Working:**
- Verify Qdrant connection
- Check TwelveLabs API key and limits
- Ensure vector database is properly indexed

**Authentication Errors:**
- Verify JWT secret configuration
- Check token expiration settings
- Ensure Supabase connection is working

### Monitoring

**Health Checks:**
- Frontend: Monitor API response times
- Backend: Check service health endpoints
- Database: Monitor connection pool usage
- Queue: Monitor Redis queue length

## Contributing

### Code Style
- Use TypeScript for type safety
- Follow existing naming conventions
- Write descriptive commit messages
- Include tests for new features

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Update documentation if needed
5. Submit pull request with description

## Security Considerations

- Never commit API keys or secrets
- Use environment variables for all configuration
- Implement proper input validation
- Sanitize user inputs
- Use HTTPS in production
- Regularly update dependencies

## License

This project is licensed under the MIT License - see the LICENSE file for details.