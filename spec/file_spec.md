# File System MCP Server Specification

This document specifies the tools provided by the File System MCP server, which enables file system navigation capabilities.

## Server Information

- **Name**: File System Tools Server
- **Description**: A server providing file system navigation tools
- **Version**: 1.0.0
- **Port**: 8003
- **Endpoint**: http://localhost:8003/mcp

## Tools

### List Directory Contents

**Name**: ls

**Description**: Lists the contents of a directory, showing files and folders with visual indicators.

**Parameters**:
```json
{
    "path": "string"  // Optional, defaults to current directory
}
```

**Returns**: A formatted string showing the directory contents, with:
- 📁 for directories
- 📄 for files
- Sorted alphabetically
- One item per line

**Example**:
```json
{
    "path": "."
}
```

**Example Response**:
```
Contents of .:
📁 example_mcp_servers/
📄 README.md
📄 requirements.txt
📄 server.py
```

### Change Directory

**Name**: cd

**Description**: Changes the current working directory. The server maintains the current directory state between calls.

**Parameters**:
```json
{
    "path": "string"  // Required, path to change to
}
```

**Returns**: A confirmation message with the new current directory path.

**Example**:
```json
{
    "path": "example_mcp_servers"
}
```

**Example Response**:
```
Changed directory to: /home/user/project/example_mcp_servers
```

## Error Handling

Both tools handle the following error cases:
- Non-existent paths
- Paths that are not directories
- Permission errors
- Invalid path formats

Error responses are prefixed with "Error:" and include a descriptive message.

## State Management

The server maintains the current working directory state between tool calls. This means:
- `cd` commands affect subsequent `ls` commands
- The state persists until the server is restarted
- Relative paths are resolved from the current directory

## Security Considerations

- The server only provides read-only access to the file system
- Paths are resolved relative to the server's working directory
- No file modification operations are provided
- All paths are validated before use 