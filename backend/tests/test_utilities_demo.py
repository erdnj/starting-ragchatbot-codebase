import pytest
from test_utils import MockRAGSystemBuilder, TestDataGenerator, APITestHelpers


class TestUtilitiesDemo:
    """Demo tests to show utility classes work correctly"""
    
    def test_mock_rag_system_builder(self):
        """Test MockRAGSystemBuilder functionality"""
        # Test default builder
        rag = MockRAGSystemBuilder().build()
        assert rag.query.return_value == ("Default response", [{"text": "Default source", "link": None}])
        
        # Test with custom courses
        courses = ["Math 101", "Physics 201"]
        rag = MockRAGSystemBuilder().with_courses(courses).build()
        analytics = rag.get_course_analytics()
        assert analytics["total_courses"] == 2
        assert analytics["course_titles"] == courses
        
        # Test with custom query response
        rag = MockRAGSystemBuilder().with_query_response(
            "Custom answer",
            [{"text": "Custom source", "link": "http://test.com"}]
        ).build()
        answer, sources = rag.query("test")
        assert answer == "Custom answer"
        assert sources[0]["link"] == "http://test.com"
    
    def test_test_data_generator(self):
        """Test TestDataGenerator functionality"""
        # Test sample documents
        docs = TestDataGenerator.sample_documents(3)
        assert len(docs) == 3
        assert all("content" in doc for doc in docs)
        assert all("metadata" in doc for doc in docs)
        
        # Test course analytics
        analytics = TestDataGenerator.sample_course_analytics(5)
        assert analytics["total_courses"] == 5
        assert len(analytics["course_titles"]) == 5
        
        # Test query sources
        sources = TestDataGenerator.sample_query_sources(2)
        assert len(sources) == 2
        assert sources[0]["link"] is not None  # Even index has link
        assert sources[1]["link"] is None      # Odd index has no link
        
        # Test large text content
        large_text = TestDataGenerator.large_text_content(5)  # 5KB
        assert len(large_text) == 5 * 1024
    
    def test_api_test_helpers(self):
        """Test APITestHelpers functionality"""
        # Test query response validation
        valid_response = {
            "answer": "Test answer",
            "sources": [{"text": "Source 1"}],
            "session_id": "session-123"
        }
        APITestHelpers.assert_valid_query_response(valid_response)
        
        # Test course stats validation
        valid_stats = {
            "total_courses": 3,
            "course_titles": ["Course 1", "Course 2", "Course 3"]
        }
        APITestHelpers.assert_valid_course_stats(valid_stats)
        
        # Test session response validation
        valid_session = {"session_id": "test-session"}
        APITestHelpers.assert_valid_session_response(valid_session)
        
        # Test query request creation
        request = APITestHelpers.create_test_query_request("test query", "session-1")
        assert request["query"] == "test query"
        assert request["session_id"] == "session-1"
        
        request_no_session = APITestHelpers.create_test_query_request("test")
        assert "session_id" not in request_no_session
    
    def test_mock_chromadb_collection(self):
        """Test MockChromaDBCollection functionality"""
        from test_utils import MockChromaDBCollection
        
        collection = MockChromaDBCollection()
        
        # Test initial state
        assert collection.count() == 0
        
        # Test adding documents
        collection.add(
            documents=["Doc 1", "Doc 2"],
            metadatas=[{"source": "file1.txt"}, {"source": "file2.txt"}],
            ids=["id1", "id2"]
        )
        assert collection.count() == 2
        
        # Test querying
        results = collection.query(query_texts=["test"], n_results=10)
        assert len(results["documents"][0]) == 2
        assert len(results["metadatas"][0]) == 2
        
        # Test deletion
        collection.delete(ids=["id1"])
        assert collection.count() == 1
    
    def test_error_handling_in_helpers(self):
        """Test that helpers properly handle invalid data"""
        # Invalid query response should raise assertion error
        invalid_response = {"answer": "test"}  # Missing sources and session_id
        
        with pytest.raises(AssertionError):
            APITestHelpers.assert_valid_query_response(invalid_response)
        
        # Invalid course stats
        invalid_stats = {"total_courses": 2, "course_titles": ["Only one"]}  # Mismatch
        
        with pytest.raises(AssertionError):
            APITestHelpers.assert_valid_course_stats(invalid_stats)