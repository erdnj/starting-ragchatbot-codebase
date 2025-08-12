import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any, Optional
import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Mock configuration object"""
    config = MagicMock()
    config.anthropic_api_key = "test-api-key"
    config.model_name = "test-model"
    config.chunk_size = 500
    config.chunk_overlap = 50
    config.chromadb_path = "test_chromadb"
    return config


@pytest.fixture
def mock_rag_system():
    """Mock RAG system for API testing"""
    rag_system = Mock()
    
    # Mock query method
    rag_system.query = Mock(return_value=(
        "This is a test response about Python programming.",
        [
            {"text": "Source 1: Python basics", "link": None},
            {"text": "Source 2: Advanced Python", "link": "http://example.com/python"}
        ]
    ))
    
    # Mock analytics method
    rag_system.get_course_analytics = Mock(return_value={
        "total_courses": 5,
        "course_titles": ["Python 101", "Data Science", "Web Development", "Machine Learning", "Database Systems"]
    })
    
    # Mock session manager
    rag_system.session_manager = Mock()
    rag_system.session_manager.create_session = Mock(return_value="test-session-123")
    rag_system.session_manager.clear_session = Mock()
    
    # Mock add_course_folder
    rag_system.add_course_folder = Mock(return_value=(3, 150))
    
    return rag_system


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing"""
    vector_store = Mock()
    
    # Mock search results
    vector_store.search = Mock(return_value=[
        {
            "content": "Python is a high-level programming language.",
            "metadata": {"source": "python_basics.txt", "chunk_index": 0}
        },
        {
            "content": "Python supports multiple programming paradigms.",
            "metadata": {"source": "python_advanced.txt", "chunk_index": 5}
        }
    ])
    
    # Mock add_documents
    vector_store.add_documents = Mock()
    
    # Mock clear
    vector_store.clear = Mock()
    
    # Mock get_collection_stats
    vector_store.get_collection_stats = Mock(return_value={
        "total_documents": 150,
        "total_chunks": 150
    })
    
    return vector_store


@pytest.fixture
def mock_ai_generator():
    """Mock AI generator for testing"""
    ai_generator = Mock()
    
    # Mock generate_response
    ai_generator.generate_response = Mock(
        return_value="Based on the course materials, Python is a versatile programming language."
    )
    
    return ai_generator


@pytest.fixture
def mock_document_processor():
    """Mock document processor for testing"""
    processor = Mock()
    
    # Mock process_folder
    processor.process_folder = Mock(return_value=[
        {
            "content": "Chapter 1: Introduction to Python",
            "metadata": {"source": "python_course.txt", "chunk_index": 0}
        },
        {
            "content": "Chapter 2: Variables and Data Types",
            "metadata": {"source": "python_course.txt", "chunk_index": 1}
        }
    ])
    
    # Mock process_file
    processor.process_file = Mock(return_value=[
        {
            "content": "Test content",
            "metadata": {"source": "test.txt", "chunk_index": 0}
        }
    ])
    
    return processor


@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing"""
    manager = Mock()
    
    # Session storage
    manager.sessions = {}
    
    # Mock methods
    manager.create_session = Mock(return_value="session-456")
    manager.get_session = Mock(return_value=[])
    manager.add_to_session = Mock()
    manager.clear_session = Mock()
    manager.get_conversation_history = Mock(return_value="")
    
    return manager


@pytest.fixture
def sample_query_request():
    """Sample query request data"""
    return {
        "query": "What is Python programming?",
        "session_id": "test-session-123"
    }


@pytest.fixture
def sample_course_documents():
    """Sample course documents for testing"""
    return [
        {
            "content": "Python is a high-level, interpreted programming language.",
            "metadata": {
                "source": "python_basics.txt",
                "chunk_index": 0,
                "course": "Python Fundamentals"
            }
        },
        {
            "content": "Python supports object-oriented, procedural, and functional programming.",
            "metadata": {
                "source": "python_paradigms.txt",
                "chunk_index": 0,
                "course": "Advanced Python"
            }
        },
        {
            "content": "Data science with Python involves libraries like pandas, numpy, and scikit-learn.",
            "metadata": {
                "source": "data_science.txt",
                "chunk_index": 0,
                "course": "Data Science"
            }
        }
    ]


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing"""
    with patch('backend.ai_generator.anthropic.Anthropic') as mock_anthropic:
        client = Mock()
        mock_anthropic.return_value = client
        
        # Mock message response
        message_response = Mock()
        message_response.content = [Mock(text="Test AI response")]
        message_response.stop_reason = "end_turn"
        
        client.messages.create = Mock(return_value=message_response)
        
        yield client


@pytest.fixture
def mock_chromadb_client():
    """Mock ChromaDB client for testing"""
    with patch('backend.vector_store.chromadb.PersistentClient') as mock_chromadb:
        client = Mock()
        collection = Mock()
        
        # Setup collection mock
        collection.query = Mock(return_value={
            'documents': [["Doc 1", "Doc 2"]],
            'metadatas': [[{"source": "test1.txt"}, {"source": "test2.txt"}]],
            'distances': [[0.1, 0.2]]
        })
        collection.add = Mock()
        collection.delete = Mock()
        collection.count = Mock(return_value=10)
        
        client.get_or_create_collection = Mock(return_value=collection)
        mock_chromadb.return_value = client
        
        yield client, collection


@pytest.fixture
def test_app_client():
    """Create a test client for FastAPI app without static files"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.testclient import TestClient
    from pydantic import BaseModel
    from typing import List, Optional, Union
    
    # Create test app without static files
    app = FastAPI(title="Test RAG System")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Define models
    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None
    
    class SourceInfo(BaseModel):
        text: str
        link: Optional[str] = None
    
    class QueryResponse(BaseModel):
        answer: str
        sources: List[Union[str, SourceInfo]]
        session_id: str
    
    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]
    
    # Mock RAG system
    mock_rag = Mock()
    mock_rag.query = Mock(return_value=(
        "Test response",
        [{"text": "Source 1", "link": None}]
    ))
    mock_rag.get_course_analytics = Mock(return_value={
        "total_courses": 3,
        "course_titles": ["Course 1", "Course 2", "Course 3"]
    })
    mock_rag.session_manager = Mock()
    mock_rag.session_manager.create_session = Mock(return_value="test-session")
    mock_rag.session_manager.clear_session = Mock()
    
    # Define endpoints
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id or mock_rag.session_manager.create_session()
            answer, sources = mock_rag.query(request.query, session_id)
            
            formatted_sources = []
            for source in sources:
                if isinstance(source, dict):
                    formatted_sources.append(SourceInfo(
                        text=source.get("text", ""),
                        link=source.get("link")
                    ))
                else:
                    formatted_sources.append(source)
            
            return QueryResponse(
                answer=answer,
                sources=formatted_sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/session/clear")
    async def clear_session(session_id: Optional[str] = None):
        try:
            if session_id:
                mock_rag.session_manager.clear_session(session_id)
            new_session_id = mock_rag.session_manager.create_session()
            return {"session_id": new_session_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/")
    async def root():
        return {"message": "RAG System API", "version": "1.0.0"}
    
    # Store mock for test access
    app.mock_rag = mock_rag
    
    return TestClient(app)


@pytest.fixture
def cleanup_test_chromadb():
    """Cleanup test ChromaDB after tests"""
    yield
    # Cleanup test ChromaDB directory if it exists
    import shutil
    test_db_path = "test_chromadb"
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)