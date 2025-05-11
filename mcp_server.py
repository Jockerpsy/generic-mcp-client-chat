import asyncio
import websockets
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

class MCPServer:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("Warning: ANTHROPIC_API_KEY not set in .env file")
        
        self.client = Anthropic(api_key=self.api_key)
        self.conversation_history = []
        
        self.tools = {
            "echo": {
                "name": "echo",
                "description": "Echoes back the input message",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back"
                        }
                    },
                    "required": ["message"]
                }
            }
        }

    async def get_llm_response(self, message: str) -> str:
        if not self.api_key:
            return "Error: Anthropic API key not configured. Please set ANTHROPIC_API_KEY in .env file"
        
        try:
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": message})
            
            # Get response from Claude
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0.7,
                messages=self.conversation_history
            )
            
            # Add assistant response to history
            assistant_message = response.content[0].text
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return assistant_message
            
        except Exception as e:
            print(f"Error calling Anthropic API: {e}")
            return f"Error: Failed to get response from Claude: {str(e)}"

    async def handle_message(self, websocket, message: Dict[str, Any]):
        print(f"Handling message: {message}")
        
        if message.get("type") == "message":
            # Get response from LLM
            user_message = message.get('content', '')
            print(f"Getting LLM response for: {user_message}")
            llm_response = await self.get_llm_response(user_message)
            
            response = {
                "type": "message",
                "content": llm_response
            }
            print(f"Sending response: {response}")
            await websocket.send(json.dumps(response))
        
        elif message.get("type") == "tool_call":
            # Handle tool calls
            tool_name = message.get("name")
            if tool_name == "echo":
                params = message.get("parameters", {})
                response = {
                    "type": "tool_response",
                    "name": "echo",
                    "content": params.get("message", "")
                }
                print(f"Sending tool response: {response}")
                await websocket.send(json.dumps(response))
            else:
                response = {
                    "type": "error",
                    "content": f"Unknown tool: {tool_name}"
                }
                print(f"Sending error response: {response}")
                await websocket.send(json.dumps(response))
        else:
            response = {
                "type": "error",
                "content": f"Unknown message type: {message.get('type')}"
            }
            print(f"Sending error response: {response}")
            await websocket.send(json.dumps(response))

    async def handle_client(self, websocket, path):
        print(f"New connection from {websocket.remote_address} on path {path}")
        
        if path != "/mcp":
            print(f"Invalid path: {path}")
            await websocket.close(1008, "Invalid path")
            return
            
        try:
            async for message in websocket:
                try:
                    print(f"Received raw message: {message}")
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    response = {
                        "type": "error",
                        "content": "Invalid JSON message"
                    }
                    await websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

async def main():
    server = MCPServer()
    async with websockets.serve(server.handle_client, "localhost", 8000):
        print("MCP Server running on ws://localhost:8000/mcp")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main()) 