// User types
export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  created_at: string;
}

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Chat types
export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  model?: string;
  context?: Message[];
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  model_used: string;
  created_at: string;
}

export interface Conversation {
  conversation_id: string;
  last_message: string;
  message_count: number;
}

// System types
export interface SystemStatus {
  system: {
    platform: string;
    platform_version: string;
    python_version: string;
    processor: string;
  };
  resources: {
    cpu_percent: number;
    cpu_count: number;
    memory_total_gb: number;
    memory_used_gb: number;
    memory_percent: number;
    disk_total_gb: number;
    disk_used_gb: number;
    disk_percent: number;
  };
  config: {
    llm_provider: string;
    llm_model: string;
    enable_memory: boolean;
    enable_plugins: boolean;
    debug: boolean;
  };
}

export interface ModelInfo {
  current_model: string;
  available_models: string[];
  providers: Record<string, {
    name: string;
    available: boolean;
    models: string[];
  }>;
}
