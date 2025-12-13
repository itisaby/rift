"""
Base Agent Class for Rift
Foundation class for all AI agents in the system
"""

import httpx
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger("rift.agents")


class BaseAgent:
    """
    Base class for all Rift AI agents.
    Provides common functionality for communicating with DigitalOcean Gradient AI agents.
    """

    def __init__(
        self,
        agent_endpoint: str,
        agent_key: str,
        agent_id: str,
        agent_name: str,
        knowledge_base_id: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        Initialize base agent.

        Args:
            agent_endpoint: Gradient AI agent endpoint URL
            agent_key: API key for authentication
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
            knowledge_base_id: Optional knowledge base ID for RAG
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.agent_endpoint = agent_endpoint
        self.agent_key = agent_key
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.knowledge_base_id = knowledge_base_id
        self.max_retries = max_retries
        self.timeout = timeout

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {agent_key}",
                "Content-Type": "application/json"
            }
        )

        logger.info(f"Initialized {agent_name} agent (ID: {agent_id})")

    async def query_agent(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        use_knowledge_base: bool = True
    ) -> Dict[str, Any]:
        """
        Query the Gradient AI agent with a prompt.

        Args:
            prompt: The prompt/question to send to the agent
            context: Optional additional context
            use_knowledge_base: Whether to use RAG knowledge base

        Returns:
            Agent response as dictionary with 'response' key containing the answer

        Raises:
            Exception: If query fails after max retries
        """
        # Build message with context if provided
        message_content = prompt
        if context:
            context_str = json.dumps(context, indent=2)
            message_content = f"Context:\n{context_str}\n\nQuestion: {prompt}"

        # DigitalOcean Gradient AI uses OpenAI-compatible chat completions endpoint
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": message_content
                }
            ],
            "stream": False,
            "include_functions_info": False,
            "include_retrieval_info": use_knowledge_base and self.knowledge_base_id is not None,
            "include_guardrails_info": False
        }
        
        # Add knowledge base ID if using RAG
        if use_knowledge_base and self.knowledge_base_id:
            payload["knowledge_base_id"] = self.knowledge_base_id
            logger.debug(f"{self.agent_name}: Using knowledge base: {self.knowledge_base_id}")

        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"{self.agent_name}: Querying agent (attempt {attempt + 1}/{self.max_retries})")

                response = await self.client.post(
                    f"{self.agent_endpoint}/api/v1/chat/completions",
                    json=payload
                )

                response.raise_for_status()
                result = response.json()

                # Log the full response structure for debugging
                logger.debug(f"{self.agent_name}: Full API response: {json.dumps(result, indent=2)[:1000]}")

                # Extract the assistant's response from the OpenAI-style response
                choices = result.get("choices", [])
                logger.debug(f"{self.agent_name}: Number of choices: {len(choices)}")
                
                if not choices:
                    logger.error(f"{self.agent_name}: No choices in response")
                    logger.error(f"{self.agent_name}: Full result: {result}")
                
                assistant_message = choices[0].get("message", {}).get("content", "") if choices else ""
                
                logger.debug(f"{self.agent_name}: Assistant message length: {len(assistant_message)} chars")

                # Return in a simplified format
                simplified_result = {
                    "response": assistant_message,
                    "raw": result
                }

                logger.info(f"{self.agent_name}: Query successful (response: {len(assistant_message)} chars)")

                # Log interaction for traceability
                self._log_interaction(prompt, simplified_result)

                return simplified_result

            except httpx.HTTPStatusError as e:
                logger.error(f"{self.agent_name}: HTTP error {e.response.status_code}: {e.response.text}")

                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"{self.agent_name}: Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise Exception(f"{self.agent_name}: Query failed after {self.max_retries} attempts: {str(e)}")

            except httpx.RequestError as e:
                logger.error(f"{self.agent_name}: Request error: {str(e)}")

                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"{self.agent_name}: Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise Exception(f"{self.agent_name}: Connection failed after {self.max_retries} attempts: {str(e)}")

            except Exception as e:
                logger.error(f"{self.agent_name}: Unexpected error: {str(e)}")
                raise

    async def call_function(
        self,
        function_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a function/tool via the agent.

        This method allows agents to use MCP functions through the Gradient AI platform.

        Args:
            function_name: Name of the function to call
            parameters: Function parameters

        Returns:
            Function result as dictionary
        """
        payload = {
            "function": function_name,
            "parameters": parameters,
            "agent_id": self.agent_id
        }

        try:
            logger.debug(f"{self.agent_name}: Calling function '{function_name}'")

            response = await self.client.post(
                f"{self.agent_endpoint}/function",
                json=payload
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"{self.agent_name}: Function '{function_name}' executed successfully")
            return result

        except Exception as e:
            logger.error(f"{self.agent_name}: Function call failed: {str(e)}")
            raise

    def _log_interaction(self, prompt: str, response: Dict[str, Any]) -> None:
        """
        Log agent interaction for traceability.

        Args:
            prompt: The prompt sent to the agent
            response: The agent's response
        """
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,  # Truncate long prompts
            "response_summary": str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
        }

        logger.debug(f"Interaction logged: {json.dumps(interaction)}")

    async def check_health(self) -> Dict[str, Any]:
        """
        Check agent health status.

        Note: Gradient AI agents don't have a /health endpoint, so we just verify
        the agent configuration and client initialization.

        Returns:
            Health status dictionary
        """
        try:
            # Verify agent configuration is valid
            if not self.agent_endpoint or not self.agent_key or not self.agent_id:
                logger.debug(f"{self.agent_name}: Config check - endpoint={bool(self.agent_endpoint)}, key={bool(self.agent_key)}, id={bool(self.agent_id)}")
                raise ValueError(f"Agent configuration incomplete (endpoint={bool(self.agent_endpoint)}, key={bool(self.agent_key)}, id={bool(self.agent_id)})")

            # Verify endpoint has proper protocol
            if not self.agent_endpoint.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid endpoint URL: {self.agent_endpoint}")

            # Verify HTTP client is initialized
            if not self.client or self.client.is_closed:
                raise ValueError("HTTP client not initialized or closed")

            return {
                "agent_name": self.agent_name,
                "agent_id": self.agent_id,
                "status": "healthy",
                "endpoint": self.agent_endpoint,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"{self.agent_name}: Health check failed: {str(e)}")
            return {
                "agent_name": self.agent_name,
                "agent_id": self.agent_id,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()
        logger.info(f"{self.agent_name}: Client connection closed")

    def __repr__(self) -> str:
        return f"<{self.agent_name} Agent (ID: {self.agent_id})>"
