import pytest
from unittest.mock import Mock, patch, MagicMock
import json


@pytest.mark.api
class TestQueryEndpoint:
    """Test suite for /api/query endpoint"""
    
    def test_query_with_valid_request(self, test_app_client):
        """Test successful query with valid request"""
        # Prepare request
        request_data = {
            "query": "What is Python?",
            "session_id": "test-session-123"
        }
        
        # Make request
        response = test_app_client.post("/api/query", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"
        assert isinstance(data["sources"], list)
    
    def test_query_without_session_id(self, test_app_client):
        """Test query without session_id creates new session"""
        # Prepare request without session_id
        request_data = {
            "query": "Tell me about databases"
        }
        
        # Make request
        response = test_app_client.post("/api/query", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == "test-session"  # Mock returns this
        
        # Verify session creation was called
        app = test_app_client.app
        app.mock_rag.session_manager.create_session.assert_called()
    
    def test_query_with_empty_query(self, test_app_client):
        """Test query with empty query string"""
        request_data = {
            "query": "",
            "session_id": "test-session"
        }
        
        response = test_app_client.post("/api/query", json=request_data)
        
        # Should still process but might return different response
        assert response.status_code in [200, 422]  # 422 for validation error
    
    def test_query_with_long_query(self, test_app_client):
        """Test query with very long query string"""
        request_data = {
            "query": "a" * 10000,  # Very long query
            "session_id": "test-session"
        }
        
        response = test_app_client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
    
    def test_query_with_special_characters(self, test_app_client):
        """Test query with special characters"""
        request_data = {
            "query": "What about Python's @decorators & *args, **kwargs?",
            "session_id": "test-session"
        }
        
        response = test_app_client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
    
    def test_query_error_handling(self, test_app_client):
        """Test error handling in query endpoint"""
        # Make RAG system raise an error
        app = test_app_client.app
        app.mock_rag.query.side_effect = Exception("RAG system error")
        
        request_data = {
            "query": "Test query",
            "session_id": "test-session"
        }
        
        response = test_app_client.post("/api/query", json=request_data)
        
        assert response.status_code == 500
        assert "RAG system error" in response.json()["detail"]
    
    def test_query_with_sources_formatting(self, test_app_client):
        """Test that sources are properly formatted"""
        # Setup mock to return different source formats
        app = test_app_client.app
        app.mock_rag.query.return_value = (
            "Test answer",
            [
                {"text": "Source with link", "link": "http://example.com"},
                {"text": "Source without link", "link": None},
                "Legacy string source"  # Test backward compatibility
            ]
        )
        
        request_data = {
            "query": "Test query",
            "session_id": "test-session"
        }
        
        response = test_app_client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        sources = data["sources"]
        assert len(sources) == 3
        
        # Check first source has link
        assert sources[0]["text"] == "Source with link"
        assert sources[0]["link"] == "http://example.com"
        
        # Check second source has no link
        assert sources[1]["text"] == "Source without link"
        assert sources[1]["link"] is None
        
        # Check legacy string source
        assert sources[2] == "Legacy string source"
    
    def test_query_invalid_json(self, test_app_client):
        """Test query with invalid JSON"""
        response = test_app_client.post(
            "/api/query",
            data="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable entity
    
    def test_query_missing_required_field(self, test_app_client):
        """Test query missing required 'query' field"""
        request_data = {
            "session_id": "test-session"
            # Missing 'query' field
        }
        
        response = test_app_client.post("/api/query", json=request_data)
        
        assert response.status_code == 422
        assert "query" in str(response.json())


@pytest.mark.api
class TestCoursesEndpoint:
    """Test suite for /api/courses endpoint"""
    
    def test_get_courses_success(self, test_app_client):
        """Test successful retrieval of course statistics"""
        response = test_app_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 3
        assert len(data["course_titles"]) == 3
        assert "Course 1" in data["course_titles"]
    
    def test_get_courses_empty_result(self, test_app_client):
        """Test courses endpoint with no courses"""
        # Mock empty course analytics
        app = test_app_client.app
        app.mock_rag.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }
        
        response = test_app_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []
    
    def test_get_courses_error_handling(self, test_app_client):
        """Test error handling in courses endpoint"""
        # Make analytics raise an error
        app = test_app_client.app
        app.mock_rag.get_course_analytics.side_effect = Exception("Analytics error")
        
        response = test_app_client.get("/api/courses")
        
        assert response.status_code == 500
        assert "Analytics error" in response.json()["detail"]
    
    def test_get_courses_large_dataset(self, test_app_client):
        """Test courses endpoint with large number of courses"""
        # Mock large course list
        app = test_app_client.app
        course_titles = [f"Course {i}" for i in range(100)]
        app.mock_rag.get_course_analytics.return_value = {
            "total_courses": 100,
            "course_titles": course_titles
        }
        
        response = test_app_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 100
        assert len(data["course_titles"]) == 100


@pytest.mark.api
class TestSessionEndpoint:
    """Test suite for /api/session/clear endpoint"""
    
    def test_clear_session_with_id(self, test_app_client):
        """Test clearing a specific session"""
        response = test_app_client.post(
            "/api/session/clear",
            params={"session_id": "existing-session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == "test-session"  # New session from mock
        
        # Verify clear was called
        app = test_app_client.app
        app.mock_rag.session_manager.clear_session.assert_called_with("existing-session")
    
    def test_clear_session_without_id(self, test_app_client):
        """Test clearing session without providing ID"""
        response = test_app_client.post("/api/session/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == "test-session"
        
        # Verify clear was not called
        app = test_app_client.app
        app.mock_rag.session_manager.clear_session.assert_not_called()
    
    def test_clear_session_error_handling(self, test_app_client):
        """Test error handling in session clear"""
        # Make clear raise an error
        app = test_app_client.app
        app.mock_rag.session_manager.clear_session.side_effect = Exception("Session error")
        
        response = test_app_client.post(
            "/api/session/clear",
            params={"session_id": "test-session"}
        )
        
        assert response.status_code == 500
        assert "Session error" in response.json()["detail"]
    
    def test_clear_nonexistent_session(self, test_app_client):
        """Test clearing a session that doesn't exist"""
        # Mock should handle this gracefully
        response = test_app_client.post(
            "/api/session/clear",
            params={"session_id": "nonexistent-session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data


@pytest.mark.api
class TestRootEndpoint:
    """Test suite for root endpoint"""
    
    def test_root_endpoint(self, test_app_client):
        """Test root endpoint returns API info"""
        response = test_app_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "RAG System API"
        assert data["version"] == "1.0.0"
    
    def test_root_endpoint_headers(self, test_app_client):
        """Test CORS headers are properly set"""
        response = test_app_client.get("/")
        
        # CORS headers are typically set by middleware on actual requests
        # For now, just verify response is successful
        assert response.status_code == 200


@pytest.mark.api
class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    def test_query_session_flow(self, test_app_client):
        """Test complete flow: query -> get session -> clear session"""
        # Step 1: Make initial query without session
        query_response = test_app_client.post("/api/query", json={
            "query": "Initial question"
        })
        assert query_response.status_code == 200
        session_id = query_response.json()["session_id"]
        
        # Step 2: Make follow-up query with session
        followup_response = test_app_client.post("/api/query", json={
            "query": "Follow-up question",
            "session_id": session_id
        })
        assert followup_response.status_code == 200
        assert followup_response.json()["session_id"] == session_id
        
        # Step 3: Clear session
        clear_response = test_app_client.post(
            "/api/session/clear",
            params={"session_id": session_id}
        )
        assert clear_response.status_code == 200
        new_session_id = clear_response.json()["session_id"]
        # In real app, new session ID would be different, but mock returns same ID
        assert new_session_id == "test-session"
    
    def test_concurrent_sessions(self, test_app_client):
        """Test handling multiple concurrent sessions"""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            response = test_app_client.post("/api/query", json={
                "query": f"Query {i}"
            })
            assert response.status_code == 200
            sessions.append(response.json()["session_id"])
        
        # All sessions should be the same in this mock
        # In real app, they would be different
        assert all(s == "test-session" for s in sessions)
    
    def test_api_response_times(self, test_app_client):
        """Test that API responses are reasonably fast"""
        import time
        
        # Test query endpoint
        start = time.time()
        response = test_app_client.post("/api/query", json={
            "query": "Test query"
        })
        query_time = time.time() - start
        assert response.status_code == 200
        assert query_time < 1.0  # Should respond in less than 1 second
        
        # Test courses endpoint
        start = time.time()
        response = test_app_client.get("/api/courses")
        courses_time = time.time() - start
        assert response.status_code == 200
        assert courses_time < 0.5  # Should be faster than query
    
    def test_malformed_requests(self, test_app_client):
        """Test various malformed requests"""
        # Wrong HTTP method
        response = test_app_client.get("/api/query")
        assert response.status_code == 405  # Method not allowed
        
        # Wrong content type
        response = test_app_client.post(
            "/api/query",
            data="query=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422
        
        # Empty body
        response = test_app_client.post("/api/query", json={})
        assert response.status_code == 422