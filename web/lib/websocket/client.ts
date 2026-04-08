/**
 * WebSocket Client for JARVIS 2.0
 * 
 * Provides real-time bidirectional communication with the API server.
 * Features: chat streaming, typing indicators, presence system, notifications.
 */

export enum EventType {
  MESSAGE = "message",
  TYPING = "typing", 
  PRESENCE = "presence",
  SYSTEM = "system",
  PLUGIN = "plugin",
  NOTIFICATION = "notification",
  ERROR = "error",
  HEARTBEAT = "heartbeat",
}

export interface WebSocketMessage {
  type: EventType;
  data: any;
  timestamp?: number;
  user_id?: number;
}

export interface ChatMessage {
  content: string;
  conversation_id?: string;
  streaming?: boolean;
  model?: string;
}

export interface TypingIndicator {
  is_typing: boolean;
  conversation_id?: string;
}

export interface PresenceUpdate {
  status: "online" | "away" | "busy" | "offline";
  last_seen?: string;
}

export interface WebSocketConfig {
  url: string;
  token: string;
  autoReconnect?: boolean;
  heartbeatInterval?: number;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
}

export type MessageHandler = (message: WebSocketMessage) => void;
export type ErrorHandler = (error: Event | Error) => void;
export type ConnectionHandler = () => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private messageHandlers: Map<EventType, MessageHandler[]> = new Map();
  private errorHandlers: ErrorHandler[] = [];
  private connectHandlers: ConnectionHandler[] = [];
  private disconnectHandlers: ConnectionHandler[] = [];
  
  private isConnected = false;
  private reconnectAttempts = 0;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  
  constructor(config: WebSocketConfig) {
    this.config = {
      autoReconnect: true,
      heartbeatInterval: 30000, // 30 seconds
      reconnectDelay: 5000, // 5 seconds
      maxReconnectAttempts: 5,
      ...config,
    };
    
    // Initialize handler maps
    Object.values(EventType).forEach(type => {
      this.messageHandlers.set(type, []);
    });
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      const wsUrl = `${this.config.url}?token=${this.config.token}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("WebSocket connected");
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Notify handlers
        this.connectHandlers.forEach(handler => handler());
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
          this.notifyErrorHandlers(new Error("Invalid message format"));
        }
      };

      this.ws.onclose = (event) => {
        console.log("WebSocket disconnected:", event.code, event.reason);
        this.isConnected = false;
        
        // Stop heartbeat
        this.stopHeartbeat();
        
        // Notify handlers
        this.disconnectHandlers.forEach(handler => handler());

        // Auto-reconnect if enabled and not a deliberate close
        if (this.config.autoReconnect && event.code !== 1000) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.notifyErrorHandlers(error);
        reject(error);
      };
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.config.autoReconnect = false; // Disable auto-reconnect
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }
  }

  /**
   * Send message to server
   */
  send(message: WebSocketMessage): void {
    if (!this.isConnected || !this.ws) {
      throw new Error("WebSocket not connected");
    }

    // Add timestamp if not present
    if (!message.timestamp) {
      message.timestamp = Date.now() / 1000;
    }

    const messageStr = JSON.stringify(message);
    this.ws.send(messageStr);
  }

  /**
   * Send chat message
   */
  sendChatMessage(content: string, options: Partial<ChatMessage> = {}): void {
    const message: WebSocketMessage = {
      type: EventType.MESSAGE,
      data: {
        content,
        conversation_id: options.conversation_id || "default",
        streaming: options.streaming || true,
        model: options.model,
      },
    };

    this.send(message);
  }

  /**
   * Send typing indicator
   */
  sendTypingIndicator(isTyping: boolean, conversationId?: string): void {
    const message: WebSocketMessage = {
      type: EventType.TYPING,
      data: {
        is_typing: isTyping,
        conversation_id: conversationId || "default",
      },
    };

    this.send(message);
  }

  /**
   * Update presence status
   */
  updatePresence(status: PresenceUpdate["status"]): void {
    const message: WebSocketMessage = {
      type: EventType.PRESENCE,
      data: { status },
    };

    this.send(message);
  }

  /**
   * Send system command
   */
  sendSystemCommand(command: string, data: any = {}): void {
    const message: WebSocketMessage = {
      type: EventType.SYSTEM,
      data: { command, ...data },
    };

    this.send(message);
  }

  /**
   * Register message handler
   */
  onMessage(type: EventType, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      handlers.push(handler);
    }
  }

  /**
   * Remove message handler
   */
  offMessage(type: EventType, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Register error handler
   */
  onError(handler: ErrorHandler): void {
    this.errorHandlers.push(handler);
  }

  /**
   * Register connection handler
   */
  onConnect(handler: ConnectionHandler): void {
    this.connectHandlers.push(handler);
  }

  /**
   * Register disconnection handler
   */
  onDisconnect(handler: ConnectionHandler): void {
    this.disconnectHandlers.push(handler);
  }

  /**
   * Get connection status
   */
  getStatus(): {
    connected: boolean;
    readyState: number | null;
    reconnectAttempts: number;
  } {
    return {
      connected: this.isConnected,
      readyState: this.ws?.readyState || null,
      reconnectAttempts: this.reconnectAttempts,
    };
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error(`Error in message handler for ${message.type}:`, error);
        }
      });
    } else {
      console.warn("No handlers for message type:", message.type);
    }
  }

  /**
   * Notify error handlers
   */
  private notifyErrorHandlers(error: Event | Error): void {
    this.errorHandlers.forEach(handler => {
      try {
        handler(error);
      } catch (err) {
        console.error("Error in error handler:", err);
      }
    });
  }

  /**
   * Start heartbeat timer
   */
  private startHeartbeat(): void {
    if (this.config.heartbeatInterval && this.config.heartbeatInterval > 0) {
      this.heartbeatTimer = setInterval(() => {
        if (this.isConnected) {
          this.send({
            type: EventType.HEARTBEAT,
            data: { client_time: Date.now() / 1000 },
          });
        }
      }, this.config.heartbeatInterval);
    }
  }

  /**
   * Stop heartbeat timer
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= (this.config.maxReconnectAttempts || 5)) {
      console.error("Max reconnection attempts reached");
      this.notifyErrorHandlers(new Error("Max reconnection attempts reached"));
      return;
    }

    const delay = this.config.reconnectDelay! * Math.pow(2, this.reconnectAttempts); // Exponential backoff
    this.reconnectAttempts++;

    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    this.reconnectTimer = setTimeout(() => {
      console.log(`Reconnect attempt ${this.reconnectAttempts}...`);
      this.connect().catch(error => {
        console.error("Reconnection failed:", error);
        // scheduleReconnect will be called again via onclose handler
      });
    }, delay);
  }
}