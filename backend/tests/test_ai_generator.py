import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_generator import AIGenerator


class TestAIGenerator:
    """Test suite for AIGenerator with sequential tool calling support"""
    
    @pytest.fixture
    def ai_generator(self):
        """Create AIGenerator instance with mocked client"""
        with patch('ai_generator.anthropic.Anthropic'):
            generator = AIGenerator(api_key="test_key", model="test-model")
            generator.client = Mock()
            return generator
    
    @pytest.fixture
    def mock_tool_manager(self):
        """Create mock tool manager"""
        tool_manager = Mock()
        tool_manager.execute_tool = Mock()
        return tool_manager
    
    @pytest.fixture
    def sample_tools(self):
        """Sample tool definitions"""
        return [
            {
                "name": "search_course_content",
                "description": "Search course materials",
                "input_schema": {"type": "object"}
            },
            {
                "name": "get_course_outline", 
                "description": "Get course outline",
                "input_schema": {"type": "object"}
            }
        ]
    
    # Test 1: Single Tool Call - Backward Compatibility
    def test_single_tool_call_backward_compatibility(self, ai_generator, mock_tool_manager, sample_tools):
        """Verify existing single tool call behavior still works"""
        # Setup mock responses
        tool_response = Mock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [
            Mock(type="tool_use", name="search_course_content", 
                 input={"query": "python basics"}, id="tool_1")
        ]
        
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Here are the Python basics...")]
        
        ai_generator.client.messages.create = Mock(side_effect=[tool_response, final_response])
        mock_tool_manager.execute_tool.return_value = "Found: Python fundamentals lesson"
        
        # Execute
        result = ai_generator.generate_response(
            query="Find Python basics",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify
        assert result == "Here are the Python basics..."
        assert ai_generator.client.messages.create.call_count == 2
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content", query="python basics"
        )
    
    # Test 2: Sequential Two-Tool Call
    def test_sequential_two_tool_calls(self, ai_generator, mock_tool_manager, sample_tools):
        """Test sequential execution of two tool calls"""
        # First tool response
        first_tool_response = Mock()
        first_tool_response.stop_reason = "tool_use"
        first_tool_response.content = [
            Mock(type="tool_use", name="get_course_outline",
                 input={"course": "Python 101"}, id="tool_1")
        ]
        
        # Second tool response (after first tool execution)
        second_tool_response = Mock()
        second_tool_response.stop_reason = "tool_use"
        second_tool_response.content = [
            Mock(type="tool_use", name="search_course_content",
                 input={"query": "lesson 4 content"}, id="tool_2")
        ]
        
        # Final response
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Based on the outline and search results...")]
        
        ai_generator.client.messages.create = Mock(
            side_effect=[first_tool_response, second_tool_response, final_response]
        )
        
        mock_tool_manager.execute_tool.side_effect = [
            "Course outline: Lesson 1, Lesson 2, Lesson 3, Lesson 4",
            "Lesson 4 covers advanced topics..."
        ]
        
        # Execute
        result = ai_generator.generate_response(
            query="What's in lesson 4 of Python 101?",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify
        assert result == "Based on the outline and search results..."
        assert ai_generator.client.messages.create.call_count == 3
        assert mock_tool_manager.execute_tool.call_count == 2
        
        # Verify tool execution order
        calls = mock_tool_manager.execute_tool.call_args_list
        assert calls[0] == call("get_course_outline", course="Python 101")
        assert calls[1] == call("search_course_content", query="lesson 4 content")
    
    # Test 3: Early Termination - No Tool Use
    def test_early_termination_no_tool_use(self, ai_generator, mock_tool_manager, sample_tools):
        """Test early termination when no tools are used"""
        # Direct response without tool use
        direct_response = Mock()
        direct_response.stop_reason = "end_turn"
        direct_response.content = [Mock(text="I can answer this directly...")]
        
        ai_generator.client.messages.create = Mock(return_value=direct_response)
        
        # Execute
        result = ai_generator.generate_response(
            query="What is Python?",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify
        assert result == "I can answer this directly..."
        assert ai_generator.client.messages.create.call_count == 1
        mock_tool_manager.execute_tool.assert_not_called()
    
    # Test 4: Early Termination - After One Tool
    def test_early_termination_after_one_tool(self, ai_generator, mock_tool_manager, sample_tools):
        """Test termination after one tool when second round has no tool use"""
        # First response with tool use
        tool_response = Mock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [
            Mock(type="tool_use", name="search_course_content",
                 input={"query": "databases"}, id="tool_1")
        ]
        
        # Second response without tool use
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Based on the search results...")]
        
        ai_generator.client.messages.create = Mock(side_effect=[tool_response, final_response])
        mock_tool_manager.execute_tool.return_value = "Database course materials..."
        
        # Execute
        result = ai_generator.generate_response(
            query="Find database courses",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify
        assert result == "Based on the search results..."
        assert ai_generator.client.messages.create.call_count == 2
        assert mock_tool_manager.execute_tool.call_count == 1
    
    # Test 5: Maximum Rounds Enforcement
    def test_maximum_rounds_enforcement(self, ai_generator, mock_tool_manager, sample_tools):
        """Test that tool calling stops after max_rounds"""
        # Create tool responses that would continue indefinitely
        tool_response = Mock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [
            Mock(type="tool_use", name="search_course_content",
                 input={"query": "test"}, id="tool_id")
        ]
        
        # Final response after max rounds
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="Final answer after max rounds")]
        
        # Setup to return tool_response twice, then final_response
        ai_generator.client.messages.create = Mock(
            side_effect=[tool_response, tool_response, final_response]
        )
        mock_tool_manager.execute_tool.return_value = "Search result"
        
        # Execute with max_rounds=2
        result = ai_generator.generate_response(
            query="Complex query",
            tools=sample_tools,
            tool_manager=mock_tool_manager,
            max_rounds=2
        )
        
        # Verify
        assert result == "Final answer after max rounds"
        assert ai_generator.client.messages.create.call_count == 3
        assert mock_tool_manager.execute_tool.call_count == 2
    
    # Test 6: Tool Execution Error Handling
    def test_tool_execution_error_handling(self, ai_generator, mock_tool_manager, sample_tools):
        """Test graceful handling of tool execution errors"""
        # Tool response
        tool_response = Mock()
        tool_response.stop_reason = "tool_use"
        tool_response.content = [
            Mock(type="tool_use", name="search_course_content",
                 input={"query": "test"}, id="tool_1"),
            Mock(type="text", text="Let me search for that...")
        ]
        
        # Second response after error
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(text="I encountered an error but here's what I know...")]
        
        ai_generator.client.messages.create = Mock(side_effect=[tool_response, final_response])
        
        # Simulate tool execution error
        mock_tool_manager.execute_tool.side_effect = Exception("Tool execution failed")
        
        # Execute
        result = ai_generator.generate_response(
            query="Search for something",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify error was handled gracefully
        assert result == "I encountered an error but here's what I know..."
        assert ai_generator.client.messages.create.call_count == 2
        mock_tool_manager.execute_tool.assert_called_once()
    
    # Test 7: API Error Handling
    def test_api_error_handling(self, ai_generator, mock_tool_manager, sample_tools):
        """Test graceful handling of API errors"""
        # Simulate API error
        ai_generator.client.messages.create.side_effect = Exception("API connection failed")
        
        # Execute
        result = ai_generator.generate_response(
            query="Test query",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify error message
        assert "Error generating response: API connection failed" in result
        mock_tool_manager.execute_tool.assert_not_called()
    
    # Test 8: Context Preservation Between Rounds
    def test_context_preservation_between_rounds(self, ai_generator, mock_tool_manager, sample_tools):
        """Test that context is preserved between tool calling rounds"""
        # Track API call arguments
        api_calls = []
        
        def track_api_call(**kwargs):
            api_calls.append(kwargs)
            if len(api_calls) == 1:
                # First call - return tool use
                response = Mock()
                response.stop_reason = "tool_use"
                response.content = [
                    Mock(type="tool_use", name="get_course_outline",
                         input={"course": "Math"}, id="tool_1")
                ]
                return response
            elif len(api_calls) == 2:
                # Second call - return another tool use
                response = Mock()
                response.stop_reason = "tool_use"
                response.content = [
                    Mock(type="tool_use", name="search_course_content",
                         input={"query": "calculus"}, id="tool_2")
                ]
                return response
            else:
                # Final call
                response = Mock()
                response.stop_reason = "end_turn"
                response.content = [Mock(text="Final response")]
                return response
        
        ai_generator.client.messages.create = Mock(side_effect=track_api_call)
        mock_tool_manager.execute_tool.side_effect = ["Outline data", "Search data"]
        
        # Execute
        result = ai_generator.generate_response(
            query="Find calculus in Math course",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify context preservation
        assert len(api_calls) == 3
        
        # Check that messages accumulate properly
        assert len(api_calls[0]["messages"]) == 1  # Initial user message
        assert len(api_calls[1]["messages"]) == 3  # User + Assistant + Tool Result
        assert len(api_calls[2]["messages"]) == 5  # Previous + Assistant + Tool Result
        
        # Verify final response
        assert result == "Final response"
    
    # Test 9: No Tools Available
    def test_no_tools_available(self, ai_generator):
        """Test behavior when no tools are provided"""
        # Direct response
        response = Mock()
        response.stop_reason = "end_turn"
        response.content = [Mock(text="Direct answer without tools")]
        
        ai_generator.client.messages.create = Mock(return_value=response)
        
        # Execute without tools
        result = ai_generator.generate_response(
            query="Answer this question"
        )
        
        # Verify
        assert result == "Direct answer without tools"
        assert ai_generator.client.messages.create.call_count == 1
        
        # Verify no tools were included in API call
        call_args = ai_generator.client.messages.create.call_args
        assert "tools" not in call_args[1]
    
    # Test 10: Conversation History Integration
    def test_conversation_history_integration(self, ai_generator, mock_tool_manager, sample_tools):
        """Test that conversation history is properly included"""
        # Setup response
        response = Mock()
        response.stop_reason = "end_turn"
        response.content = [Mock(text="Answer with context")]
        
        ai_generator.client.messages.create = Mock(return_value=response)
        
        # Execute with conversation history
        result = ai_generator.generate_response(
            query="Follow-up question",
            conversation_history="Previous Q: What is Python?\nPrevious A: A programming language",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify
        assert result == "Answer with context"
        
        # Check that conversation history was included in system prompt
        call_args = ai_generator.client.messages.create.call_args
        system_content = call_args[1]["system"]
        assert "Previous conversation:" in system_content
        assert "What is Python?" in system_content