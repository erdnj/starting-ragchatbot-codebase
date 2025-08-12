# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Course Materials RAG (Retrieval-Augmented Generation) System that enables semantic search and AI-powered Q&A over course content. It uses FastAPI for the backend, ChromaDB for vector storage, and Anthropic's Claude Sonnet 4 for response generation.

## Development Commands

### Start the Application
```bash
# Quick start with shell script
./run.sh

# Or manually
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Install Dependencies
```bash
# Install/sync dependencies using uv
uv sync

# Add new dependency
uv add <package-name>
```

### Code Quality
```bash
# Format code with black
./scripts/format.sh

# Run all quality checks (formatting, tests)
./scripts/check.sh

# Set up pre-commit hook (auto-format before commits)
cp scripts/pre-commit.sh .git/hooks/pre-commit

# Manual formatting commands
uv run black backend/                    # Format all Python files
uv run black backend/ --check           # Check formatting without changes
uv run black backend/ --check --diff    # Show formatting differences
```

### Environment Setup
Create a `.env` file in the root directory with:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Architecture

### Core Components

1. **RAG Pipeline** (`backend/rag_system.py`)
   - Orchestrates document processing, vector storage, and AI generation
   - Main entry point for RAG functionality

2. **Vector Storage** (`backend/vector_store.py`)
   - ChromaDB integration for semantic search
   - Uses all-MiniLM-L6-v2 embeddings via sentence-transformers

3. **AI Generation** (`backend/ai_generator.py`)  
   - Anthropic Claude API integration
   - Uses claude-3-5-sonnet-20241022 model

4. **API Layer** (`backend/app.py`)
   - FastAPI endpoints: `/ask`, `/initialize`, `/clear`, `/courses`
   - CORS enabled for frontend communication
   - Static file serving for frontend

5. **Document Processing** (`backend/document_processor.py`)
   - Chunks course materials into 500-character segments
   - Maintains metadata for source tracking

### Data Flow

1. Course materials in `docs/` are processed and chunked
2. Chunks are embedded and stored in ChromaDB
3. User queries trigger semantic search for relevant chunks
4. Retrieved context is sent to Claude for response generation
5. Responses maintain conversation history via session management

### Frontend

Single-page application in `frontend/` with:
- Chat interface for Q&A
- Course statistics display
- Session management
- Real-time response streaming indication

## Key Configuration

- **Python**: 3.13+ required
- **Package Manager**: uv (modern Python tooling)
- **Vector DB**: ChromaDB with persistent storage
- **AI Model**: Claude 3.5 Sonnet via Anthropic API
- **Embedding Model**: all-MiniLM-L6-v2
- **Server**: Uvicorn with hot-reload for development

## Important Notes

- No test suite currently exists
- Uses modern pyproject.toml instead of requirements.txt
- ChromaDB data persists in `chromadb_data/` directory
- Frontend served directly from FastAPI (no separate build process)
- CORS configured for development (allows all origins)