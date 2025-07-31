#!/bin/bash
"""
Performance Test Runner Script
Runs performance tests in different environments
"""

set -e  # Exit on any error

echo "🎬 Video Processing Performance Test Runner"
echo "============================================="

# Check if we're in Docker
if [ -f /.dockerenv ]; then
    echo "🐳 Running in Docker container"
    ENVIRONMENT="docker"
else
    echo "💻 Running on host system"
    ENVIRONMENT="host"
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required"
    exit 1
fi

# Check API key
if [ -z "$TWELVELABS_API_KEY" ]; then
    echo "❌ TWELVELABS_API_KEY environment variable is required"
    echo "   export TWELVELABS_API_KEY='your_api_key_here'"
    exit 1
fi

# Check Redis connection
echo "📡 Checking Redis connection..."
if [ "$ENVIRONMENT" = "docker" ]; then
    REDIS_HOST=${REDIS_HOST:-redis}
    REDIS_PORT=${REDIS_PORT:-6379}
else
    REDIS_HOST=${REDIS_HOST:-localhost}
    REDIS_PORT=${REDIS_PORT:-6379}
fi

# Test Redis connection
python3 -c "
import redis
try:
    r = redis.Redis(host='$REDIS_HOST', port=$REDIS_PORT, db=0)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    print('   Make sure Redis is running')
    if '$ENVIRONMENT' == 'host':
        print('   Start Redis: redis-server')
        print('   Or with Docker: docker run -d -p 6379:6379 redis:alpine')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Determine which test to run
TEST_TYPE=${1:-quick}

case $TEST_TYPE in
    "quick")
        echo "🚀 Running Quick Performance Test..."
        python3 quick_performance_test.py
        ;;
    "full")
        echo "🚀 Running Full Performance Test Suite..."
        python3 performance_test.py
        ;;
    "docker")
        echo "🐳 Running Docker-specific Performance Test..."
        python3 docker_performance_test.py
        ;;
    *)
        echo "Usage: $0 [quick|full|docker]"
        echo ""
        echo "Test Types:"
        echo "  quick  - Quick performance comparison (default)"
        echo "  full   - Comprehensive test suite with detailed analysis"
        echo "  docker - Docker-optimized test"
        echo ""
        echo "Examples:"
        echo "  $0              # Run quick test"
        echo "  $0 quick        # Run quick test"
        echo "  $0 full         # Run full test suite"
        echo "  $0 docker       # Run Docker test"
        exit 1
        ;;
esac

echo ""
echo "✅ Performance test completed!"