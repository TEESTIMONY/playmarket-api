/**
 * Test WebSocket Component (JavaScript version)
 * 
 * This component provides a simple interface to test WebSocket functionality
 * including connection establishment, message sending/receiving, and authentication.
 */

// Simple WebSocket test component for vanilla JavaScript
export class TestWebSocketComponent {
  constructor(containerId = 'websocket-test-container') {
    this.containerId = containerId;
    this.ws = null;
    this.isConnected = false;
    this.isConnecting = false;
    this.messages = [];
    this.selectedAction = 'echo';
    
    this.testWebSocketUrl = 'ws://localhost:8000/ws/test/';
    
    this.init();
  }

  init() {
    this.render();
    this.bindEvents();
  }

  render() {
    const container = document.getElementById(this.containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
        <h2 class="text-2xl font-bold text-gray-800 mb-6">WebSocket Test Interface</h2>
        
        <!-- Connection Status -->
        <div class="mb-6 p-4 border rounded-lg">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold">Connection Status</h3>
              <p class="text-sm text-gray-600">
                Test WebSocket functionality before implementing auction features
              </p>
            </div>
            <div class="flex items-center space-x-4">
              <div id="status-indicator" class="px-3 py-1 rounded-full text-white text-sm font-medium bg-red-500">
                Disconnected
              </div>
              <button id="connect-btn" class="px-4 py-2 rounded-md font-medium bg-blue-500 text-white">
                Connect
              </button>
              <button id="disconnect-btn" class="px-4 py-2 rounded-md font-medium bg-red-500 text-white" disabled>
                Disconnect
              </button>
            </div>
          </div>
          
          <!-- Authentication Status -->
          <div id="auth-status" class="mt-4 p-3 bg-gray-50 rounded-lg">
            <p class="text-sm">
              Authentication: <span id="auth-text">Checking...</span>
            </p>
          </div>
        </div>

        <!-- Error Display -->
        <div id="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg hidden">
          <p class="text-red-700 text-sm"></p>
        </div>

        <!-- Message Controls -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <!-- Action Selection -->
          <div class="lg:col-span-1">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Action Type
            </label>
            <select id="action-select" class="w-full px-3 py-2 border border-gray-300 rounded-md">
              <option value="echo">Echo Message</option>
              <option value="ping">Ping/Pong</option>
              <option value="test_auth">Test Authentication</option>
              <option value="custom">Custom Message</option>
            </select>
            <p id="action-description" class="text-xs text-gray-500 mt-1">
              Send a message and get it echoed back
            </p>
          </div>

          <!-- Message Input -->
          <div class="lg:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Message
            </label>
            <div class="flex space-x-2">
              <input
                id="message-input"
                type="text"
                placeholder="Enter your message here..."
                class="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              />
              <button id="send-btn" class="px-4 py-2 bg-green-500 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed">
                Send
              </button>
            </div>
          </div>
        </div>

        <!-- Messages Display -->
        <div class="border rounded-lg">
          <div class="flex items-center justify-between p-4 border-b">
            <h3 class="text-lg font-semibold">Messages</h3>
            <button id="clear-btn" class="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded-md">
              Clear
            </button>
          </div>
          <div id="messages-list" class="p-4 max-h-96 overflow-y-auto">
            <p class="text-gray-500 text-center py-8">
              No messages yet. Connect to WebSocket and send a message to get started.
            </p>
          </div>
        </div>

        <!-- Instructions -->
        <div class="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 class="font-semibold text-blue-900 mb-2">Testing Instructions:</h4>
          <ul class="text-sm text-blue-800 space-y-1">
            <li>• Click "Connect" to establish WebSocket connection</li>
            <li>• Use "Echo Message" to test basic message sending/receiving</li>
            <li>• Use "Ping/Pong" to test connection health</li>
            <li>• Use "Test Authentication" to verify JWT token functionality</li>
            <li>• Check the messages panel to see real-time communication</li>
            <li>• Ensure you're logged in to test authenticated features</li>
          </ul>
        </div>
      </div>
    `;
  }

  bindEvents() {
    // DOM elements
    this.statusIndicator = document.getElementById('status-indicator');
    this.connectBtn = document.getElementById('connect-btn');
    this.disconnectBtn = document.getElementById('disconnect-btn');
    this.sendBtn = document.getElementById('send-btn');
    this.messagesList = document.getElementById('messages-list');
    this.errorDiv = document.getElementById('error');
    this.authStatus = document.getElementById('auth-status');
    this.authText = document.getElementById('auth-text');
    this.actionSelect = document.getElementById('action-select');
    this.actionDescription = document.getElementById('action-description');
    this.messageInput = document.getElementById('message-input');
    this.clearBtn = document.getElementById('clear-btn');

    // Event listeners
    this.connectBtn.addEventListener('click', () => this.connectWebSocket());
    this.disconnectBtn.addEventListener('click', () => this.disconnectWebSocket());
    this.sendBtn.addEventListener('click', () => this.sendMessage());
    this.actionSelect.addEventListener('change', () => {
      const descriptions = {
        'echo': 'Send a message and get it echoed back',
        'ping': 'Test connection with ping/pong',
        'test_auth': 'Check if user is authenticated',
        'custom': 'Send a custom message type'
      };
      this.actionDescription.textContent = descriptions[this.actionSelect.value];
    });
    this.messageInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.sendMessage();
    });
    this.clearBtn.addEventListener('click', () => this.clearMessages());

    // Check authentication status
    this.checkAuthStatus();
    setInterval(() => this.checkAuthStatus(), 5000);

    // Add welcome message
    this.addMessage({ type: 'system', message: 'WebSocket Test Interface loaded. Click "Connect" to begin testing.' });
  }

  // Check if user has JWT token
  checkAuthStatus() {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      this.authStatus.className = 'mt-4 p-3 bg-green-50 rounded-lg';
      this.authText.textContent = '✅ JWT Token Available';
    } else {
      this.authStatus.className = 'mt-4 p-3 bg-red-50 rounded-lg';
      this.authText.textContent = '❌ No JWT Token - Some features require authentication';
    }
  }

  // Update connection status
  updateStatus(status, isConnecting = false) {
    this.isConnected = status === 'connected';
    this.isConnecting = isConnecting;
    
    if (status === 'connected') {
      this.statusIndicator.className = 'px-3 py-1 rounded-full text-white text-sm font-medium bg-green-500';
      this.statusIndicator.textContent = 'Connected';
      this.connectBtn.disabled = true;
      this.disconnectBtn.disabled = false;
      this.sendBtn.disabled = false;
    } else if (status === 'connecting') {
      this.statusIndicator.className = 'px-3 py-1 rounded-full text-white text-sm font-medium bg-yellow-500';
      this.statusIndicator.textContent = 'Connecting...';
      this.connectBtn.disabled = true;
      this.disconnectBtn.disabled = true;
      this.sendBtn.disabled = true;
    } else {
      this.statusIndicator.className = 'px-3 py-1 rounded-full text-white text-sm font-medium bg-red-500';
      this.statusIndicator.textContent = 'Disconnected';
      this.connectBtn.disabled = false;
      this.disconnectBtn.disabled = true;
      this.sendBtn.disabled = true;
    }
  }

  // Show error
  showError(message) {
    const errorText = this.errorDiv.querySelector('p');
    errorText.textContent = message;
    this.errorDiv.classList.remove('hidden');
    setTimeout(() => {
      this.errorDiv.classList.add('hidden');
    }, 5000);
  }

  // Add message to the list
  addMessage(message) {
    this.messages.push(message);
    
    // Clear existing content
    this.messagesList.innerHTML = '';
    
    if (this.messages.length === 0) {
      this.messagesList.innerHTML = '<p class="text-gray-500 text-center py-8">No messages yet. Connect to WebSocket and send a message to get started.</p>';
      return;
    }

    this.messages.forEach((msg, index) => {
      const messageDiv = document.createElement('div');
      messageDiv.className = `p-3 rounded-lg border ${
        msg.type === 'sent' ? 'bg-blue-50 border-blue-200' :
        msg.type === 'system' ? 'bg-gray-50 border-gray-200' :
        'bg-green-50 border-green-200'
      }`;
      
      const headerDiv = document.createElement('div');
      headerDiv.className = 'flex items-center justify-between mb-2';
      headerDiv.innerHTML = `
        <span class="text-xs text-gray-600 font-medium">${msg.type.toUpperCase()}</span>
        <span class="text-xs text-gray-500">${new Date(msg.timestamp || Date.now()).toLocaleTimeString()}</span>
      `;
      
      const contentDiv = document.createElement('div');
      contentDiv.className = 'text-sm';
      
      if (msg.message) {
        contentDiv.textContent = msg.message;
      } else if (msg.authenticated !== undefined) {
        contentDiv.innerHTML = `
          <p>Authenticated: ${msg.authenticated ? 'Yes' : 'No'}</p>
          ${msg.username ? `<p>Username: ${msg.username}</p>` : ''}
        `;
      } else if (msg.status) {
        contentDiv.textContent = `Status: ${msg.status}`;
      } else if (msg.features && Array.isArray(msg.features)) {
        contentDiv.innerHTML = `
          <p class="font-medium">Features:</p>
          <ul class="list-disc list-inside text-sm">
            ${msg.features.map(feature => `<li>${feature}</li>`).join('')}
          </ul>
        `;
      }
      
      messageDiv.appendChild(headerDiv);
      messageDiv.appendChild(contentDiv);
      this.messagesList.appendChild(messageDiv);
    });
    
    this.messagesList.scrollTop = this.messagesList.scrollHeight;
  }

  // Connect to WebSocket
  connectWebSocket() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this.updateStatus('connecting', true);
    this.addMessage({ type: 'system', message: 'Attempting to connect to WebSocket...' });

    try {
      this.ws = new WebSocket(this.testWebSocketUrl);

      this.ws.onopen = () => {
        this.updateStatus('connected');
        this.addMessage({ type: 'system', message: 'Connected to WebSocket successfully!' });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.addMessage(data);
        } catch (err) {
          console.error('Error parsing message:', err);
          this.showError('Failed to parse message');
        }
      };

      this.ws.onclose = (event) => {
        this.updateStatus('disconnected');
        this.addMessage({ 
          type: 'system', 
          message: `Disconnected: ${event.code} - ${event.reason}` 
        });
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.showError('WebSocket connection error');
        this.updateStatus('disconnected');
      };

    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      this.showError('Failed to create WebSocket connection');
      this.updateStatus('disconnected');
    }
  }

  // Disconnect from WebSocket
  disconnectWebSocket() {
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    this.updateStatus('disconnected');
    this.addMessage({ type: 'system', message: 'Disconnected from WebSocket' });
  }

  // Send message to WebSocket
  sendMessage() {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.showError('WebSocket not connected');
      return;
    }

    const messageText = this.messageInput.value.trim();
    if (!messageText) {
      this.showError('Please enter a message');
      return;
    }

    try {
      const message = {
        type: this.actionSelect.value,
        message: messageText,
        timestamp: new Date().toISOString()
      };

      this.ws.send(JSON.stringify(message));
      this.addMessage({ type: 'sent', ...message });
      this.messageInput.value = '';
      this.showError(null);
    } catch (err) {
      console.error('Failed to send message:', err);
      this.showError('Failed to send message');
    }
  }

  // Clear messages
  clearMessages() {
    this.messages = [];
    this.messagesList.innerHTML = '<p class="text-gray-500 text-center py-8">No messages yet. Connect to WebSocket and send a message to get started.</p>';
  }
}

// Auto-initialize if container exists
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('websocket-test-container');
    if (container) {
      new TestWebSocketComponent();
    }
  });
}