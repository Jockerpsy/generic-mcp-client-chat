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
    "Math Tools Server",
    description="A server providing letter counting and fibonacci tools",
    version="1.0.0"
)

@mcp.tool()
def count_letters(word: str) -> str:
    """Count the number of letters in a word"""
    logger.info(f"Count letters tool called with word: {word}")
    count = len(word)
    return f"The word '{word}' has {count} letters"

@mcp.tool()
def fibonacci(n: int) -> str:
    """Calculate the fibonacci number for a given input"""
    logger.info(f"Fibonacci tool called with n: {n}")
    if n < 0:
        return "Error: Input must be a non-negative integer"
    
    def fib(n):
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    result = fib(n)
    return f"Fibonacci({n}) = {result}"

if __name__ == "__main__":
    logger.info("Starting second MCP server...")
    logger.info("Server will be available at http://localhost:8002/mcp")
    logger.info("Available tools:")
    logger.info("- count_letters: Count the number of letters in a word")
    logger.info("- fibonacci: Calculate the fibonacci number for a given input")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8002,
        path="/mcp"
    ) 