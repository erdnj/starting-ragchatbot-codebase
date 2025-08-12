import anthropic
from typing import List, Optional, Dict


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to tools for course information.

Available Tools:
1. **search_course_content**: Search within course materials for specific content
   - Use for questions about specific topics, concepts, or detailed educational materials
   - Can filter by course name and lesson number

2. **get_course_outline**: Get complete course structure with all lessons
   - Use for questions about course overview, structure, or lesson list
   - Returns course title, link, and all lesson titles with numbers
   - Perfect for "show outline", "list lessons", "what's in the course" queries

Tool Usage Guidelines:
- **Sequential tool usage**: You may use up to 2 tools sequentially to answer complex queries
- Choose tools strategically based on the query:
  - Outline/structure questions → use get_course_outline
  - Content/topic questions → use search_course_content
  - Complex comparisons → use multiple tools to gather comprehensive information
- After receiving tool results, you can make another tool call if needed to:
  - Search for related content based on initial findings
  - Get additional context or details
  - Compare information across different courses or lessons
- If tool yields no results, state this clearly and consider alternative searches

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without tools
- **Course outline questions**: Use get_course_outline tool, then format the response clearly
- **Course content questions**: Use search_course_content tool, then synthesize results
- **Complex queries**: Use multiple tools sequentially to build comprehensive answers
- **No meta-commentary**: Provide direct answers only

For outline queries, format the response as:
- Course title and link
- Numbered list of all lessons with their titles

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Well-formatted** - Use clear structure for outlines and lists
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
        max_rounds: int = 2,
    ) -> str:
        """
        Generate AI response with optional sequential tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            max_rounds: Maximum number of tool-calling rounds (default: 2)

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Initialize messages with user query
        messages = [{"role": "user", "content": query}]

        # Track rounds for sequential tool calling
        rounds_completed = 0

        while rounds_completed < max_rounds:
            # Prepare API call parameters
            api_params = {
                **self.base_params,
                "messages": messages,
                "system": system_content,
            }

            # Add tools if available and tool_manager exists
            if tools and tool_manager:
                api_params["tools"] = tools
                api_params["tool_choice"] = {"type": "auto"}

            # Get response from Claude
            try:
                response = self.client.messages.create(**api_params)
            except Exception as e:
                # Handle API errors gracefully
                return f"Error generating response: {str(e)}"

            # Check if this response contains tool use
            if response.stop_reason == "tool_use" and tool_manager:
                # Execute tools and add results to conversation
                tool_executed = self._execute_tool_round(
                    response, messages, tool_manager
                )
                if not tool_executed:
                    # Tool execution failed, return what we have
                    return self._extract_text_from_response(response)
                rounds_completed += 1
                print(
                    f"Round {rounds_completed} completed, continuing with next round."
                )
                # Continue to next round for potential follow-up tool use
            else:
                # No tool use or no tool_manager, return the response
                return self._extract_text_from_response(response)

        # Maximum rounds reached, get final response without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content,
        }

        try:
            final_response = self.client.messages.create(**final_params)
            return self._extract_text_from_response(final_response)
        except Exception as e:
            return f"Error generating final response: {str(e)}"

    def _execute_tool_round(self, response, messages: List[Dict], tool_manager) -> bool:
        """
        Execute tool calls from a response and update message history.

        Args:
            response: The response containing tool use requests
            messages: Message history to update
            tool_manager: Manager to execute tools

        Returns:
            True if tools were executed successfully, False otherwise
        """
        # Add AI's response with tool use to messages
        messages.append({"role": "assistant", "content": response.content})

        # Execute all tool calls and collect results
        tool_results = []
        print(response)
        for content_block in response.content:
            if content_block.type == "tool_use":
                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name, **content_block.input
                    )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": tool_result,
                        }
                    )
                except Exception as e:
                    # Handle tool execution errors
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": f"Error executing tool: {str(e)}",
                        }
                    )

        # Add tool results to messages if any were executed
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
            return True

        return False

    def _extract_text_from_response(self, response) -> str:
        """
        Extract text content from API response.

        Args:
            response: API response object

        Returns:
            Extracted text or error message
        """
        try:
            # Find first text content block
            for content_block in response.content:
                if hasattr(content_block, "text"):
                    return content_block.text
            # No text found
            return "No text content in response"
        except Exception as e:
            return f"Error extracting response text: {str(e)}"
