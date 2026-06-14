import { create } from 'zustand';

interface Message {
  id: string;
  role: 'user' | 'agent';
  text: string;
  audioUrl?: string;
}

interface ChatState {
  messages: Message[];
  isRecording: boolean;
  isProcessing: boolean;
  addMessage: (msg: Message) => void;
  clearMessages: () => void;
  setRecording: (val: boolean) => void;
  setProcessing: (val: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isRecording: false,
  isProcessing: false,
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  clearMessages: () => set({ messages: [] }),
  setRecording: (val) => set({ isRecording: val }),
  setProcessing: (val) => set({ isProcessing: val })
}));
