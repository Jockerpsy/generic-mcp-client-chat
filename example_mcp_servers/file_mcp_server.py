from fastmcp import FastMCP
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP(
    "File System Tools Server",
    description="A server providing file system navigation tools",
    version="1.0.0"
)

# Keep track of current directory
current_dir = os.getcwd()

@mcp.tool()
def ls(path: str = ".") -> str:
    """List contents of a directory"""
    logger.info(f"ls tool called with path: {path}")
    try:
        # Resolve path relative to current directory
        full_path = os.path.join(current_dir, path)
        full_path = os.path.abspath(full_path)
        
        # Check if path exists
        if not os.path.exists(full_path):
            return f"Error: Path '{path}' does not exist"
            
        # Check if it's a directory
        if not os.path.isdir(full_path):
            return f"Error: '{path}' is not a directory"
            
        # List contents
        items = os.listdir(full_path)
        
        # Format output
        result = f"Contents of {path}:\n"
        for item in sorted(items):
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                result += f"📁 {item}/\n"
            else:
                result += f"📄 {item}\n"
        return result
    except Exception as e:
        logger.error(f"Error in ls: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def cd(path: str) -> str:
    """Change current directory"""
    logger.info(f"cd tool called with path: {path}")
    global current_dir
    try:
        # Resolve path relative to current directory
        new_dir = os.path.join(current_dir, path)
        new_dir = os.path.abspath(new_dir)
        
        # Check if path exists
        if not os.path.exists(new_dir):
            return f"Error: Path '{path}' does not exist"
            
        # Check if it's a directory
        if not os.path.isdir(new_dir):
            return f"Error: '{path}' is not a directory"
            
        # Update current directory
        current_dir = new_dir
        return f"Changed directory to: {current_dir}"
    except Exception as e:
        logger.error(f"Error in cd: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting File System MCP server...")
    logger.info("Server will be available at http://localhost:8003/mcp")
    logger.info("Available tools:")
    logger.info("- ls: List contents of a directory")
    logger.info("- cd: Change current directory")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8003,
        path="/mcp"
    ) 