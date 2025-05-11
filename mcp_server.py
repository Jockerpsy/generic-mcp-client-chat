from fastmcp import FastMCP
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP(
    "Tools Server",
    description="A server providing echo and conversation history tools",
    version="1.0.0"
)

@mcp.tool()
def echo(message: str) -> str:
    """Echo back the input message"""
    logger.info(f"Echo tool called with message: {message}")
    return f"Echo: {message}"

@mcp.tool()
def chat(message: str) -> str:
    """Handle chat messages"""
    logger.info(f"Chat tool called with message: {message}")
    # Add the message to conversation history
    mcp.conversation_history.append({"role": "user", "content": message})
    # For now, just echo back with a chat prefix
    response = f"Chat: {message}"
    mcp.conversation_history.append({"role": "assistant", "content": response})
    return response

@mcp.resource("conversation://history")
def get_conversation_history() -> str:
    """Get the current conversation history"""
    history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in mcp.conversation_history])
    logger.info(f"Conversation history requested. Length: {len(mcp.conversation_history)} messages")
    return history

if __name__ == "__main__":
    logger.info("Starting MCP server...")
    logger.info("Server will be available at http://localhost:8000/mcp")
    logger.info("Available tools:")
    logger.info("- echo: Echoes back the input message")
    logger.info("- chat: Handles chat messages")
    logger.info("Available resources:")
    logger.info("- conversation://history: Returns the conversation history")
    
    # Run the server with streamable-http transport
    mcp.run(
        transport="streamable-http",  # Use streamable-http transport
        host="0.0.0.0",
        port=8000,
        path="/mcp"
    ) 