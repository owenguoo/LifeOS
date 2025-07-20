# LifeOS Web Service Deployment

## Overview

This deployment guide covers deploying the **web-only** LifeOS service to Railway. The video ingestion and processing components run separately from this web service.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Railway Web    │    │  Local Video    │
│   (Next.js)     │◄──►│  API Service    │◄──►│  Processing     │
│                 │    │                 │    │  (OpenCV)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  External APIs  │
                       │  (Qdrant, S3,   │
                       │   TwelveLabs)   │
                       └─────────────────┘
```

## What's Included in Web Service

### ✅ Available Endpoints
- **Authentication**: `/api/v1/auth/*`
- **Memory Search**: `/api/v1/memory/*`
- **Video Management**: `/api/v1/videos/*`
- **Insights**: `/api/v1/insights/*`
- **Highlights**: `/api/v1/highlights/*`
- **Health Check**: `/health`

### ❌ Not Included (Runs Separately)
- Real-time video ingestion
- Video processing with OpenCV
- Audio processing with PyAudio
- System management endpoints

## Railway Deployment

### 1. Environment Variables

Set these in Railway dashboard:

```
# Required
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET=your_s3_bucket_name
TWELVELABS_API_KEY=your_twelvelabs_api_key
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_secure_jwt_secret

# Vector Database
QDRANT_URL=https://your-qdrant-instance.com:6333
QDRANT_API_KEY=your_qdrant_api_key

# App Settings
DEBUG=False
ENVIRONMENT=production
```

### 2. Deployment Process

Railway will:
1. Use `Dockerfile` to build container
2. Install dependencies from `requirements-web.txt` (no OpenCV/PyAudio)
3. Start `app.web_app:app` (web-only FastAPI)

### 3. Verify Deployment

Test these endpoints:
```bash
# Health check
curl https://your-app.railway.app/health

# Root endpoint
curl https://your-app.railway.app/

# API docs
curl https://your-app.railway.app/docs
```

## Video Processing Workflow

Since video processing runs separately:

1. **Upload videos** via web API endpoints
2. **Process locally** using the full server with OpenCV
3. **Store results** in S3 and Qdrant
4. **Access via web API** for your frontend

### Local Video Processing

```bash
# Install full dependencies
pip install -r requirements.txt

# Start video processing
python main.py both

# Or start individual components
python main.py ingestion  # Start video ingestion
python main.py workers    # Start video processing workers
```

## File Structure

```
server/
├── app/
│   ├── web_app.py              # Web-only FastAPI app
│   ├── api/v1/
│   │   ├── web_router.py       # Web-only router
│   │   └── endpoints/          # All API endpoints
│   └── ...
├── requirements-web.txt         # Web-only dependencies
├── requirements.txt            # Full dependencies (local)
├── Dockerfile                  # Uses web-only setup
└── main.py                     # Full server (local only)
```

## Benefits

- ✅ **Fast deployment** (no OpenCV build issues)
- ✅ **Scalable web API** (Railway handles scaling)
- ✅ **Full functionality** (all web endpoints available)
- ✅ **Separate concerns** (web API vs video processing)
- ✅ **Cost effective** (web service is lightweight)

## Next Steps

1. **Deploy web service** to Railway
2. **Set up external services** (Qdrant Cloud, S3)
3. **Test all endpoints** with your frontend
4. **Set up local video processing** for development
5. **Configure frontend** to use Railway URL

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure using `app.web_app:app`
2. **Missing dependencies**: Check `requirements-web.txt`
3. **Environment variables**: Verify all are set in Railway
4. **Qdrant connection**: Ensure `QDRANT_URL` is correct

### Debugging

1. Check Railway logs for detailed errors
2. Test `/health` endpoint for service status
3. Verify environment variables are loaded
4. Test individual API endpoints

## Support

- Railway: [docs.railway.app](https://docs.railway.app)
- Qdrant Cloud: [cloud.qdrant.io](https://cloud.qdrant.io)
- AWS S3: [aws.amazon.com/s3](https://aws.amazon.com/s3) 