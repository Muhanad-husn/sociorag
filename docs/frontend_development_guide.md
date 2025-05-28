# Frontend Development Guide

## Getting Started

### Prerequisites
- **Node.js**: Version 18 or higher
- **Package Manager**: npm or pnpm
- **TypeScript**: Basic knowledge required
- **React/Preact**: Component-based development experience

### Quick Start
```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Start development server
npm run dev

# Open browser to http://localhost:5173/
```

## Development Environment

### Available Scripts
```bash
# Development
npm run dev          # Start dev server with hot reload
npm run build        # Create production build
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # TypeScript validation
```

### Project Structure
```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Base components (Card, Tabs, etc.)
│   ├── Navigation.tsx  # Main navigation
│   ├── SearchBar.tsx   # Search interface
│   ├── StreamAnswer.tsx # Real-time answer display
│   ├── FileUploader.tsx # File upload component
│   └── ProgressBar.tsx # Progress tracking
├── pages/              # Page components
│   ├── Home.tsx        # Main search page
│   ├── History.tsx     # Query history
│   ├── Saved.tsx       # Saved documents
│   └── Settings.tsx    # Application settings
├── hooks/              # Custom React hooks
│   ├── useLocalState.ts # Global state management
│   └── useSSE.ts       # Server-Sent Events
├── lib/                # Utility functions
│   ├── api.ts          # API integration
│   └── i18n.ts         # Internationalization
├── app.tsx             # Root application component
├── main.tsx            # Application entry point
└── index.css           # Global styles
```

## Component Development

### Creating New Components
```typescript
// components/ExampleComponent.tsx
import { useState } from 'preact/hooks';
import { useAppStore } from '../hooks/useLocalState';
import { t } from '../lib/i18n';

interface ExampleComponentProps {
  title: string;
  onAction?: () => void;
}

export function ExampleComponent({ title, onAction }: ExampleComponentProps) {
  const { language } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-2">
        {t('component.title', language)}
      </h3>
      <p className="text-gray-600 dark:text-gray-300">
        {title}
      </p>
      {onAction && (
        <button 
          onClick={onAction}
          disabled={isLoading}
          className="btn-primary mt-3"
        >
          {isLoading ? t('common.loading', language) : t('common.action', language)}
        </button>
      )}
    </div>
  );
}
```

### Component Best Practices
1. **Props Interface**: Always define TypeScript interfaces for props
2. **State Management**: Use local state for component-specific data, global store for shared state
3. **Styling**: Use Tailwind classes with dark mode variants
4. **Accessibility**: Include ARIA labels and keyboard navigation
5. **Internationalization**: Use translation functions for all text

### Base UI Components
Located in `src/components/ui/`, these provide consistent styling:

```typescript
// Card Component
<Card className="p-6">
  <Card.Header>
    <Card.Title>Title</Card.Title>
  </Card.Header>
  <Card.Content>
    Content goes here
  </Card.Content>
</Card>

// Tabs Component
<Tabs defaultValue="search">
  <Tabs.List>
    <Tabs.Trigger value="search">Search</Tabs.Trigger>
    <Tabs.Trigger value="upload">Upload</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Content value="search">
    Search content
  </Tabs.Content>
  <Tabs.Content value="upload">
    Upload content
  </Tabs.Content>
</Tabs>
```

## State Management

### Zustand Store
The application uses Zustand for global state management:

```typescript
// hooks/useLocalState.ts
interface AppState {
  // Theme management
  isDark: boolean;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  
  // Language management
  language: 'en' | 'ar';
  setLanguage: (lang: 'en' | 'ar') => void;
  
  // Settings
  settings: Settings;
  updateSettings: (settings: Partial<Settings>) => void;
  
  // UI state
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  
  // Current query
  currentQuery: string;
  setCurrentQuery: (query: string) => void;
  
  // Processing state
  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;
}
```

### Using the Store
```typescript
import { useAppStore } from '../hooks/useLocalState';

function MyComponent() {
  const { 
    theme, 
    language, 
    toggleTheme, 
    setLanguage,
    settings,
    updateSettings 
  } = useAppStore();

  const handleSettingsChange = (newSettings: Partial<Settings>) => {
    updateSettings(newSettings);
  };

  return (
    <div>
      <button onClick={toggleTheme}>
        Current theme: {theme}
      </button>
      <button onClick={() => setLanguage(language === 'en' ? 'ar' : 'en')}>
        Switch to {language === 'en' ? 'Arabic' : 'English'}
      </button>
    </div>
  );
}
```

