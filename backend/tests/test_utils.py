import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any
import tempfile
import os
import json


class MockRAGSystemBuilder:
    """Builder class for creating mock RAG systems with various configurations"""
    
    def __init__(self):
        self.rag_system = Mock()
        self._setup_defaults()
    
    def _setup_defaults(self):
        """Setup default mock behaviors"""
        # Default query response
        self.rag_system.query.return_value = (
            "Default response",
            [{"text": "Default source", "link": None}]
        )
        
        # Default analytics
        self.rag_system.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": ["Default Course"]
        }
        
        # Default session manager
        self.rag_system.session_manager = Mock()
        self.rag_system.session_manager.create_session.return_value = "default-session"
        self.rag_system.session_manager.clear_session = Mock()
        self.rag_system.session_manager.get_conversation_history.return_value = ""
        
        # Default folder processing
        self.rag_system.add_course_folder.return_value = (1, 10)
    
    def with_courses(self, course_titles: List[str]):
        """Configure mock with specific courses"""
        self.rag_system.get_course_analytics.return_value = {
            "total_courses": len(course_titles),
            "course_titles": course_titles
        }
        return self
    
    def with_query_response(self, answer: str, sources: List[Dict]):
        """Configure mock with specific query response"""
        self.rag_system.query.return_value = (answer, sources)
        return self
    
    def with_error(self, method_name: str, error: Exception):
        """Configure mock to raise error for specific method"""
        getattr(self.rag_system, method_name).side_effect = error
        return self
    
    def with_session_id(self, session_id: str):
        """Configure mock to return specific session ID"""
        self.rag_system.session_manager.create_session.return_value = session_id
        return self
    
    def build(self):
        """Return the configured mock RAG system"""
        return self.rag_system


class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def sample_documents(count: int = 3) -> List[Dict]:
        """Generate sample document chunks"""
        return [
            {
                "content": f"This is document {i+1} content about testing.",
                "metadata": {
                    "source": f"test_doc_{i+1}.txt",
                    "chunk_index": 0,
                    "course": f"Test Course {i+1}"
                }
            }
            for i in range(count)
        ]
    
    @staticmethod
    def sample_course_analytics(num_courses: int = 5) -> Dict[str, Any]:
        """Generate sample course analytics"""
        return {
            "total_courses": num_courses,
            "course_titles": [f"Course {i+1}" for i in range(num_courses)],
            "total_documents": num_courses * 10,
            "total_chunks": num_courses * 50
        }
    
    @staticmethod
    def sample_query_sources(count: int = 3) -> List[Dict]:
        """Generate sample query sources"""
        sources = []
        for i in range(count):
            sources.append({
                "text": f"Source {i+1}: This is relevant content for the query.",
                "link": f"http://example.com/source{i+1}" if i % 2 == 0 else None
            })
        return sources
    
    @staticmethod
    def large_text_content(size_kb: int = 10) -> str:
        """Generate large text content for testing"""
        # Generate approximately size_kb KB of text
        words = ["test", "content", "sample", "data", "large", "text", "chunk"]
        target_chars = size_kb * 1024
        content = ""
        
        while len(content) < target_chars:
            content += " ".join(words) + " "
        
        return content[:target_chars]
    
    @staticmethod
    def create_temp_course_files(num_files: int = 3) -> str:
        """Create temporary course files for testing"""
        temp_dir = tempfile.mkdtemp(prefix="test_courses_")
        
        for i in range(num_files):
            file_path = os.path.join(temp_dir, f"course_{i+1}.txt")
            content = f"""
Course {i+1}: Introduction to Topic {i+1}

Chapter 1: Basics
This chapter covers the fundamental concepts of topic {i+1}.

Chapter 2: Advanced Concepts
This chapter covers advanced material for topic {i+1}.

Chapter 3: Practical Applications
Real-world applications and examples for topic {i+1}.
            """.strip()
            
            with open(file_path, 'w') as f:
                f.write(content)
        
        return temp_dir
    
    @staticmethod
    def cleanup_temp_dir(temp_dir: str):
        """Clean up temporary directory"""
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


class MockChromaDBCollection:
    """Mock ChromaDB collection for testing"""
    
    def __init__(self):
        self.documents = []
        self.metadatas = []
        self.ids = []
        self.embeddings = []
        self._id_counter = 0
    
    def add(self, documents, metadatas=None, ids=None, embeddings=None):
        """Mock add documents"""
        if not isinstance(documents, list):
            documents = [documents]
        
        for i, doc in enumerate(documents):
            self.documents.append(doc)
            self.metadatas.append(metadatas[i] if metadatas else {})
            self.ids.append(ids[i] if ids else f"id_{self._id_counter}")
            self.embeddings.append(embeddings[i] if embeddings else [0.1] * 384)
            self._id_counter += 1
    
    def query(self, query_texts=None, query_embeddings=None, n_results=10, **kwargs):
        """Mock query documents"""
        # Return first n_results documents
        results_count = min(n_results, len(self.documents))
        
        return {
            'documents': [self.documents[:results_count]],
            'metadatas': [self.metadatas[:results_count]],
            'ids': [self.ids[:results_count]],
            'distances': [[0.1 * i for i in range(results_count)]]
        }
    
    def count(self):
        """Mock document count"""
        return len(self.documents)
    
    def delete(self, ids=None, where=None):
        """Mock delete documents"""
        if ids:
            for id_to_delete in ids:
                try:
                    idx = self.ids.index(id_to_delete)
                    self.documents.pop(idx)
                    self.metadatas.pop(idx)
                    self.ids.pop(idx)
                    self.embeddings.pop(idx)
                except ValueError:
                    pass  # ID not found


