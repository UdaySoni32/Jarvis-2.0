/**
 * API Client for JARVIS 2.0
 * 
 * Handles all HTTP requests to the JARVIS API server.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  ChatRequest,
  ChatResponse,
  Conversation,
  SystemStatus,
  ModelInfo,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type RetriableRequestConfig = {
  _retry?: boolean;
  url?: string;
};

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = this.getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle 401 errors (token expired)
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const config = (error.config || {}) as RetriableRequestConfig;
        const url = config.url || '';
        const isAuthEndpoint =
          url.includes('/api/v1/auth/login') ||
          url.includes('/api/v1/auth/register') ||
          url.includes('/api/v1/auth/refresh');

        if (error.response?.status === 401 && !config._retry && !isAuthEndpoint) {
          config._retry = true;
          // Try to refresh token
          try {
            await this.refreshToken();
            // Retry original request
            return this.client.request(config);
          } catch {
            // Refresh failed, logout
            this.logout();
            if (typeof window !== 'undefined') {
              window.location.href = '/auth/login';
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // ========== Storage Methods ==========

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  }

  private setTokens(accessToken: string, refreshToken: string) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  private clearTokens() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // ========== Auth Methods ==========

  async register(data: RegisterRequest): Promise<User> {
    const response = await this.client.post('/api/v1/auth/register', data);
    return response.data;
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/api/v1/auth/login', data);
    const { access_token, refresh_token } = response.data;
    this.setTokens(access_token, refresh_token);
    return response.data;
  }

  async logout() {
    this.clearTokens();
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/api/v1/auth/me');
    return response.data;
  }

  async refreshToken(): Promise<void> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token');

    // Use a plain axios call to avoid interceptor recursion on /auth/refresh.
    const response = await axios.post<AuthResponse>(
      `${API_URL}/api/v1/auth/refresh`,
      {},
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken}`,
        },
      }
    );
    
    const { access_token, refresh_token: newRefreshToken } = response.data;
    this.setTokens(access_token, newRefreshToken);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // ========== Chat Methods ==========

  async sendMessage(data: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>('/api/v1/chat/completions', data);
    return response.data;
  }

  async* streamMessage(data: ChatRequest): AsyncGenerator<string, void, unknown> {
    const token = this.getToken();
    const response = await fetch(`${API_URL}/api/v1/chat/completions/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No reader available');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          if (data.chunk) {
            yield data.chunk;
          }
          if (data.done) {
            return;
          }
        }
      }
    }
  }

  async getConversations(): Promise<{ conversations: Conversation[]; total: number }> {
    const response = await this.client.get('/api/v1/chat/conversations');
    return response.data;
  }

  async getConversation(id: string): Promise<{ conversation_id: string; messages: any[]; total: number }> {
    const response = await this.client.get(`/api/v1/chat/conversations/${id}`);
    return response.data;
  }

  // ========== System Methods ==========

  async getSystemStatus(): Promise<SystemStatus> {
    const response = await this.client.get<SystemStatus>('/api/v1/system/status');
    return response.data;
  }

  async getModels(): Promise<ModelInfo> {
    const response = await this.client.get<ModelInfo>('/api/v1/system/models');
    return response.data;
  }

  async switchModel(modelName: string): Promise<{ success: boolean; model: string; message: string }> {
    const response = await this.client.post(`/api/v1/system/models/${modelName}`);
    return response.data;
  }

  async getPlugins(): Promise<{ plugins: any[]; total: number }> {
    const response = await this.client.get('/api/v1/system/plugins');
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;
