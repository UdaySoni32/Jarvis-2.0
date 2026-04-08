'use client';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { useChatStore } from '@/lib/store/chat';
import { Send, Loader2, Settings, LogOut } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export default function ChatPage() {
  const router = useRouter();
  const { user, isAuthenticated, logout, fetchUser } = useAuthStore();
  const { messages, isLoading, isStreaming, sendMessage, streamMessage, clearMessages } = useChatStore();
  const [input, setInput] = useState('');
  const [useStreaming, setUseStreaming] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }
    if (!user) fetchUser();
  }, [isAuthenticated, user, router, fetchUser]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || isStreaming) return;

    const message = input.trim();
    setInput('');

    try {
      if (useStreaming) {
        await streamMessage(message);
      } else {
        await sendMessage(message);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/auth/login');
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-b border-border">
        <div>
          <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">JARVIS 2.0</h1>
          <p className="text-sm text-muted-foreground">Welcome, {user?.username || 'User'}!</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => router.push('/settings')} className="p-2 hover:bg-accent rounded-lg transition-colors" title="Settings"><Settings className="w-5 h-5" /></button>
          <button onClick={handleLogout} className="p-2 hover:bg-accent rounded-lg transition-colors" title="Logout"><LogOut className="w-5 h-5" /></button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-4">
              <div className="text-6xl">🤖</div>
              <h2 className="text-2xl font-semibold">How can I help you today?</h2>
              <p className="text-muted-foreground">Ask me anything - I'm powered by advanced AI</p>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}>
              <div className={`max-w-3xl px-4 py-3 rounded-2xl ${msg.role === 'user' ? 'bg-primary text-primary-foreground ml-12' : 'bg-white dark:bg-gray-800 mr-12'}`}>
                {msg.role === 'assistant' ? (
                  <ReactMarkdown className="prose dark:prose-invert max-w-none">{msg.content}</ReactMarkdown>
                ) : (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-4 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-t border-border">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex items-end gap-3">
          <div className="flex-1">
            <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }} placeholder="Type your message... (Shift+Enter for new line)" rows={1} className="w-full px-4 py-3 bg-background border border-input rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary resize-none" style={{ minHeight: '52px', maxHeight: '200px' }} />
          </div>
          <button type="submit" disabled={!input.trim() || isLoading || isStreaming} className="px-6 py-3 bg-primary text-primary-foreground rounded-2xl hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
            {isLoading || isStreaming ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </form>
        <div className="max-w-4xl mx-auto mt-2 flex items-center justify-between text-xs text-muted-foreground">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={useStreaming} onChange={(e) => setUseStreaming(e.target.checked)} className="rounded" />
            <span>Enable streaming</span>
          </label>
          <button onClick={clearMessages} className="hover:text-foreground transition-colors">Clear chat</button>
        </div>
      </div>
    </div>
  );
}
