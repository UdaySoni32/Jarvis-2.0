import { create } from "zustand";
import type { Message, Conversation } from "@/types";
import { apiClient } from "@/lib/api/client";

interface ChatState {
  messages: Message[];
  conversations: Conversation[];
  currentConversationId: string | null;
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  sendMessage: (message: string, model?: string) => Promise<void>;
  streamMessage: (message: string, model?: string) => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
  loadConversations: () => Promise<void>;
  clearMessages: () => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  conversations: [],
  currentConversationId: null,
  isLoading: false,
  isStreaming: false,
  error: null,
  sendMessage: async (message, model) => {
    set({ isLoading: true, error: null });
    const userMessage: Message = { role: "user", content: message };
    set((state) => ({ messages: [...state.messages, userMessage] }));
    try {
      const response = await apiClient.sendMessage({
        message,
        conversation_id: get().currentConversationId || undefined,
        model,
      });
      const assistantMessage: Message = {
        role: "assistant",
        content: response.message,
        created_at: response.created_at,
      };
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        currentConversationId: response.conversation_id,
        isLoading: false,
      }));
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || "Failed to send message",
        isLoading: false,
      });
      throw error;
    }
  },
  streamMessage: async (message, model) => {
    set({ isStreaming: true, error: null });
    const userMessage: Message = { role: "user", content: message };
    set((state) => ({ messages: [...state.messages, userMessage] }));
    const assistantMessage: Message = { role: "assistant", content: "" };
    set((state) => ({ messages: [...state.messages, assistantMessage] }));
    try {
      const stream = apiClient.streamMessage({
        message,
        conversation_id: get().currentConversationId || undefined,
        model,
      });
      for await (const chunk of stream) {
        set((state) => {
          const newMessages = [...state.messages];
          const lastMessage = newMessages[newMessages.length - 1];
          if (lastMessage.role === "assistant") {
            lastMessage.content += chunk;
          }
          return { messages: newMessages };
        });
      }
      set({ isStreaming: false });
    } catch (error: any) {
      set({
        error: error.message || "Failed to stream message",
        isStreaming: false,
      });
      throw error;
    }
  },
  loadConversation: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiClient.getConversation(id);
      const messages: Message[] = data.messages.map((msg: any) => ({
        role: msg.role,
        content: msg.content,
        created_at: msg.created_at,
      }));
      set({
        messages,
        currentConversationId: id,
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || "Failed to load conversation",
        isLoading: false,
      });
    }
  },
  loadConversations: async () => {
    try {
      const data = await apiClient.getConversations();
      set({ conversations: data.conversations });
    } catch (error) {}
  },
  clearMessages: () => set({ messages: [], currentConversationId: null }),
  clearError: () => set({ error: null }),
}));
