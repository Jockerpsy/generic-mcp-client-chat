let ws = null;
const chatContainer = document.getElementById('chat-container');
const messageInput = document.getElementById('message-input');

function connect() {
    ws = new WebSocket('ws://localhost:8001/ws');
    
    ws.onopen = () => {
        console.log('Connected to server');
        addMessage('System', 'Connected to server', 'assistant-message');
    };
    
    ws.onmessage = (event) => {
        console.log('Received message:', event.data);
        try {
            const response = JSON.parse(event.data);
            if (response.type === 'error') {
                addMessage('Error', response.content, 'assistant-message');
            } else if (response.type === 'message') {
                addMessage('Assistant', response.content, 'assistant-message');
            } else if (response.type === 'tool_response') {
                addMessage('Tool Response', response.content, 'assistant-message');
            } else {
                addMessage('Assistant', JSON.stringify(response), 'assistant-message');
            }
        } catch (e) {
            console.error('Error parsing message:', e);
            addMessage('Error', 'Invalid response from server', 'assistant-message');
        }
    };
    
    ws.onclose = () => {
        console.log('Disconnected from server');
        addMessage('System', 'Disconnected from server', 'assistant-message');
        // Try to reconnect after 5 seconds
        setTimeout(connect, 5000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        addMessage('System', 'Error connecting to server', 'assistant-message');
    };
}

function addMessage(sender, content, className) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${className}`;
    messageDiv.innerHTML = `<strong>${sender}:</strong> ${content}`;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function sendMessage() {
    const message = messageInput.value.trim();
    if (message && ws && ws.readyState === WebSocket.OPEN) {
        const messageObj = {
            type: 'message',
            content: message
        };
        
        console.log('Sending message:', messageObj);
        ws.send(JSON.stringify(messageObj));
        addMessage('You', message, 'user-message');
        messageInput.value = '';
    } else {
        console.error('Cannot send message:', {
            message,
            wsReady: ws?.readyState,
            wsOpen: ws?.readyState === WebSocket.OPEN
        });
    }
}

// Handle Enter key press
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Connect when the page loads
connect(); 