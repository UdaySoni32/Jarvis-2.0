import { create } from "zustand";
import type { User } from "@/types";
import { apiClient } from "@/lib/api/client";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  error: null,
  isAuthenticated: apiClient.isAuthenticated(),
  login: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.login({ username, password });
      const user = await apiClient.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || "Login failed", isLoading: false });
      throw error;
    }
  },
  register: async (username, email, password, fullName) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.register({ username, email, password, full_name: fullName });
      await apiClient.login({ username, password });
      const user = await apiClient.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || "Registration failed", isLoading: false });
      throw error;
    }
  },
  logout: () => {
    apiClient.logout();
    set({ user: null, isAuthenticated: false });
  },
  fetchUser: async () => {
    if (!apiClient.isAuthenticated()) return;
    set({ isLoading: true });
    try {
      const user = await apiClient.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isAuthenticated: false, isLoading: false });
    }
  },
  clearError: () => set({ error: null }),
}));
