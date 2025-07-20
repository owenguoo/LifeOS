#!/usr/bin/env python3
"""
Test script for Qdrant integration
Run this script to test the vector store functionality
"""

import asyncio
import httpx
import json
from datetime import datetime
from uuid import uuid4

# Test data
TEST_MEMORIES = [
    {
        "content": "I had a great conversation with John about machine learning and AI ethics today.",
        "content_type": "text",
        "metadata": {"location": "office", "duration": "30 minutes"},
        "tags": ["conversation", "machine-learning", "ethics"],
        "source_id": "meeting-001"
    },
    {
        "content": "Watched an interesting documentary about space exploration and Mars missions.",
        "content_type": "video",
        "metadata": {"duration": "120 minutes", "platform": "Netflix"},
        "tags": ["space", "documentary", "mars"],
        "source_id": "video-001"
    },
    {
        "content": "Learned about vector databases and their applications in semantic search.",
        "content_type": "text",
        "metadata": {"source": "online course", "topic": "databases"},
        "tags": ["learning", "vector-databases", "semantic-search"],
        "source_id": "course-001"
    }
]

BASE_URL = "http://localhost:8000/api/v1"


async def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/memory/health")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed: {health_data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False


async def test_create_multiple_memories():
    """Test creating multiple memories individually"""
    print("📝 Testing individual memory creation...")
    
    memory_ids = []
    async with httpx.AsyncClient() as client:
        for i, memory_data in enumerate(TEST_MEMORIES):
            print(f"  Creating memory {i+1}/{len(TEST_MEMORIES)}...")
            
            response = await client.post(
                f"{BASE_URL}/memory/create",
                json=memory_data
            )
            
            if response.status_code == 200:
                result = response.json()
                memory_ids.append(result['id'])
                print(f"    ✅ Created: {result['id']}")
            else:
                print(f"    ❌ Failed: {response.status_code} - {response.text}")
    
    print(f"✅ Created {len(memory_ids)} memories individually")
    return memory_ids


async def test_search_memories():
    """Test memory search functionality"""
    print("🔍 Testing memory search...")
    
    search_queries = [
        "machine learning",
        "space exploration",
        "vector databases",
        "conversation with John"
    ]
    
    async with httpx.AsyncClient() as client:
        for query in search_queries:
            print(f"  Searching for: '{query}'")
            
            response = await client.post(
                f"{BASE_URL}/memory/search",
                json={
                    "query": query,
                    "limit": 5,
                    "score_threshold": 0.01
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"    Found {result['total_found']} results in {result['search_time_ms']:.2f}ms")
                
                for i, memory in enumerate(result['results'][:2]):  # Show first 2 results
                    print(f"    {i+1}. {memory['content'][:80]}... (score: {memory['score']:.3f})")
            else:
                print(f"    ❌ Search failed: {response.status_code}")


async def test_collection_stats():
    """Test getting collection statistics"""
    print("📊 Testing collection statistics...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/memory/stats/collection")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Collection stats: {stats}")
        else:
            print(f"❌ Failed to get stats: {response.status_code}")


async def main():
    """Run all tests"""
    print("🚀 Starting Qdrant Integration Tests")
    print("=" * 50)
    
    # Test health check
    if not await test_health_check():
        print("❌ Health check failed, stopping tests")
        return
    
    print()
    
    # Test individual memory creation
    memory_ids = await test_create_multiple_memories()
    
    print()
    
    # Test search
    await test_search_memories()
    
    print()
    
    # Test stats
    await test_collection_stats()
    
    print()
    print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main()) 