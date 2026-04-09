'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { useChatWebSocket, usePresence, useNotifications } from '@/lib/websocket/hooks';
import { Send, Loader2, Settings, LogOut, Users, Wifi, WifiOff, RotateCcw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: number;
  content: string;
  user_type: 'user' | 'assistant';
  timestamp: number;
}

export default function ChatPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout, fetchUser } = useAuthStore();
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showWebSocket, setShowWebSocket] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout>();
  
  // WebSocket hooks (conditionally used)
  const chat = useChatWebSocket('default');
  const presence = usePresence();
  const notifications = useNotifications();

  // Fallback to HTTP API if WebSocket fails
  const [httpMessages, setHttpMessages] = useState<Message[]>([]);
  const [httpLoading, setHttpLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }
    if (!user) fetchUser();
  }, [isAuthenticated, user, router, fetchUser]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [showWebSocket ? chat.messages : httpMessages, chat.streamingMessage]);

  // Handle typing indicator for WebSocket
  useEffect(() => {
    if (!showWebSocket) return;
    
    if (isTyping) {
      chat.sendTyping(true);
      
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      
      typingTimeoutRef.current = setTimeout(() => {
        chat.sendTyping(false);
        setIsTyping(false);
      }, 2000);
    } else {
      chat.sendTyping(false);
    }
    
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [isTyping, chat.sendTyping, showWebSocket]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const message = input.trim();
    setInput('');
    setIsTyping(false);

    if (showWebSocket && chat.connected) {
      // Use WebSocket
      chat.sendMessage(message, true);
    } else {
      // Fallback to HTTP API
      await sendHttpMessage(message);
    }
  };

  const sendHttpMessage = async (content: string) => {
    setHttpLoading(true);
    const userMessage: Message = {
      id: Date.now(),
      content,
      user_type: 'user',
      timestamp: Date.now() / 1000,
    };
    setHttpMessages(prev => [...prev, userMessage]);

    try {
      const { apiClient } = await import('@/lib/api/client');
      const response = await apiClient.sendMessage({
        message: content,
      });

      const assistantMessage: Message = {
        id: Date.now() + 1,
        content: response.message,
        user_type: 'assistant',
        timestamp: Date.now() / 1000,
      };
      setHttpMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('HTTP message error:', error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        content: 'Sorry, I encountered an error. Please try again.',
        user_type: 'assistant', 
        timestamp: Date.now() / 1000,
      };
      setHttpMessages(prev => [...prev, errorMessage]);
    } finally {
      setHttpLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
    if (!isTyping && e.target.value.length > 0) {
      setIsTyping(true);
    }
  };

  const handleLogout = () => {
    if (showWebSocket) {
      chat.disconnect();
      presence.disconnect();  
      notifications.disconnect();
    }
    logout();
    router.push('/auth/login');
  };

  const toggleMode = () => {
    setShowWebSocket(!showWebSocket);
    // Clear messages when switching modes
    if (showWebSocket) {
      chat.clearMessages();
    } else {
      setHttpMessages([]);
    }
  };

  const formatMessage = (message: Message) => {
    return (
      <div
        key={message.id}
        className={`flex ${
          message.user_type === 'user' ? 'justify-end' : 'justify-start'
        } mb-4`}
      >
        <div
          className={`max-w-[70%] rounded-lg px-4 py-2 ${
            message.user_type === 'user'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
          }`}
        >
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
          <div className="text-xs mt-1 opacity-70">
            {new Date(message.timestamp * 1000).toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const currentMessages = showWebSocket ? chat.messages : httpMessages;
  const isCurrentlyLoading = showWebSocket ? chat.isStreaming : httpLoading;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="flex justify-between items-center max-w-4xl mx-auto">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              JARVIS 2.0 Chat
            </h1>
            <div className="flex items-center gap-2">
              {showWebSocket ? (
                chat.connected ? (
                  <div className="flex items-center gap-1 text-green-600 text-sm">
                    <Wifi className="h-4 w-4" />
                    <span>WebSocket</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-red-600 text-sm">
                    <WifiOff className="h-4 w-4" />
                    <span>Disconnected</span>
                  </div>
                )
              ) : (
                <div className="flex items-center gap-1 text-blue-600 text-sm">
                  <RotateCcw className="h-4 w-4" />
                  <span>HTTP API</span>
                </div>
              )}
              
              {showWebSocket && chat.reconnectAttempts > 0 && (
                <div className="text-yellow-600 text-sm">
                  Reconnecting... ({chat.reconnectAttempts})
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Mode toggle */}
            <button
              onClick={toggleMode}
              className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              title={showWebSocket ? "Switch to HTTP API" : "Switch to WebSocket"}
            >
              {showWebSocket ? "WebSocket" : "HTTP"}
            </button>
            
            {/* Online users (WebSocket only) */}
            {showWebSocket && (
              <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                <Users className="h-4 w-4" />
                <span>{presence.onlineUsers.length}</span>
              </div>
            )}
            
            <button
              onClick={() => router.push('/settings')}
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            </button>
            
            <button
              onClick={handleLogout}
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <LogOut className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        </div>
      </header>

      {/* Notifications (WebSocket only) */}
      {showWebSocket && notifications.notifications.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800">
          <div className="max-w-4xl mx-auto px-4 py-2">
            {notifications.notifications.slice(-1).map((notification) => (
              <div key={notification.id} className="flex items-center justify-between">
                <span className="text-blue-800 dark:text-blue-200 text-sm">
                  {notification.message || JSON.stringify(notification)}
                </span>
                <button
                  onClick={() => notifications.removeNotification(notification.id)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat Container */}
      <div className="max-w-4xl mx-auto h-[calc(100vh-120px)] flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {currentMessages.length === 0 && (
            <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
              <h2 className="text-lg font-medium mb-2">Welcome to JARVIS 2.0!</h2>
              <p>Start a conversation with your AI assistant.</p>
              <div className="mt-4 text-sm">
                <p>Mode: {showWebSocket ? 'WebSocket (Real-time)' : 'HTTP API (Standard)'}</p>
                {showWebSocket && (
                  <p>Status: {chat.connected ? '✅ Connected' : '❌ Disconnected'}</p>
                )}
                {showWebSocket && chat.error && (
                  <p className="text-red-500">Error: {chat.error.message}</p>
                )}
              </div>
            </div>
          )}
          
          {currentMessages.map((message) => formatMessage(message))}
          
          {/* Streaming message (WebSocket only) */}
          {showWebSocket && chat.isStreaming && chat.streamingMessage && (
            <div className="flex justify-start mb-4">
              <div className="max-w-[70%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown>{chat.streamingMessage}</ReactMarkdown>
                </div>
                <div className="flex items-center gap-2 text-xs mt-1 opacity-70">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>Streaming...</span>
                </div>
              </div>
            </div>
          )}

          {/* HTTP Loading indicator */}
          {!showWebSocket && httpLoading && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          {/* Typing indicators (WebSocket only) */}
          {showWebSocket && chat.typingUsers.length > 0 && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                  <span>Someone is typing...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={handleInputChange}
              placeholder={
                showWebSocket 
                  ? (chat.connected ? "Type your message..." : "Connecting...")
                  : "Type your message..."
              }
              disabled={showWebSocket ? !chat.connected : httpLoading}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       placeholder-gray-500 dark:placeholder-gray-400
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={
                !input.trim() || 
                (showWebSocket ? !chat.connected : httpLoading)
              }
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isCurrentlyLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </form>
          
          <div className="flex justify-between items-center mt-2 text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center gap-4">
              <span>
                Mode: {showWebSocket ? 'WebSocket' : 'HTTP'} 
                {showWebSocket && ` (${chat.connected ? 'Connected' : 'Disconnected'})`}
              </span>
              {showWebSocket && presence.onlineUsers.length > 0 && (
                <span>{presence.onlineUsers.length} users online</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={showWebSocket ? chat.clearMessages : () => setHttpMessages([])}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                Clear chat
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
