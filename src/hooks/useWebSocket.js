/**
 * WebSocket hook for React applications (JavaScript version)
 * Provides WebSocket connection management with authentication and error handling
 */

// Simple WebSocket manager for vanilla JavaScript or React without TypeScript
export class WebSocketManager {
  constructor(options = {}) {
    this.url = options.url || '';
    this.onOpen = options.onOpen || (() => {});
    this.onClose = options.onClose || (() => {});
    this.onError = options.onError || (() => {});
    this.onMessage = options.onMessage || (() => {});
    this.reconnectInterval = options.reconnectInterval || 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10;

    this.ws = null;
    this.reconnectTimeout = null;
    this.reconnectAttempts = 0;
    this.isConnected = false;
    this.isConnecting = false;
    this.lastMessage = null;
    this.error = null;
  }

  // Generate WebSocket URL with authentication token
  getWebSocketURL() {
    const token = localStorage.getItem('jwt_token');
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    // Replace http:// with ws:// and add token as query parameter
    const wsUrl = this.url.replace(/^http/, 'ws');
    return `${wsUrl}?token=${encodeURIComponent(token)}`;
  }

  // Handle incoming messages
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      this.lastMessage = data;
      
      // Call custom message handler if provided
      if (this.onMessage) {
        this.onMessage(data);
      }
    } catch (err) {
      console.error('Error parsing WebSocket message:', err);
      this.error = 'Failed to parse message';
    }
  }

  // Handle WebSocket connection open
  handleOpen() {
    this.isConnected = true;
    this.isConnecting = false;
    this.error = null;
    this.reconnectAttempts = 0;
    
    console.log('WebSocket connected successfully');
    
    // Call custom open handler if provided
    if (this.onOpen) {
      this.onOpen();
    }
  }

  // Handle WebSocket connection close
  handleClose(event) {
    this.isConnected = false;
    this.isConnecting = false;
    
    console.log('WebSocket disconnected:', event.code, event.reason);
    
    // Call custom close handler if provided
    if (this.onClose) {
      this.onClose();
    }
    
    // Attempt to reconnect if not manually closed
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnect();
    }
  }

  // Handle WebSocket errors
  handleError(event) {
    console.error('WebSocket error:', event);
    this.error = 'WebSocket connection error';
    
    // Call custom error handler if provided
    if (this.onError) {
      this.onError(event);
    }
  }

  // Connect to WebSocket
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      this.isConnecting = true;
      this.error = null;
      
      const wsUrl = this.getWebSocketURL();
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onclose = (event) => this.handleClose(event);
      this.ws.onerror = (event) => this.handleError(event);
      
    } catch (err) {
      console.error('Failed to connect to WebSocket:', err);
      this.error = err instanceof Error ? err.message : 'Connection failed';
      this.isConnecting = false;
      
      // Attempt to reconnect after delay
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectTimeout = setTimeout(() => {
          this.reconnect();
        }, this.reconnectInterval);
      }
    }
  }

  // Disconnect from WebSocket
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
  }

  // Reconnect to WebSocket
  reconnect() {
    this.disconnect();
    
    this.reconnectAttempts++;
    console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, this.reconnectInterval);
  }

  // Send message to WebSocket
  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (err) {
        console.error('Failed to send WebSocket message:', err);
        this.error = 'Failed to send message';
      }
    } else {
      console.warn('WebSocket not connected, cannot send message');
      this.error = 'WebSocket not connected';
    }
  }

  // Get current connection status
  getStatus() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      lastMessage: this.lastMessage,
      error: this.error
    };
  }
}

// Simple hook-like function for React (without TypeScript)
export function createWebSocketHook(options) {
  const manager = new WebSocketManager(options);
  
  // Auto-connect on creation
  manager.connect();
  
  // Return methods for React component usage
  return {
    connect: () => manager.connect(),
    disconnect: () => manager.disconnect(),
    sendMessage: (message) => manager.sendMessage(message),
    reconnect: () => manager.reconnect(),
    getStatus: () => manager.getStatus()
  };
}