### Local Component State
For component-specific state, use Preact's useState:

```typescript
import { useState, useEffect } from 'preact/hooks';

function DataComponent() {
  const [data, setData] = useState<DataType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData()
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {data.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
}
```

## API Integration

### API Client
The `src/lib/api.ts` file provides functions for all backend communication:

```typescript
import { uploadFile, createSearchStream, getHistory } from '../lib/api';

// File upload with progress
async function handleFileUpload(file: File) {
  try {
    const result = await uploadFile(file, (progress) => {
      console.log(`Upload progress: ${progress}%`);
    });
    console.log('Upload successful:', result);
  } catch (error) {
    console.error('Upload failed:', error);
  }
}

// Real-time search
function performSearch(query: string, settings: Settings) {
  const source = createSearchStream(query, settings);
  
  source.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle streaming data
  };
  
  source.onerror = (error) => {
    console.error('Search error:', error);
    source.close();
  };
  
  return source;
}

// Fetch history
async function loadHistory() {
  try {
    const response = await getHistory(1, 20); // page 1, 20 items
    return response.items;
  } catch (error) {
    console.error('Failed to load history:', error);
    return [];
  }
}
```

### Server-Sent Events (SSE)
For real-time streaming, use the custom SSE hook:

```typescript
import { useSSE } from '../hooks/useSSE';
import { createSearchStream } from '../lib/api';

function SearchComponent() {
  const [searchSource, setSearchSource] = useState<EventSource | null>(null);
  const { text, progress, isComplete, error } = useSSE(searchSource);

  const startSearch = (query: string) => {
    // Close existing search
    if (searchSource) {
      searchSource.close();
    }
    
    const source = createSearchStream(query, settings);
    setSearchSource(source);
  };

  return (
    <div>
      <button onClick={() => startSearch('test query')}>
        Start Search
      </button>
      
      {searchSource && (
        <div>
          <div>Progress: {progress}%</div>
          <div>Response: {text}</div>
          {error && <div>Error: {error}</div>}
          {isComplete && <div>Search complete!</div>}
        </div>
      )}
    </div>
  );
}
```

## Styling and Theming

### Tailwind CSS Classes
The project uses a custom Tailwind configuration with design tokens:

```typescript
// Common button styles
'btn-primary': 'px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50'
'btn-secondary': 'px-4 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100'
'btn-destructive': 'px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700'

// Card styles
'card': 'bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700'

// Input styles
'input': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800'
```

### Dark Mode Support
All components should support dark mode using Tailwind's dark: prefix:

```typescript
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
  <h1 className="text-gray-900 dark:text-white">Title</h1>
  <p className="text-gray-600 dark:text-gray-300">Description</p>
  <button className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600">
    Action
  </button>
</div>
```

### CSS Variables
The theme system uses CSS variables for consistent theming:

```css
:root {
  --color-primary: 59 130 246;
  --color-background: 255 255 255;
  --color-foreground: 15 23 42;
  --color-muted: 100 116 139;
  --color-border: 229 231 235;
}

.dark {
  --color-background: 15 23 42;
  --color-foreground: 248 250 252;
  --color-muted: 148 163 184;
  --color-border: 55 65 81;
}
```

## Internationalization

### Adding Translations
Translations are defined in `src/lib/i18n.ts`:

```typescript
export const translations = {
  // Navigation
  navigation: {
    home: { en: 'Home', ar: 'الرئيسية' },
    history: { en: 'History', ar: 'التاريخ' },
    // ... more translations
  },
  
  // Add new sections
  newFeature: {
    title: { en: 'New Feature', ar: 'ميزة جديدة' },
    description: { en: 'Feature description', ar: 'وصف الميزة' }
  }
};
```

### Using Translations
```typescript
import { t } from '../lib/i18n';
import { useAppStore } from '../hooks/useLocalState';

function MyComponent() {
  const { language } = useAppStore();

  return (
    <div>
      <h1>{t('newFeature.title', language)}</h1>
      <p>{t('newFeature.description', language)}</p>
    </div>
  );
}
```

