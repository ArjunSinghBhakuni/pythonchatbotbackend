# AI Chatbot Backend

A local AI-powered chatbot system that can process PDF documents, generate embeddings, and answer questions using Ollama and pgvector.

## Features

- 📄 **PDF Processing**: Extract text from PDF documents and split into chunks
- 🧠 **Local Embeddings**: Generate embeddings using sentence-transformers
- 🗄️ **Vector Database**: Store embeddings in PostgreSQL with pgvector
- 🤖 **Local LLM**: Generate responses using Ollama (fully local)
- 🔍 **Semantic Search**: Find relevant document chunks using vector similarity
- 💬 **Chat Interface**: Conversational AI with context awareness
- 🌐 **REST API**: FastAPI backend with CORS support for React integration

## Prerequisites

### 1. PostgreSQL with pgvector

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install pgvector extension
sudo apt install postgresql-14-pgvector  # Adjust version as needed

# Or using Docker
docker run --name postgres-pgvector -e POSTGRES_PASSWORD=password -e POSTGRES_DB=ai_chatbot_db -p 5432:5432 -d pgvector/pgvector:pg14
```

### 2. Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model (e.g., llama2)
ollama pull llama2

# Start Ollama service
ollama serve
```

### 3. Python Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Setup

### 1. Database Setup

```bash
# Create database and run setup script
psql -U postgres -c "CREATE DATABASE ai_chatbot_db;"
psql -U postgres -d ai_chatbot_db -f setup_database.sql
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/ai_chatbot_db
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ai_chatbot_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Application Configuration
UPLOAD_DIR=./uploads
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CHUNKS_PER_QUERY=5
```

### 3. Run the Application

```bash
# Start the FastAPI server
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Health Check

- `GET /health` - Check service status

### Document Management

- `POST /upload` - Upload and process PDF documents
- `GET /documents` - List uploaded documents

### Query & Chat

- `POST /query` - Query documents with semantic search
- `POST /chat` - Chat with conversation history
- `GET /ollama/models` - Get available Ollama models

## Usage Examples

### Upload a PDF Document

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "title=My Document"
```

### Query Documents

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main requirements?",
    "max_results": 5
  }'
```

### Chat with Context

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you explain this in simpler terms?",
    "conversation_history": [
      {"role": "user", "content": "What is the DPDP Act?"},
      {"role": "assistant", "content": "The DPDP Act is..."}
    ]
  }'
```

## React Integration

The backend is configured with CORS to work with React applications running on:

- `http://localhost:3000`
- `http://127.0.0.1:3000`

### Example React Component Usage

```javascript
// Upload document
const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("http://localhost:8000/upload", {
    method: "POST",
    body: formData,
  });

  return response.json();
};

// Query documents
const queryDocuments = async (query) => {
  const response = await fetch("http://localhost:8000/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, max_results: 5 }),
  });

  return response.json();
};
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React App     │    │   FastAPI        │    │   PostgreSQL    │
│                 │◄──►│   Backend        │◄──►│   + pgvector    │
│  - Chat UI      │    │                  │    │                 │
│  - File Upload  │    │  - PDF Processing│    │  - Embeddings   │
└─────────────────┘    │  - Embeddings    │    │  - Documents    │
                       │  - API Endpoints │    └─────────────────┘
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │     Ollama       │
                       │                  │
                       │  - Local LLM     │
                       │  - Text Gen      │
                       └──────────────────┘
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**

   - Ensure PostgreSQL is running
   - Check database credentials in `.env`
   - Verify pgvector extension is installed

2. **Ollama Not Available**

   - Start Ollama service: `ollama serve`
   - Check if model is pulled: `ollama list`
   - Verify Ollama URL in configuration

3. **PDF Processing Issues**

   - Ensure PDF is not password-protected
   - Check if PDF contains extractable text
   - Verify file permissions

4. **Memory Issues**
   - Reduce `CHUNK_SIZE` for large documents
   - Use smaller embedding models
   - Increase system RAM

## Development

### Project Structure

```
ai-chatbot-backend/
├── main.py                 # FastAPI application
├── config.py              # Configuration settings
├── database.py            # Database connection and setup
├── models.py              # Pydantic models
├── pdf_processor.py       # PDF text extraction and chunking
├── embedding_service.py   # Embedding generation
├── ollama_service.py      # Ollama LLM integration
├── requirements.txt       # Python dependencies
├── setup_database.sql     # Database setup script
└── README.md             # This file
```

### Adding New Features

1. Add new endpoints in `main.py`
2. Create corresponding models in `models.py`
3. Update database schema if needed
4. Test with the React frontend

## License

This project is open source and available under the MIT License.

