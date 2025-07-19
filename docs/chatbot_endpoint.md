# Chatbot Endpoint Documentation

## Overview

The chatbot endpoint (`POST /api/v1/memory/chatbot`) is designed to handle natural language queries from users and return relevant video information. It uses OpenAI to refine user input into better search queries, then finds the most relevant video using vector similarity search.

## Endpoint Details

- **URL**: `POST /api/v1/memory/chatbot`
- **Content-Type**: `application/json`
- **Authentication**: Currently uses demo user ID (will be replaced with proper auth)

## Request Schema

```json
{
  "user_input": "What was I doing yesterday?",
  "confidence_threshold": 0.7
}
```

### Fields

- `user_input` (string, required): The user's question or input
- `confidence_threshold` (float, optional): Minimum confidence score for video match (default: 0.7, range: 0.0-1.0)

## Response Schema

### Success Response (Video Found)

```json
{
  "original_input": "What was I doing yesterday?",
  "refined_query": "yesterday activities",
  "video_found": true,
  "video_id": "video_123",
  "timestamp": "2024-01-01T12:00:00",
  "summary": "User was working on computer and cooking dinner",
  "confidence_score": 0.85,
  "processing_time_ms": 245.67
}
```

### Success Response (No Video Found)

```json
{
  "original_input": "What was I doing last year?",
  "refined_query": "last year activities",
  "video_found": false,
  "video_id": null,
  "timestamp": null,
  "summary": null,
  "confidence_score": null,
  "processing_time_ms": 156.23
}
```

## How It Works

1. **Query Refinement**: Uses OpenAI GPT-3.5-turbo to convert user input into a better search query
2. **Embedding Generation**: Converts the refined query into a vector embedding
3. **Vector Search**: Searches the vector database for the most similar video
4. **Data Enrichment**: Fetches detailed video information from Supabase
5. **Response**: Returns the video summary, timestamp, and confidence score

## Example Usage

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/memory/chatbot" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Show me when I was cooking",
    "confidence_threshold": 0.8
  }'
```

### Python Example

```python
import requests

url = "http://localhost:8000/api/v1/memory/chatbot"
data = {
    "user_input": "What was I doing yesterday?",
    "confidence_threshold": 0.7
}

response = requests.post(url, json=data)
result = response.json()

if result["video_found"]:
    print(f"Found video: {result['summary']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"Confidence: {result['confidence_score']}")
else:
    print("No matching video found")
```

## Error Handling

- **400 Bad Request**: Invalid request format
- **500 Internal Server Error**: Service failures (OpenAI, embedding, vector search, etc.)

## Configuration Requirements

- `OPENAI_API_KEY`: Required for query refinement
- Vector database (Qdrant) must be running
- Supabase connection must be configured
- Text embedding service must be available

## Performance Notes

- Typical response time: 200-500ms
- OpenAI API calls add ~100-200ms
- Vector search is typically very fast (<50ms)
- Supabase queries are typically fast (<100ms)

## Testing

Run the test suite:

```bash
cd server
pytest tests/test_chatbot.py -v
```

## Health Check

Check if all required services are healthy:

```bash
curl "http://localhost:8000/api/v1/memory/health"
```

This will return the status of:
- Vector store
- Video embedding service
- Text embedding service
- OpenAI service 