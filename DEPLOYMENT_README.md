# Python Chatbot Backend - Deployment Guide

## Environment Variables Required

Set these environment variables in your deployment platform:

```
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://username:password@host:port/database_name?sslmode=require
LOCAL_EMBED_MODEL=all-MiniLM-L6-v2
```

## Render Deployment

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn new_main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3

## API Endpoints

- `GET /health` - Health check
- `POST /chat` - Chat with the AI
- `POST /risk-assessment` - Risk assessment
- `GET /knowledge-stats` - Knowledge base statistics
- `POST /retrain` - Retrain from uploads

## Features

- FastAPI backend with Gemini AI integration
- PostgreSQL database with pgvector for embeddings
- PDF processing and text extraction
- Risk assessment capabilities
- Knowledge base management
