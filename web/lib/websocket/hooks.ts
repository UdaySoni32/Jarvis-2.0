/**
 * React Hooks for WebSocket Integration
 * 
 * Provides React hooks for easy WebSocket integration with automatic
 * connection management and cleanup.
 */

'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '../store/auth';
import { 
  WebSocketClient, 
  WebSocketMessage, 
  EventType,
  MessageHandler,
  ErrorHandler,
  ConnectionHandler
} from './client';

interface UseWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  onMessage?: MessageHandler;
  onError?: ErrorHandler;
  onConnect?: ConnectionHandler;
  onDisconnect?: ConnectionHandler;
}

interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: Error | null;
  reconnectAttempts: number;
}

/**
 * Main WebSocket hook
 */
export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { token } = useAuthStore();
  const [state, setState] = useState<WebSocketState>({
    connected: false,
    connecting: false,
    error: null,
    reconnectAttempts: 0,
  });

  const clientRef = useRef<WebSocketClient | null>(null);
  const handlersRef = useRef<{
    onMessage?: MessageHandler;
    onError?: ErrorHandler;
    onConnect?: ConnectionHandler;
    onDisconnect?: ConnectionHandler;
  }>({});

  // Store handlers in ref to avoid re-creating client on handler changes
  handlersRef.current = {
    onMessage: options.onMessage,
    onError: options.onError,
    onConnect: options.onConnect,
    onDisconnect: options.onDisconnect,
  };

  const connect = useCallback(async () => {
    if (!token) {
      setState(prev => ({ 
        ...prev, 
        error: new Error('No authentication token available') 
      }));
      return;
    }

    if (clientRef.current?.getStatus().connected) {
      return; // Already connected
    }

    setState(prev => ({ ...prev, connecting: true, error: null }));

    try {
      const wsUrl = options.url || `ws://localhost:8000/api/v1/ws/chat`;
      
      clientRef.current = new WebSocketClient({
        url: wsUrl,
        token,
        autoReconnect: true,
      });

      // Set up handlers
      if (handlersRef.current.onMessage) {
        // Listen to all message types for general handler
        Object.values(EventType).forEach(type => {
          clientRef.current!.onMessage(type, handlersRef.current.onMessage!);
        });
      }

      if (handlersRef.current.onError) {
        clientRef.current.onError(handlersRef.current.onError);
      }

      clientRef.current.onConnect(() => {
        setState(prev => ({ 
          ...prev, 
          connected: true, 
          connecting: false, 
          error: null,
          reconnectAttempts: 0
        }));
        handlersRef.current.onConnect?.();
      });

      clientRef.current.onDisconnect(() => {
        setState(prev => ({ ...prev, connected: false }));
        handlersRef.current.onDisconnect?.();
      });

      clientRef.current.onError((error) => {
        setState(prev => ({ 
          ...prev, 
          error: error instanceof Error ? error : new Error('WebSocket error'),
          connecting: false
        }));
      });

      await clientRef.current.connect();

    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error : new Error('Connection failed'),
        connecting: false
      }));
    }
  }, [token, options.url]);

  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }
    setState({
      connected: false,
      connecting: false,
      error: null,
      reconnectAttempts: 0,
    });
  }, []);

  const send = useCallback((message: WebSocketMessage) => {
    if (!clientRef.current) {
      throw new Error('WebSocket not connected');
    }
    clientRef.current.send(message);
  }, []);

  const sendChatMessage = useCallback((content: string, options: any = {}) => {
    if (!clientRef.current) {
      throw new Error('WebSocket not connected');
    }
    clientRef.current.sendChatMessage(content, options);
  }, []);

  const sendTypingIndicator = useCallback((isTyping: boolean, conversationId?: string) => {
    if (!clientRef.current) return;
    clientRef.current.sendTypingIndicator(isTyping, conversationId);
  }, []);

  const updatePresence = useCallback((status: "online" | "away" | "busy" | "offline") => {
    if (!clientRef.current) return;
    clientRef.current.updatePresence(status);
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (options.autoConnect !== false && token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [options.autoConnect, token]); // Don't include connect/disconnect to avoid loops

  // Update reconnect attempts in state
  useEffect(() => {
    const interval = setInterval(() => {
      if (clientRef.current) {
        const status = clientRef.current.getStatus();
        setState(prev => {
          if (prev.reconnectAttempts !== status.reconnectAttempts) {
            return { ...prev, reconnectAttempts: status.reconnectAttempts };
          }
          return prev;
        });
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return {
    ...state,
    connect,
    disconnect,
    send,
    sendChatMessage,
    sendTypingIndicator,
    updatePresence,
    client: clientRef.current,
  };
}

/**
 * Hook for chat-specific WebSocket functionality
 */
export function useChatWebSocket(conversationId: string = 'default') {
  const [messages, setMessages] = useState<any[]>([]);
  const [typingUsers, setTypingUsers] = useState<number[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case EventType.MESSAGE:
        const { data } = message;
        
        if (data.streaming && data.status === 'streaming') {
          // Update streaming message
          setStreamingMessage(data.full_content || data.content);
          setIsStreaming(true);
        } else if (data.streaming && data.status === 'completed') {
          // Finalize streaming message
          setMessages(prev => [...prev, {
            id: Date.now(),
            content: data.content,
            user_type: data.user_type,
            conversation_id: data.conversation_id,
            timestamp: message.timestamp,
          }]);
          setStreamingMessage('');
          setIsStreaming(false);
        } else if (!data.streaming) {
          // Regular message
          setMessages(prev => [...prev, {
            id: Date.now(),
            content: data.content,
            user_type: data.user_type,
            conversation_id: data.conversation_id,
            timestamp: message.timestamp,
          }]);
        }
        break;

      case EventType.TYPING:
        const typingData = data;
        if (typingData.conversation_id === conversationId) {
          setTypingUsers(typingData.typing_users || []);
        }
        break;
    }
  }, [conversationId]);

  const ws = useWebSocket({
    autoConnect: true,
    onMessage: handleMessage,
  });

  const sendMessage = useCallback((content: string, streaming = true) => {
    // Add user message to UI immediately
    setMessages(prev => [...prev, {
      id: Date.now(),
      content,
      user_type: 'user',
      conversation_id: conversationId,
      timestamp: Date.now() / 1000,
    }]);

    // Send to server
    ws.sendChatMessage(content, {
      conversation_id: conversationId,
      streaming,
    });
  }, [ws, conversationId]);

  const sendTyping = useCallback((isTyping: boolean) => {
    ws.sendTypingIndicator(isTyping, conversationId);
  }, [ws, conversationId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    ...ws,
    messages,
    typingUsers,
    streamingMessage,
    isStreaming,
    sendMessage,
    sendTyping,
    clearMessages,
  };
}

/**
 * Hook for presence/user status
 */
export function usePresence() {
  const [onlineUsers, setOnlineUsers] = useState<any[]>([]);
  const [userPresence, setUserPresence] = useState<Record<number, string>>({});

  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === EventType.PRESENCE) {
      const { user_id, status } = message.data;
      setUserPresence(prev => ({
        ...prev,
        [user_id]: status,
      }));
    } else if (message.type === EventType.SYSTEM) {
      const { command, users } = message.data;
      if (command === 'online_users_response') {
        setOnlineUsers(users || []);
      }
    }
  }, []);

  const ws = useWebSocket({
    autoConnect: true,
    onMessage: handleMessage,
  });

  const getOnlineUsers = useCallback(() => {
    ws.client?.sendSystemCommand('get_online_users');
  }, [ws.client]);

  const setPresenceStatus = useCallback((status: "online" | "away" | "busy" | "offline") => {
    ws.updatePresence(status);
  }, [ws]);

  // Get online users on connect
  useEffect(() => {
    if (ws.connected) {
      getOnlineUsers();
    }
  }, [ws.connected, getOnlineUsers]);

  return {
    ...ws,
    onlineUsers,
    userPresence,
    getOnlineUsers,
    setPresenceStatus,
  };
}

/**
 * Hook for system notifications
 */
export function useNotifications() {
  const [notifications, setNotifications] = useState<any[]>([]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === EventType.NOTIFICATION) {
      setNotifications(prev => [...prev, {
        id: Date.now(),
        ...message.data,
        timestamp: message.timestamp,
      }]);
    } else if (message.type === EventType.ERROR) {
      setNotifications(prev => [...prev, {
        id: Date.now(),
        type: 'error',
        message: message.data.error || 'Unknown error',
        timestamp: message.timestamp,
      }]);
    }
  }, []);

  const ws = useWebSocket({
    autoConnect: true,
    onMessage: handleMessage,
  });

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const removeNotification = useCallback((id: number) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  return {
    ...ws,
    notifications,
    clearNotifications,
    removeNotification,
  };
}