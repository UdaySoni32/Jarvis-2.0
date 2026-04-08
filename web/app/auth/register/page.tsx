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
