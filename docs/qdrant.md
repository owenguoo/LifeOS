# Qdrant Integration for LifeOS Server

This document describes the Qdrant vector database integration implemented in the LifeOS Server.

## Overview

The Qdrant integration provides semantic search capabilities for storing and retrieving memories/past summaries from videos (embedding the text, NOT the video) using vector embeddings. It enables users to search through their personal memories using natural language queries.

## Architecture

### Components

1. **VectorStoreService** (`app/services/vector_store.py`)
   - Manages Qdrant client connection
   - Handles CRUD operations for memories
   - Provides semantic search functionality
   - Manages collection initialization and indexing

2. **EmbeddingService** (`app/services/embedding_service.py`)
   - Generates text embeddings using OpenAI API
   - Handles API rate limiting and error handling

3. **Memory Models** (`app/models/memory.py`)
   - `MemoryPoint`: Core data model for vector storage
   - `MemorySearchResult`: Search result model

4. **API Endpoints** (`app/api/v1/endpoints/memory.py`)
   - RESTful API for memory operations
   - Semantic search endpoints
   - Health check and statistics endpoints

## Features

### Memory Operations
- **Create Memory**: Store new memories with automatic embedding generation
- **Get Memory**: Retrieve specific memories by ID
- **Delete Memory**: Remove memories from the vector store

### Semantic Search
- **Natural Language Queries**: Search using human-readable text
- **Filtering**: Filter by content type, tags, date range
- **Similarity Scoring**: Results ranked by semantic similarity
- **Configurable Limits**: Control number of results and score thresholds

### Collection Management
- **Automatic Initialization**: Collection created on first startup
- **Indexed Fields**: Optimized filtering on user_id, content_type, timestamp, tags
- **Statistics**: Monitor collection health and performance

## API Endpoints

### Memory Management
```
POST /api/v1/memory/create          # Create single memory
GET  /api/v1/memory/{memory_id}     # Get specific memory
DELETE /api/v1/memory/delete        # Delete memories
```

### Search & Analytics
```
POST /api/v1/memory/search          # Semantic search
GET  /api/v1/memory/stats/collection # Collection statistics
GET  /api/v1/memory/health          # Health check
```

## Configuration

### Environment Variables
```bash
# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_api_key_optional

# OpenAI Configuration (for embeddings)
OPENAI_API_KEY=your_openai_api_key
```

### Collection Settings
- **Vector Size**: 1536 (OpenAI text-embedding-ada-002)
- **Distance Metric**: Cosine similarity
- **Collection Name**: `lifeos_memories`

## Setup Instructions

### 1. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys

### 2. Docker Compose
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f lifeos-server
```

### 3. Testing
```bash
# Run the test script
python test_qdrant.py
```

## Performance Considerations

### Vector Search Optimization
- **Indexed Fields**: User ID, content type, timestamp, and tags are indexed
- **Filtering**: Use filters to reduce search space before vector similarity
- **Individual Operations**: Optimized for real-time memory creation (1 per 10 seconds)

### Embedding Generation
- **Caching**: Consider implementing embedding cache for repeated content
- **Rate Limiting**: OpenAI API has rate limits, implement backoff strategies
- **Real-time Processing**: Optimized for individual embedding generation every 10 seconds

### Storage
- **Vector Compression**: Qdrant supports vector quantization for storage optimization
- **Collection Sharding**: For large datasets, consider collection sharding by user or time

## Monitoring

### Health Checks
- **Service Health**: `/api/v1/memory/health` endpoint
- **Collection Stats**: `/api/v1/memory/stats/collection` endpoint
- **Logging**: Comprehensive logging throughout the service

### Metrics to Monitor
- Search response times
- Embedding generation latency
- Collection size and growth
- Error rates and types

## Security Considerations

### API Key Management
- Store API keys securely in environment variables
- Rotate keys regularly
- Use different keys for development and production

### Data Privacy
- User data isolation through user_id filtering
- Consider encryption for sensitive metadata
- Implement proper access controls

### Rate Limiting
- Implement rate limiting for embedding generation
- Monitor API usage and costs
- Set up alerts for unusual usage patterns

## Troubleshooting

### Common Issues

1. **Qdrant Connection Failed**
   - Check if Qdrant is running on the correct port
   - Verify network connectivity
   - Check firewall settings

2. **Embedding Generation Failed**
   - Verify OpenAI API key is valid
   - Check API rate limits
   - Ensure sufficient API credits

3. **Search Returns No Results**
   - Lower the score threshold
   - Check if memories exist for the user
   - Verify search query format

### Debug Mode
Enable debug logging by setting `DEBUG=True` in environment variables.

## Future Enhancements

1. **Multi-modal Embeddings**: Support for image and audio embeddings
2. **Advanced Filtering**: More sophisticated filtering options
3. **Caching Layer**: Redis-based caching for embeddings and search results
4. **Analytics Dashboard**: Web interface for monitoring and analytics
5. **Backup & Recovery**: Automated backup and restore procedures 