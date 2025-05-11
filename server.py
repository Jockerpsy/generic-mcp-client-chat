from fastapi import FastAPI, HTTPException, Request, WebSocket
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
import json
import re
from fastapi.responses import FileResponse

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
    default_server_name = "default_mcp"
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
    
    # Disconnect from all servers
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
    message: str  # Removed server_name since we'll use all servers

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
        
        # Get response from Claude with all available tools
        all_tools = []
        for server_name in mcp_manager._clients.keys():
            if mcp_manager.is_connected(server_name):
                try:
                    tools = await mcp_manager.list_tools(server_name)
                    logger.info(f"Found {len(tools)} tools on server {server_name}")
                    for tool in tools:
                        tool_info = {
                            "name": f"{server_name}.{tool.name}",  # Prefix tool name with server
                            "description": tool.description,
                            "input_schema": tool.inputSchema,
                            "server": server_name
                        }
                        logger.info(f"Adding tool: {tool_info['name']}")
                        all_tools.append(tool_info)
                except Exception as e:
                    logger.error(f"Error getting tools from server {server_name}: {e}")
        
        logger.info(f"Total tools available: {len(all_tools)}")
        
        # Create system message with tool descriptions
        system_content = f"""You are a helpful AI assistant with access to the following tools:
{json.dumps(all_tools, indent=2)}

When you need to use a tool, respond with a JSON object in this format:
{{
    "tool": "server_name.tool_name",
    "parameters": {{
        "param_name": "param_value"
    }}
}}

For example, to use the echo tool, respond with:
{{
    "tool": "default_mcp.echo",
    "parameters": {{
        "message": "your message here"
    }}
}}

Otherwise, respond normally with your message."""
        
        # Get response from Claude
        response = anthropic.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            system=system_content,
            messages=[{"role": "user", "content": message}]
        )
        
        # Check if response is a tool call
        try:
            response_text = response.content[0].text.strip()
            # Try to extract JSON from code block
            code_block_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', response_text)
            if code_block_match:
                json_str = code_block_match.group(1)
                tool_call = json.loads(json_str)
            else:
                # Try to find the first JSON object in the text
                json_match = re.search(r'(\{[\s\S]*\})', response_text)
                if json_match:
                    tool_call = json.loads(json_match.group(1))
                else:
                    tool_call = json.loads(response_text)
            
            if isinstance(tool_call, dict) and "tool" in tool_call and "parameters" in tool_call:
                # Parse server and tool name
                server_name, tool_name = tool_call["tool"].split(".", 1)
                logger.info(f"Executing tool call: {tool_name} on server {server_name}")
                # Execute the tool call
                tool_response = await mcp_manager.call_tool(
                    server_name,
                    tool_name,
                    tool_call["parameters"]
                )
                return {"response": str(tool_response)}
        except Exception as e:
            logger.error(f"Tool call parsing/execution failed: {e}")
            # Not a tool call, return Claude's response
            pass
        
        return {"response": response.content[0].text}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/servers")
async def list_servers():
    """List all connected servers"""
    connected_servers = []
    for server_name in mcp_manager._clients.keys():
        if mcp_manager.is_connected(server_name):
            connected_servers.append(server_name)
    logger.info(f"Listing connected servers: {connected_servers}")
    return {"servers": connected_servers}

@app.get("/")
async def get_index():
    """Serve the main page"""
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server for MCP manager on http://localhost:8001")
    logger.info("Ensure your target MCP server(s) (e.g., mcp_server.py) are running.")
    # The startup event will try to connect to the default MCP server.
    uvicorn.run(app, host="0.0.0.0", port=8001) 