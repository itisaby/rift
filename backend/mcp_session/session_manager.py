"""
MCP Session Manager
Manages MCP server subprocesses and client sessions for the Rift backend
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger("rift.mcp_session")


class ServerSession:
    """Manages one MCP server subprocess + ClientSession"""

    def __init__(self, name: str, server_params: StdioServerParameters):
        self.name = name
        self.server_params = server_params
        self._session: Optional[ClientSession] = None
        self._lock = asyncio.Lock()
        self._context_manager = None
        self._session_cm = None

    async def start(self):
        """Start the server subprocess and establish client session"""
        logger.info(f"Starting MCP server: {self.name}")
        self._context_manager = stdio_client(self.server_params)
        read_stream, write_stream = await self._context_manager.__aenter__()
        self._session_cm = ClientSession(read_stream, write_stream)
        self._session = await self._session_cm.__aenter__()
        await self._session.initialize()
        logger.info(f"MCP server '{self.name}' started and initialized")

    async def stop(self):
        """Stop the server subprocess"""
        logger.info(f"Stopping MCP server: {self.name}")
        try:
            if self._session_cm:
                await self._session_cm.__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"Error closing session for {self.name}: {e}")
        try:
            if self._context_manager:
                await asyncio.wait_for(
                    self._context_manager.__aexit__(None, None, None),
                    timeout=5.0,
                )
        except (asyncio.TimeoutError, asyncio.CancelledError):
            logger.warning(f"Timed out or cancelled stopping stdio client for {self.name}, forcing shutdown")
        except Exception as e:
            logger.warning(f"Error closing stdio client for {self.name}: {e}")
        self._session = None
        logger.info(f"MCP server '{self.name}' stopped")

    async def call(self, tool_name: str, arguments: dict) -> Any:
        """Call a tool on this server, serializing writes via lock"""
        if not self._session:
            raise RuntimeError(f"MCP server '{self.name}' not started")
        async with self._lock:
            result = await self._session.call_tool(tool_name, arguments)
        # Parse TextContent results automatically
        if result.content:
            texts = []
            for content in result.content:
                if hasattr(content, "text"):
                    texts.append(content.text)
            if texts:
                combined = texts[0] if len(texts) == 1 else "\n".join(texts)
                try:
                    return json.loads(combined)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"MCP server '{self.name}' tool '{tool_name}' returned non-JSON: {combined[:200]}")
                    return combined
        return None

    async def list_tools(self):
        """List available tools on this server"""
        if not self._session:
            raise RuntimeError(f"MCP server '{self.name}' not started")
        result = await self._session.list_tools()
        return result.tools


class MCPSessionManager:
    """
    Manages all MCP server subprocesses.
    Registers servers, starts them all, provides call(server, tool, args) method.
    """

    def __init__(self):
        self._servers: Dict[str, ServerSession] = {}

    def register(self, name: str, command: str, args: list[str] = None, env: dict = None):
        """
        Register an MCP server to be managed.

        Args:
            name: Server name (e.g. "do", "terraform")
            command: Command to run (e.g. "python")
            args: Command arguments (e.g. ["mcp_servers/do_server.py"])
            env: Optional environment variables
        """
        params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env,
        )
        self._servers[name] = ServerSession(name, params)
        logger.info(f"Registered MCP server: {name} ({command} {' '.join(args or [])})")

    async def start_all(self):
        """Start all registered MCP server subprocesses"""
        logger.info(f"Starting {len(self._servers)} MCP servers...")
        for name, session in self._servers.items():
            try:
                await session.start()
            except Exception as e:
                logger.error(f"Failed to start MCP server '{name}': {e}")
                raise
        logger.info("All MCP servers started successfully")

    async def stop_all(self):
        """Stop all MCP server subprocesses"""
        logger.info("Stopping all MCP servers...")
        for name, session in self._servers.items():
            try:
                await session.stop()
            except Exception as e:
                logger.error(f"Error stopping MCP server '{name}': {e}")
        logger.info("All MCP servers stopped")

    async def call(self, server_name: str, tool_name: str, arguments: dict = None) -> Any:
        """
        Call a tool on a specific MCP server.

        Args:
            server_name: Name of the server (e.g. "do", "terraform")
            tool_name: Name of the tool to call
            arguments: Tool arguments dict

        Returns:
            Parsed result (dict, list, str, etc.)
        """
        if server_name not in self._servers:
            raise ValueError(f"Unknown MCP server: {server_name}. Available: {list(self._servers.keys())}")
        return await self._servers[server_name].call(tool_name, arguments or {})

    async def list_tools(self, server_name: str):
        """List tools available on a specific server"""
        if server_name not in self._servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        return await self._servers[server_name].list_tools()

    @property
    def server_names(self) -> list[str]:
        return list(self._servers.keys())