### RTL Support
For Arabic text, the layout automatically adjusts:

```typescript
import { getDirection, isRTL } from '../lib/i18n';

function RTLAwareComponent() {
  const { language } = useAppStore();
  const direction = getDirection(language);
  const isArabic = isRTL(language);

  return (
    <div 
      dir={direction}
      className={`${isArabic ? 'text-right' : 'text-left'}`}
    >
      <div className="flex space-x-4 rtl:space-x-reverse">
        <span>Item 1</span>
        <span>Item 2</span>
      </div>
    </div>
  );
}
```

## Testing

### Component Testing
```typescript
// Example test structure (testing framework not included)
import { render } from '@testing-library/preact';
import { SearchBar } from '../SearchBar';

describe('SearchBar', () => {
  it('should render search input', () => {
    const { getByPlaceholderText } = render(<SearchBar />);
    expect(getByPlaceholderText('Ask a question...')).toBeInTheDocument();
  });

  it('should handle search submission', async () => {
    const onSearch = jest.fn();
    const { getByRole } = render(<SearchBar onSearch={onSearch} />);
    
    // Test search functionality
    fireEvent.click(getByRole('button', { name: 'Ask' }));
    expect(onSearch).toHaveBeenCalled();
  });
});
```

### Manual Testing Checklist
- [ ] All pages load correctly
- [ ] Navigation works on all screen sizes
- [ ] Theme switching functions properly
- [ ] Language switching works
- [ ] Search streaming operates correctly
- [ ] File upload shows progress
- [ ] History displays and reruns work
- [ ] Settings save and apply
- [ ] Dark mode renders properly
- [ ] Arabic RTL layout works
- [ ] Mobile navigation functions
- [ ] All buttons and inputs respond

## Performance Optimization

### Bundle Analysis
```bash
# Analyze bundle size
npm run build
npx vite-bundle-analyzer dist
```

### Code Splitting
```typescript
// Lazy load pages for better performance
import { lazy, Suspense } from 'preact/compat';

const Home = lazy(() => import('./pages/Home'));
const History = lazy(() => import('./pages/History'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Router>
        <Route path="/" component={Home} />
        <Route path="/history" component={History} />
      </Router>
    </Suspense>
  );
}
```

### Image Optimization
```typescript
// Use WebP format with fallbacks
<picture>
  <source srcSet="image.webp" type="image/webp" />
  <img src="image.jpg" alt="Description" />
</picture>
```

## Deployment

### Production Build
```bash
# Create optimized build
npm run build

# Preview production build locally
npm run preview
```

### Environment Configuration
```typescript
// lib/config.ts
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
};
```

### Environment Variables
Create `.env` files for different environments:

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000

# .env.production
VITE_API_BASE_URL=https://api.sociorag.com
```

## Troubleshooting

### Common Issues

1. **Build Errors**
   ```bash
   # Clear node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **TypeScript Errors**
   ```bash
   # Check types without building
   npx tsc --noEmit
   ```

3. **Styling Issues**
   ```bash
   # Rebuild Tailwind
   npx tailwindcss -i ./src/index.css -o ./dist/output.css --watch
   ```

4. **Hot Reload Not Working**
   - Check if files are saved properly
   - Restart development server
   - Clear browser cache

### Debug Mode
Enable debug logging:

```typescript
// Add to development environment
if (import.meta.env.DEV) {
  window.debugApp = {
    store: useAppStore.getState(),
    api: window.fetch,
    // Add debugging utilities
  };
}
```

## Contributing

### Code Style
- Use TypeScript for all files
- Follow Prettier formatting
- Use meaningful component and variable names
- Add JSDoc comments for complex functions
- Maintain consistent file structure

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-component

# Make changes and commit
git add .
git commit -m "feat: add new search component"

# Push and create pull request
git push origin feature/new-component
```

### Pull Request Checklist
- [ ] Code follows TypeScript conventions
- [ ] Components are properly typed
- [ ] Internationalization added for new text
- [ ] Dark mode support included
- [ ] Mobile responsiveness tested
- [ ] Performance impact considered
- [ ] Documentation updated

---

This guide provides the foundation for developing and maintaining the SocioRAG frontend. For specific implementation details, refer to the existing code examples in the project.
