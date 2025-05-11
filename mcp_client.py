import asyncio
import logging
from typing import Dict, Optional, Any
from fastmcp import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPManager:
    def __init__(self):
        self._clients: Dict[str, Client] = {}
        self._connections: Dict[str, asyncio.Task] = {}

    async def connect(self, server_name: str, server_url: str) -> bool:
        """Connect to an MCP server and store the connection"""
        if server_name in self._clients:
            logger.info(f"Already connected to {server_name}")
            return True

        logger.info(f"Connecting to MCP server '{server_name}' at {server_url}")
        try:
            # Create a new client connection
            client = Client(server_url)
            # Start the connection
            connection = asyncio.create_task(client.__aenter__())
            await connection
            
            # Store the client and connection
            self._clients[server_name] = client
            self._connections[server_name] = connection
            
            # Test the connection by listing tools
            tools = await client.list_tools()
            logger.info(f"Successfully connected to '{server_name}'. Available tools: {len(tools)}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to '{server_name}': {type(e).__name__} - {e}")
            await self.disconnect(server_name)
            return False

    async def disconnect(self, server_name: str) -> bool:
        """Disconnect from an MCP server"""
        if server_name not in self._clients:
            logger.warning(f"No connection found for '{server_name}'")
            return True

        logger.info(f"Disconnecting from '{server_name}'")
        try:
            client = self._clients.pop(server_name)
            connection = self._connections.pop(server_name)
            
            # Close the client connection
            await client.__aexit__(None, None, None)
            # Cancel the connection task if it's still running
            if not connection.done():
                connection.cancel()
            
            logger.info(f"Successfully disconnected from '{server_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from '{server_name}': {type(e).__name__} - {e}")
            return False

    def is_connected(self, server_name: str) -> bool:
        """Check if connected to a server"""
        return server_name in self._clients

    async def call_tool(self, server_name: str, tool_name: str, parameters: dict) -> Any:
        """Call a tool on a specific server"""
        if not self.is_connected(server_name):
            raise ConnectionError(f"Not connected to server: {server_name}")

        client = self._clients[server_name]
        try:
            result = await client.call_tool(tool_name, parameters)
            # Handle different types of responses
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                # Handle list of TextContent objects
                return result[0].text
            elif hasattr(result, 'text'):
                return result.text
            elif isinstance(result, (str, int, float, bool)):
                return str(result)
            elif isinstance(result, (list, dict)):
                return str(result)  # Convert to string to ensure proper serialization
            else:
                return str(result)
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}' on '{server_name}': {type(e).__name__} - {e}")
            raise

    async def list_tools(self, server_name: str) -> list:
        """List tools available on a specific server"""
        if not self.is_connected(server_name):
            raise ConnectionError(f"Not connected to server: {server_name}")

        client = self._clients[server_name]
        try:
            return await client.list_tools()
        except Exception as e:
            logger.error(f"Error listing tools on '{server_name}': {type(e).__name__} - {e}")
            raise

    async def get_resource(self, server_name: str, resource_path: str) -> str:
        """Get a resource from a specific server"""
        if not self.is_connected(server_name):
            raise ConnectionError(f"Not connected to server: {server_name}")

        client = self._clients[server_name]
        try:
            result = await client.get_resource(resource_path)
            # Handle different types of responses
            if hasattr(result, 'text'):
                return result.text
            elif isinstance(result, (str, int, float, bool)):
                return str(result)
            elif isinstance(result, (list, dict)):
                return str(result)  # Convert to string to ensure proper serialization
            else:
                return str(result)
        except Exception as e:
            logger.error(f"Error getting resource '{resource_path}' from '{server_name}': {type(e).__name__} - {e}")
            raise

async def main():
    """Test the MCP manager with multiple servers"""
    manager = MCPManager()
    
    # Connect to multiple servers
    servers = {
        "server1": "http://localhost:8000/mcp",
        "server2": "http://localhost:8001/mcp"  # Example second server
    }
    
    # Connect to all servers
    for name, url in servers.items():
        if await manager.connect(name, url):
            logger.info(f"Connected to {name}")
            
            # List tools
            tools = await manager.list_tools(name)
            logger.info(f"Tools on {name}: {tools}")
            
            # Call echo tool if available
            if any(tool.name == "echo" for tool in tools):
                result = await manager.call_tool(name, "echo", {"message": f"Hello from {name}!"})
                logger.info(f"Echo result from {name}: {result}")
            
            # Get conversation history
            try:
                history = await manager.get_resource(name, "conversation://history")
                logger.info(f"History from {name}: {history}")
            except Exception as e:
                logger.warning(f"Could not get history from {name}: {e}")
    
    # Disconnect from all servers
    for name in list(servers.keys()):
        await manager.disconnect(name)

if __name__ == "__main__":
    asyncio.run(main()) 