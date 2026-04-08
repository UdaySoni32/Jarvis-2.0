#!/bin/bash
# Complete Web Interface Setup Script

cd web || exit 1

echo "🌐 Setting up JARVIS 2.0 Web Interface"
echo "======================================"
echo

# Create register page
cat > app/auth/register/page.tsx << 'EOF'
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store/auth';

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error, clearError } = useAuthStore();
  const [formData, setFormData] = useState({ username: '', email: '', password: '', confirmPassword: '', fullName: '' });
  const [validationError, setValidationError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setValidationError('');
    if (formData.password !== formData.confirmPassword) {
      setValidationError('Passwords do not match');
      return;
    }
    if (formData.password.length < 6) {
      setValidationError('Password must be at least 6 characters');
      return;
    }
    try {
      await register(formData.username, formData.email, formData.password, formData.fullName || undefined);
      router.push('/chat');
    } catch (error) {}
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4">
      <div className="w-full max-w-md p-8 space-y-6 bg-white dark:bg-gray-800 rounded-2xl shadow-2xl">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">JARVIS 2.0</h1>
          <p className="mt-2 text-sm text-muted-foreground">Create your account</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {(error || validationError) && <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 rounded-lg">{error || validationError}</div>}
          <div><label className="block text-sm font-medium mb-2">Username *</label>
          <input type="text" required value={formData.username} onChange={(e) => setFormData({ ...formData, username: e.target.value })} className="w-full px-4 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-background" placeholder="Choose a username" /></div>
          <div><label className="block text-sm font-medium mb-2">Email *</label>
          <input type="email" required value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className="w-full px-4 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-background" placeholder="your@email.com" /></div>
          <div><label className="block text-sm font-medium mb-2">Full Name</label>
          <input type="text" value={formData.fullName} onChange={(e) => setFormData({ ...formData, fullName: e.target.value })} className="w-full px-4 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-background" placeholder="John Doe (optional)" /></div>
          <div><label className="block text-sm font-medium mb-2">Password *</label>
          <input type="password" required value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} className="w-full px-4 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-background" placeholder="At least 6 characters" /></div>
          <div><label className="block text-sm font-medium mb-2">Confirm Password *</label>
          <input type="password" required value={formData.confirmPassword} onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })} className="w-full px-4 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-background" placeholder="Confirm your password" /></div>
          <button type="submit" disabled={isLoading} className="w-full px-4 py-2 text-white bg-primary hover:bg-primary/90 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed">{isLoading ? 'Creating account...' : 'Sign Up'}</button>
        </form>
        <p className="text-center text-sm text-muted-foreground">Already have an account? <Link href="/auth/login" className="text-primary hover:underline font-medium">Sign in</Link></p>
      </div>
    </div>
  );
}
EOF

# Create chat page
cat > app/chat/page.tsx << 'EOF'
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
EOF

echo "✅ Web interface files created!"
echo
echo "📦 Now run: npm install"
echo "🚀 Then run: npm run dev"
echo
