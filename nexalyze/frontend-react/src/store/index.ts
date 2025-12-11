import { create } from 'zustand';
import type { Company, ChatMessage, SystemStats } from '../types';

interface AppState {
    // Search state
    searchQuery: string;
    searchResults: Company[];
    isSearching: boolean;
    setSearchQuery: (query: string) => void;
    setSearchResults: (results: Company[]) => void;
    setIsSearching: (loading: boolean) => void;

    // Chat state
    chatMessages: ChatMessage[];
    chatSessionId: string | null;
    isChatLoading: boolean;
    addChatMessage: (message: ChatMessage) => void;
    setChatSessionId: (id: string) => void;
    setIsChatLoading: (loading: boolean) => void;
    clearChatHistory: () => void;

    // Stats state
    stats: SystemStats | null;
    setStats: (stats: SystemStats) => void;

    // Selected company
    selectedCompany: Company | null;
    setSelectedCompany: (company: Company | null) => void;

    // UI state
    isSidebarOpen: boolean;
    toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
    // Search state
    searchQuery: '',
    searchResults: [],
    isSearching: false,
    setSearchQuery: (query) => set({ searchQuery: query }),
    setSearchResults: (results) => set({ searchResults: results }),
    setIsSearching: (loading) => set({ isSearching: loading }),

    // Chat state
    chatMessages: [],
    chatSessionId: null,
    isChatLoading: false,
    addChatMessage: (message) =>
        set((state) => ({ chatMessages: [...state.chatMessages, message] })),
    setChatSessionId: (id) => set({ chatSessionId: id }),
    setIsChatLoading: (loading) => set({ isChatLoading: loading }),
    clearChatHistory: () => set({ chatMessages: [], chatSessionId: null }),

    // Stats state
    stats: null,
    setStats: (stats) => set({ stats }),

    // Selected company
    selectedCompany: null,
    setSelectedCompany: (company) => set({ selectedCompany: company }),

    // UI state
    isSidebarOpen: false,
    toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
}));
