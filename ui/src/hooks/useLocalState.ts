import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Settings {
  topK: number;
  topKR: number;
  temperature: number;
  translateToArabic: boolean;
}

export interface AppState {
  // Theme
  isDark: boolean;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  
  // Language
  language: 'en' | 'ar';
  setLanguage: (lang: 'en' | 'ar') => void;
  
  // Settings
  settings: Settings;
  updateSettings: (settings: Partial<Settings>) => void;
  
  // UI State
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  
  // Current query and results
  currentQuery: string;
  setCurrentQuery: (query: string) => void;
  
  // Processing state
  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;
}

const defaultSettings: Settings = {
  topK: 5,
  topKR: 3,
  temperature: 0.7,
  translateToArabic: false,
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({      // Theme
      isDark: false,
      theme: 'light' as 'light' | 'dark',
      toggleTheme: () => {
        const newIsDark = !get().isDark;
        const newTheme = newIsDark ? 'dark' : 'light';
        set({ isDark: newIsDark, theme: newTheme });
        // Update document class
        if (newIsDark) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      },
      
      // Language
      language: 'en' as 'en' | 'ar',
      setLanguage: (lang) => set({ language: lang }),
      
      // Settings
      settings: defaultSettings,
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),
      
      // UI State
      sidebarOpen: false,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      
      // Current query and results
      currentQuery: '',
      setCurrentQuery: (query) => set({ currentQuery: query }),
      
      // Processing state
      isProcessing: false,
      setIsProcessing: (processing) => set({ isProcessing: processing }),
    }),
    {
      name: 'sociograph-storage',
      partialize: (state) => ({
        isDark: state.isDark,
        settings: state.settings,
      }),
    }
  )
);

// Initialize theme on load
const initializeTheme = () => {
  const stored = useAppStore.getState();
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const shouldBeDark = stored.isDark ?? prefersDark;
  
  if (shouldBeDark) {
    document.documentElement.classList.add('dark');
    useAppStore.setState({ isDark: true });
  } else {
    document.documentElement.classList.remove('dark');
    useAppStore.setState({ isDark: false });
  }
};

// Call on module load
if (typeof window !== 'undefined') {
  initializeTheme();
}
