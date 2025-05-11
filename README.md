# Generic MCP Client Chat

A simple chat client that connects to an MCP (Model Control Protocol) server, allowing you to interact with LLMs and use MCP tools.

Vibe coded using cursor.

## Goals

I believe we should have completely generic agents and completely generic UIs.

People should not need to write new code to write new agents. This UI is an experiment in building this generic MCP client.

## Features

- Real-time chat interface with Claude 3 Sonnet
- Tool support (currently implements an echo tool)
- WebSocket-based communication
- Modern, responsive UI
- Connection status monitoring
- Error handling and user feedback

## Prerequisites

- Python 3.8 or higher
- Anthropic API key

## Setup

1. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install websockets anthropic python-dotenv
```

3. Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Running the Application

1. Start the MCP server:
```bash
python mcp_server.py
```

2. Open your web browser and navigate to:
```
http://localhost:8001/static/index.html
```

## Tool Support

The system currently supports the following tool:

### Echo Tool
- **Name**: echo
- **Description**: Echoes back the input message
- **Parameters**: 
  ```json
  {
    "message": "text to echo"
  }
  ```

To use the echo tool, simply ask Claude to use it. For example:
- "Can you use the echo tool to repeat back my message?"
- "Please use the echo tool to echo back: Hello World!"

## Project Structure

- `mcp_server.py`: WebSocket server that handles communication with Claude's API
- `static/`: Frontend files
  - `index.html`: Main chat interface with WebSocket client and UI logic
- `.env`: Configuration file (create this)

## Error Handling

The system handles various error cases:
- Invalid JSON messages
- Unknown tool calls
- Connection issues
- API errors

All errors are displayed to the user in the chat interface with appropriate styling.

## Development

To add new tools:
1. Add the tool definition to the `tools` dictionary in `MCPServer.__init__`
2. Update the system prompt in `get_llm_response` to include the new tool
3. Implement the tool handling logic in `handle_message`

## License

[Your chosen license]

## Contributing

[Your contribution guidelines] 