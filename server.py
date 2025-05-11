from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from mcp_client import MCPManager
import logging
from contextlib import asynccontextmanager
from anthropic import Anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Anthropic client
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
anthropic = Anthropic(api_key=api_key)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    default_mcp_server_url = "http://localhost:8000/mcp" # Full path
    default_server_name = "default_mcp_server"
    logger.info(f"Attempting to connect to default MCP server '{default_server_name}' at {default_mcp_server_url} on startup.")
    
    # Perform a quick availability check first
    if await check_server_availability(default_mcp_server_url):
        logger.info(f"Basic availability check passed for {default_mcp_server_url}. Proceeding with FastMCP connection.")
        success = await mcp_manager.connect(default_server_name, default_mcp_server_url)
        if success:
            logger.info(f"Successfully connected to default MCP server '{default_server_name}' using MCPManager.")
            try:
                tools = await mcp_manager.list_tools(default_server_name)
                logger.info(f"Tools on '{default_server_name}': {tools}")
            except Exception as e:
                logger.error(f"Error listing tools on default server after startup connection: {e}")
        else:
            logger.error(f"Failed to connect to default MCP server '{default_server_name}' using MCPManager after availability check.")
    else:
        logger.error(f"Basic availability check failed for default MCP server at {default_mcp_server_url}. Will not attempt FastMCP connection on startup.")
    
    yield
    
    # Shutdown
    for server_name in list(mcp_manager._clients.keys()):
        await mcp_manager.disconnect(server_name)

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Instantiate the MCP manager
mcp_manager = MCPManager()

# Data models
class ServerConfig(BaseModel):
    server_name: str
    server_url: str
    api_key: Optional[str] = None

class ConnectionRequest(BaseModel):
    server_name: str
    server_url: str
    api_key: Optional[str] = None

class ChatRequest(BaseModel):
    server_name: str
    message: str

class DisconnectRequest(BaseModel):
    server_name: str

async def check_server_availability(url: str) -> bool:
    """Basic check if an HTTP server is listening at the URL (before full MCP connection)."""
    logger.info(f"Performing basic availability check for URL: {url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=3) as response:
                # We just care if it responds, status 200-4xx is fine for a basic ping
                logger.info(f"Availability check for {url} got status: {response.status}")
                return True # Server is at least responding to HTTP
    except asyncio.TimeoutError:
        logger.error(f"Timeout during basic availability check for {url}")
        return False
    except aiohttp.ClientConnectorError as e:
        logger.error(f"Connection error during basic availability check for {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during basic availability check for {url}: {e}")
        return False

@app.post("/api/connect")
async def connect_mcp_server(request: ConnectionRequest):
    logger.info(f"API call to connect to MCP server: '{request.server_name}' at {request.server_url}")
    
    if not request.server_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid server_url format. Must include http:// or https://")

    # The server_url for connect should already include the /mcp path if needed by FastMCP server
    if await check_server_availability(request.server_url):
        logger.info(f"Basic availability check passed for '{request.server_name}'. Proceeding with FastMCP connection.")
        success = await mcp_manager.connect(request.server_name, request.server_url)
        if success:
            logger.info(f"Successfully initiated connection to '{request.server_name}'.")
            return {"status": "connected", "server_name": request.server_name}
        else:
            logger.error(f"Failed to connect to '{request.server_name}' using MCPManager after availability check.")
            raise HTTPException(status_code=500, detail=f"Failed to connect to MCP server '{request.server_name}'. Check server logs.")
    else:
        logger.error(f"Basic availability check failed for '{request.server_name}' at {request.server_url}.")
        raise HTTPException(status_code=503, detail=f"MCP server '{request.server_name}' not available at {request.server_url}.")

@app.post("/api/disconnect")
async def disconnect_mcp_server(request: DisconnectRequest):
    logger.info(f"API call to disconnect from MCP server: '{request.server_name}'")
    success = await mcp_manager.disconnect(request.server_name)
    if success:
        logger.info(f"Successfully processed disconnect for '{request.server_name}'.")
        return {"status": "disconnected", "server_name": request.server_name}
    else:
        # Disconnect might return False if error during cleanup, but still considered processed.
        logger.warning(f"Disconnect for '{request.server_name}' completed, possibly with minor issues (e.g., already disconnected).")
        return {"status": "disconnected_with_issues_or_not_found", "server_name": request.server_name}

@app.post("/api/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "")
        server_name = data.get("server", "claude")  # Default to claude if not specified
        
        if server_name == "claude":
            # Use Anthropic client for Claude
            response = anthropic.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1024,
                messages=[{"role": "user", "content": message}]
            )
            return {"response": response.content[0].text}
        else:
            # Use MCP server for other servers
            if not mcp_manager.is_connected(server_name):
                raise HTTPException(status_code=503, detail=f"Server {server_name} is not connected")
            
            # Get available tools
            tools = await mcp_manager.list_tools(server_name)
            tool_names = [tool.name for tool in tools]
            
            # If the message starts with a tool name, use that tool
            first_word = message.split()[0].lower() if message else ""
            if first_word in tool_names and first_word != "chat":
                # Extract the tool name and parameters
                tool_name = first_word
                parameters = {"message": " ".join(message.split()[1:])}
                response = await mcp_manager.call_tool(server_name, tool_name, parameters)
            else:
                # Use the chat tool for regular messages
                response = await mcp_manager.call_tool(server_name, "chat", {"message": message})
            
            # Ensure response is a string
            if not isinstance(response, str):
                response = str(response)
                
            return {"response": response}
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/servers")
async def list_servers():
    """List all connected servers"""
    return {"servers": list(mcp_manager.list_servers())}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server for MCP manager on http://localhost:8001")
    logger.info("Ensure your target MCP server(s) (e.g., mcp_server.py) are running.")
    # The startup event will try to connect to the default MCP server.
    uvicorn.run(app, host="0.0.0.0", port=8001) 