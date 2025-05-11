# MCP Chat Client

A simple chat client that connects to an MCP (Model Control Protocol) server, allowing you to interact with LLMs and use MCP tools.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with your MCP server configuration:
```
MCP_URI=ws://your-mcp-server:port/mcp
```

## Running the Application

1. Start the backend server:
```bash
python server.py
```

2. Open your web browser and navigate to:
```
http://localhost:8001/static/index.html
```

## Features

- Real-time chat interface
- WebSocket communication with MCP server
- Automatic reconnection on disconnection
- Simple and clean UI
- Support for MCP tools and LLM interactions

## Project Structure

- `server.py`: FastAPI backend server
- `static/`: Frontend files
  - `index.html`: Main chat interface
  - `app.js`: WebSocket client and UI logic
- `requirements.txt`: Python dependencies
- `.env`: Configuration file (create this) 