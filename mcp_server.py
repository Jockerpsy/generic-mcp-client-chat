from fastmcp import FastMCP
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP(
    "Tools Server",
    description="A server providing echo and repeat tools",
    version="1.0.0"
)

@mcp.tool()
def echo(message: str) -> str:
    """Echoes back the input message"""
    logger.info(f"Echo tool called with message: {message}")
    return message

@mcp.tool()
def repeat(message: str, times: int = 10) -> str:
    """Repeats the input message a specified number of times (default: 10)"""
    logger.info(f"Repeat tool called with message: {message} and times: {times}")
    repeated = "\n".join([message] * times)
    return f"Repeating {times} times:\n{repeated}"

if __name__ == "__main__":
    logger.info("Starting MCP server...")
    logger.info("Server will be available at http://localhost:8000/mcp")
    logger.info("Available tools:")
    logger.info("- echo: Echoes back the input message")
    logger.info("- repeat: Repeats the input message a specified number of times")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        path="/mcp"
    ) 