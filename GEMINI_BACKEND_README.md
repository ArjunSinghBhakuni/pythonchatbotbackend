# Gemini AI Backend

This is the new backend implementation using Google's Gemini AI APIs instead of Ollama and Mistral.

## Features

- **Gemini Embeddings**: Uses Google's `embedding-001` model for vector embeddings
- **Gemini Chat**: Uses `gemini-1.5-flash` model for AI responses
- **PDF Processing**: Automatically processes PDFs and deletes them after storing in database
- **No Sources Display**: Frontend no longer shows source citations
- **Auto Table Management**: Drops and recreates database tables on startup

## Setup

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   Create a `.env` file with:

   ```
   GEMINI_API_KEY=AIzaSyCk1XOPzJ8tTBTczHPhILjjEtzjAuGKLq4
   DATABASE_URL=your_database_url_here
   ```

3. **Run the Backend**:
   ```bash
   python run_gemini_backend.py
   ```

## API Endpoints

- `GET /health` - Health check
- `POST /chat` - Chat with AI (no sources returned)
- `POST /risk-assessment` - Risk assessment (no sources returned)
- `POST /upload-pdf` - Upload and process PDF (file deleted after processing)
- `GET /knowledge-stats` - Get knowledge base statistics
- `POST /retrain` - Retrain from uploads folder

## Key Changes from Previous Version

1. **No Ollama/Mistral**: Completely replaced with Gemini APIs
2. **PDF Auto-Delete**: PDFs are automatically deleted after processing
3. **No Sources**: API responses no longer include source citations
4. **Table Management**: Database tables are dropped and recreated on startup
5. **768-Dimensional Embeddings**: Updated for Gemini's embedding dimensions

## Testing

Run the test script to verify everything works:

```bash
python test_gemini_backend.py
```

## Frontend Updates

The frontend has been updated to:

- Remove source display from chat responses
- Remove source display from risk assessment results
- Work with the new API response format

## Database Schema

The embeddings table now uses 768-dimensional vectors (Gemini's embedding size):

```sql
CREATE TABLE embeddings (
    id BIGSERIAL PRIMARY KEY,
    session_name TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    created_at TIMESTAMP DEFAULT NOW()
);
```