class APITestHelpers:
    """Helper functions for API testing"""
    
    @staticmethod
    def assert_valid_query_response(response_data: Dict[str, Any]):
        """Assert that query response has valid structure"""
        assert "answer" in response_data
        assert "sources" in response_data
        assert "session_id" in response_data
        assert isinstance(response_data["sources"], list)
        assert isinstance(response_data["answer"], str)
        assert isinstance(response_data["session_id"], str)
    
    @staticmethod
    def assert_valid_course_stats(response_data: Dict[str, Any]):
        """Assert that course stats response has valid structure"""
        assert "total_courses" in response_data
        assert "course_titles" in response_data
        assert isinstance(response_data["total_courses"], int)
        assert isinstance(response_data["course_titles"], list)
        assert response_data["total_courses"] >= 0
        assert len(response_data["course_titles"]) == response_data["total_courses"]
    
    @staticmethod
    def assert_valid_session_response(response_data: Dict[str, Any]):
        """Assert that session response has valid structure"""
        assert "session_id" in response_data
        assert isinstance(response_data["session_id"], str)
        assert len(response_data["session_id"]) > 0
    
    @staticmethod
    def create_test_query_request(query: str, session_id: str = None) -> Dict[str, Any]:
        """Create a test query request"""
        request = {"query": query}
        if session_id:
            request["session_id"] = session_id
        return request
    
    @staticmethod
    def simulate_network_delay():
        """Simulate network delay for testing timeouts"""
        import time
        time.sleep(0.1)  # 100ms delay


class ComponentTestSetup:
    """Setup utilities for component testing"""
    
    @staticmethod
    def mock_embedding_model():
        """Create mock embedding model"""
        with patch('sentence_transformers.SentenceTransformer') as mock_model:
            model_instance = Mock()
            model_instance.encode.return_value = [[0.1] * 384]  # Mock embeddings
            mock_model.return_value = model_instance
            return mock_model, model_instance
    
    @staticmethod
    def mock_anthropic_client():
        """Create mock Anthropic client"""
        with patch('anthropic.Anthropic') as mock_anthropic:
            client = Mock()
            
            # Mock message response
            message_response = Mock()
            message_response.content = [Mock(text="Mock AI response")]
            message_response.stop_reason = "end_turn"
            client.messages.create.return_value = message_response
            
            mock_anthropic.return_value = client
            return mock_anthropic, client
    
    @staticmethod
    def mock_chromadb():
        """Create mock ChromaDB"""
        with patch('chromadb.PersistentClient') as mock_chromadb:
            client = Mock()
            collection = MockChromaDBCollection()
            client.get_or_create_collection.return_value = collection
            mock_chromadb.return_value = client
            return mock_chromadb, client, collection


# Pytest utilities for common test patterns
class TestPatterns:
    """Common test patterns and utilities"""
    
    @staticmethod
    def run_with_timeout(func, timeout_seconds: float = 5.0):
        """Run function with timeout for testing performance"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Function took longer than {timeout_seconds} seconds")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout_seconds))
        
        try:
            result = func()
            signal.alarm(0)  # Cancel alarm
            return result
        except TimeoutError:
            signal.alarm(0)  # Cancel alarm
            raise
    
    @staticmethod
    def assert_performance(func, max_time_seconds: float = 1.0):
        """Assert that function runs within time limit"""
        import time
        start_time = time.time()
        func()
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time <= max_time_seconds, \
            f"Function took {execution_time:.3f}s, expected <= {max_time_seconds}s"
    
    @staticmethod
    def test_error_scenarios(test_func, error_cases: List[tuple]):
        """Test multiple error scenarios"""
        for error_input, expected_error in error_cases:
            with pytest.raises(expected_error):
                test_func(error_input)
    
    @staticmethod
    def parametrize_with_data(data_generator_func):
        """Decorator to parametrize tests with generated data"""
        def decorator(test_func):
            test_data = data_generator_func()
            return pytest.mark.parametrize("test_input", test_data)(test_func)
        return decorator


# Example usage fixtures for complex scenarios
@pytest.fixture
def rag_system_with_errors():
    """RAG system that raises different errors based on input"""
    def create_error_system():
        rag = Mock()
        
        def query_with_conditional_error(query, session_id=None):
            if "error" in query.lower():
                raise Exception("Query processing failed")
            return ("Success response", [{"text": "Source", "link": None}])
        
        rag.query.side_effect = query_with_conditional_error
        return rag
    
    return create_error_system


@pytest.fixture
def performance_test_data():
    """Generate data for performance testing"""
    return {
        "small_query": "test",
        "medium_query": "a" * 100,
        "large_query": "a" * 10000,
        "complex_query": "What is the relationship between " + "complex topic " * 50
    }