from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import asyncio
import websockets
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# MCP WebSocket connection
async def connect_to_mcp():
    uri = os.getenv("MCP_URI", "ws://localhost:8000/mcp")
    print(f"Connecting to MCP server at {uri}")
    try:
        websocket = await websockets.connect(uri)
        print("Successfully connected to MCP server")
        return websocket
    except Exception as e:
        print(f"Failed to connect to MCP server: {e}")
        raise

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("New client connection request")
    await websocket.accept()
    print("Client connection accepted")
    mcp_ws = None
    
    try:
        mcp_ws = await connect_to_mcp()
        print("Connected to MCP server")
        
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            print(f"Received from frontend: {data}")
            
            try:
                message = json.loads(data)
                
                # Forward message to MCP
                print(f"Sending to MCP: {message}")
                await mcp_ws.send(json.dumps(message))
                print("Message sent to MCP")
                
                # Get response from MCP
                print("Waiting for MCP response...")
                response = await mcp_ws.recv()
                print(f"Received from MCP: {response}")
                
                # Send response back to frontend
                print("Sending response to frontend")
                await websocket.send_text(response)
                print("Response sent to frontend")
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                error_response = {
                    "type": "error",
                    "content": "Invalid JSON message"
                }
                await websocket.send_text(json.dumps(error_response))
            except websockets.exceptions.ConnectionClosed as e:
                print(f"MCP connection closed: {e}")
                error_response = {
                    "type": "error",
                    "content": "Connection to MCP server lost"
                }
                await websocket.send_text(json.dumps(error_response))
                break
            
    except Exception as e:
        print(f"Error in websocket endpoint: {e}")
        try:
            error_response = {
                "type": "error",
                "content": f"Server error: {str(e)}"
            }
            await websocket.send_text(json.dumps(error_response))
        except:
            pass
    finally:
        if mcp_ws:
            try:
                await mcp_ws.close()
                print("Closed MCP connection")
            except:
                pass

if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001) 