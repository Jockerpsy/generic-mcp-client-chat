async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessageToChat('user', message);
    messageInput.value = '';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        addMessageToChat('assistant', data.response);
    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('error', 'Error sending message: ' + error.message);
    }
}

function addServer() {
    const serverList = document.getElementById('serverList');
    const serverItem = document.createElement('div');
    serverItem.className = 'server-item';
    serverItem.innerHTML = `
        <input type="text" placeholder="Server name" />
        <input type="text" placeholder="Server URL" value="http://localhost:8000/mcp" />
        <button onclick="connectToServer(this)">Connect</button>
        <span class="server-status disconnected">Disconnected</span>
    `;
    serverList.appendChild(serverItem);
}

async function connectToServer(button) {
    const serverItem = button.parentElement;
    const nameInput = serverItem.querySelector('input:nth-child(1)');
    const urlInput = serverItem.querySelector('input:nth-child(2)');
    const statusSpan = serverItem.querySelector('.server-status');
    
    const serverName = nameInput.value.trim();
    const serverUrl = urlInput.value.trim();

    if (!serverName || !serverUrl) {
        addMessageToChat('error', 'Please enter both server name and URL');
        return;
    }

    try {
        statusSpan.textContent = 'Connecting...';
        statusSpan.className = 'server-status disconnected';

        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                server_name: serverName,
                server_url: serverUrl
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to connect: ${response.statusText}`);
        }

        const data = await response.json();
        statusSpan.textContent = 'Connected';
        statusSpan.className = 'server-status connected';
        button.textContent = 'Disconnect';
        button.onclick = () => disconnectFromServer(button);
        
        // Update server list in chat
        updateServerList();
    } catch (error) {
        console.error('Connection error:', error);
        statusSpan.textContent = 'Connection failed';
        statusSpan.className = 'server-status disconnected';
        addMessageToChat('error', `Error: ${error.message}`);
    }
}

async function disconnectFromServer(button) {
    const serverItem = button.parentElement;
    const serverName = serverItem.querySelector('input:first-child').value.trim();
    const statusSpan = serverItem.querySelector('.server-status');

    try {
        const response = await fetch('/api/disconnect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ server_name: serverName })
        });

        if (!response.ok) {
            throw new Error(`Failed to disconnect: ${response.statusText}`);
        }

        statusSpan.textContent = 'Disconnected';
        statusSpan.className = 'server-status disconnected';
        button.textContent = 'Connect';
        button.onclick = () => connectToServer(button);
        
        // Update server list in chat
        updateServerList();
    } catch (error) {
        console.error('Disconnection error:', error);
        addMessageToChat('error', `Error: ${error.message}`);
    }
}

async function updateServerList() {
    try {
        const response = await fetch('/api/servers');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.servers.length === 0) {
            addMessageToChat('system', 'No MCP servers connected. Please add a server.');
        } else {
            addMessageToChat('system', `Connected to ${data.servers.length} MCP servers: ${data.servers.join(', ')}`);
        }
    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('error', 'Error updating server list: ' + error.message);
    }
}

function addMessageToChat(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Get the original Add Server button
    const addButton = document.querySelector('.add-server-button');
    
    // Clear the default server list but preserve the Add Server button
    const serverList = document.getElementById('serverList');
    const serverItems = serverList.querySelectorAll('.server-item');
    serverItems.forEach(item => item.remove());
    
    // Get current server connections
    try {
        const response = await fetch('/api/servers');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Add each connected server to the list
        for (const serverName of data.servers) {
            const serverItem = document.createElement('div');
            serverItem.className = 'server-item';
            serverItem.innerHTML = `
                <input type="text" placeholder="Server name" value="${serverName}" readonly />
                <input type="text" placeholder="Server URL" value="http://localhost:${serverName === 'default_mcp' ? '8000' : '8002'}/mcp" readonly />
                <button onclick="disconnectFromServer(this)">Disconnect</button>
                <span class="server-status connected">Connected</span>
            `;
            serverList.insertBefore(serverItem, addButton);
        }
        
        // Update server list message
        if (data.servers.length === 0) {
            addMessageToChat('system', 'No MCP servers connected. Please add a server.');
        } else {
            addMessageToChat('system', `Connected to ${data.servers.length} MCP servers: ${data.servers.join(', ')}`);
        }
    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('error', 'Error loading server list: ' + error.message);
    }
    
    // Add enter key handler for message input
    const messageInput = document.getElementById('messageInput');
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}); 