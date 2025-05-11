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

1. Clone the repository:
```bash
git clone https://github.com/rom1504/generic-mcp-client-chat.git
cd generic-mcp-client-chat
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install websockets anthropic python-dotenv
```

4. Create a `.env` file in the project root:
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

MIT License

Copyright (c) 2024 Romain Beaumont

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contributing

[Your contribution guidelines] 