# Frontend Testing Guide

## Overview
Comprehensive testing strategy for the SocioGraph frontend application, covering unit tests, integration tests, and end-to-end testing approaches.

## 🧪 Testing Strategy

### Testing Pyramid
1. **Unit Tests** (70%) - Component logic and utilities
2. **Integration Tests** (20%) - Component interactions and API integration
3. **E2E Tests** (10%) - Complete user workflows

### Testing Stack
- **Test Runner**: Vitest (Vite-native)
- **Testing Library**: @testing-library/preact
- **Mocking**: MSW (Mock Service Worker)
- **E2E**: Playwright (recommended) or Cypress

## 🛠️ Setup Testing Environment

### Install Dependencies
```bash
cd ui

# Core testing dependencies
npm install -D vitest @testing-library/preact @testing-library/jest-dom

# Additional testing utilities
npm install -D @testing-library/user-event msw jsdom

# E2E testing (optional)
npm install -D @playwright/test
```

### Vitest Configuration
**`vitest.config.ts`:**
```typescript
import { defineConfig } from 'vitest/config';
import preact from '@preact/preset-vite';

export default defineConfig({
  plugins: [preact()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*'
      ]
    }
  }
});
```

### Test Setup
**`src/test/setup.ts`:**
```typescript
import '@testing-library/jest-dom';
import { beforeAll, afterAll, afterEach } from 'vitest';
import { cleanup } from '@testing-library/preact';
import { server } from './mocks/server';

// MSW server setup
beforeAll(() => server.listen());
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));
```

### Package.json Scripts
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test"
  }
}
```

## 🧪 Unit Testing

### Component Testing
**`src/components/__tests__/SearchBar.test.tsx`:**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/preact';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { SearchBar } from '../SearchBar';

describe('SearchBar', () => {
  const mockOnSearch = vi.fn();
  const mockOnUpload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search input and submit button', () => {
    render(
      <SearchBar 
        onSearch={mockOnSearch} 
        onUpload={mockOnUpload} 
        isLoading={false} 
      />
    );

    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
  });

  it('calls onSearch when form is submitted', async () => {
    const user = userEvent.setup();
    render(
      <SearchBar 
        onSearch={mockOnSearch} 
        onUpload={mockOnUpload} 
        isLoading={false} 
      />
    );

    const input = screen.getByPlaceholderText(/ask a question/i);
    const submitButton = screen.getByRole('button', { name: /search/i });

    await user.type(input, 'test query');
    await user.click(submitButton);

    expect(mockOnSearch).toHaveBeenCalledWith('test query');
  });

  it('disables input when loading', () => {
    render(
      <SearchBar 
        onSearch={mockOnSearch} 
        onUpload={mockOnUpload} 
        isLoading={true} 
      />
    );

    expect(screen.getByPlaceholderText(/ask a question/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /search/i })).toBeDisabled();
  });

  it('shows loading state', () => {
    render(
      <SearchBar 
        onSearch={mockOnSearch} 
        onUpload={mockOnUpload} 
        isLoading={true} 
      />
    );

    expect(screen.getByText(/searching/i)).toBeInTheDocument();
  });
});
```

### Hook Testing
**`src/hooks/__tests__/useLocalState.test.ts`:**
```typescript
import { renderHook, act } from '@testing-library/preact';
import { describe, it, expect, beforeEach } from 'vitest';
import { useLocalState } from '../useLocalState';

describe('useLocalState', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => useLocalState());

    expect(result.current.searchHistory).toEqual([]);
    expect(result.current.savedDocuments).toEqual([]);
    expect(result.current.theme).toBe('system');
    expect(result.current.language).toBe('en');
  });

  it('adds search to history', () => {
    const { result } = renderHook(() => useLocalState());

    act(() => {
      result.current.addSearchToHistory({
        id: '1',
        query: 'test query',
        timestamp: new Date().toISOString(),
        answer: 'test answer'
      });
    });

    expect(result.current.searchHistory).toHaveLength(1);
    expect(result.current.searchHistory[0].query).toBe('test query');
  });

  it('persists state to localStorage', () => {
    const { result } = renderHook(() => useLocalState());

    act(() => {
      result.current.setTheme('dark');
    });

    const stored = JSON.parse(localStorage.getItem('sociograph-state') || '{}');
    expect(stored.state.theme).toBe('dark');
  });
});
```

### Utility Testing
**`src/lib/__tests__/i18n.test.ts`:**
```typescript
import { describe, it, expect } from 'vitest';
import { t, setLanguage, getLanguage } from '../i18n';

describe('i18n', () => {
  it('returns English text by default', () => {
    expect(t('search.placeholder')).toBe('Ask a question about your documents...');
  });

  it('switches to Arabic when language is set', () => {
    setLanguage('ar');
    expect(t('search.placeholder')).toBe('اطرح سؤالاً حول مستنداتك...');
    expect(getLanguage()).toBe('ar');
  });

  it('falls back to English for missing translations', () => {
    setLanguage('ar');
    expect(t('nonexistent.key')).toBe('nonexistent.key');
  });
});
```

## 🔗 Integration Testing

### API Integration
**`src/test/mocks/handlers.ts`:**
```typescript
import { rest } from 'msw';

export const handlers = [
  // Search endpoint
  rest.post('/api/v1/search', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 'search-123',
        query: 'test query',
        answer: 'Test answer',
        sources: []
      })
    );
  }),

  // Upload endpoint
  rest.post('/api/v1/upload', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 'doc-123',
        filename: 'test.pdf',
        status: 'uploaded'
      })
    );
  }),

  // SSE endpoint
  rest.get('/api/v1/search/:id/stream', (req, res, ctx) => {
    return res(
      ctx.text('data: {"type": "progress", "value": 50}\n\n')
    );
  })
];
```

**`src/test/mocks/server.ts`:**
```typescript
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

### Component Integration
**`src/pages/__tests__/Home.test.tsx`:**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/preact';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Home } from '../Home';

describe('Home Page Integration', () => {
  it('performs complete search workflow', async () => {
    const user = userEvent.setup();
    render(<Home />);

    // Enter search query
    const searchInput = screen.getByPlaceholderText(/ask a question/i);
    await user.type(searchInput, 'What is artificial intelligence?');

    // Submit search
    const searchButton = screen.getByRole('button', { name: /search/i });
    await user.click(searchButton);

    // Verify loading state
    expect(screen.getByText(/searching/i)).toBeInTheDocument();

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText(/test answer/i)).toBeInTheDocument();
    });

    // Verify search is in history
    expect(screen.getByText(/what is artificial intelligence/i)).toBeInTheDocument();
  });

  it('handles file upload workflow', async () => {
    const user = userEvent.setup();
    render(<Home />);

    // Create mock file
    const file = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

    // Upload file
    const fileInput = screen.getByLabelText(/upload pdf/i);
    await user.upload(fileInput, file);

    // Verify upload progress
    await waitFor(() => {
      expect(screen.getByText(/uploading/i)).toBeInTheDocument();
    });

    // Verify completion
    await waitFor(() => {
      expect(screen.getByText(/upload complete/i)).toBeInTheDocument();
    });
  });
});
```

## 🌐 End-to-End Testing

### Playwright Setup
**`playwright.config.ts`:**
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

### E2E Test Examples
**`e2e/search-workflow.spec.ts`:**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Search Workflow', () => {
  test('complete search and view results', async ({ page }) => {
    await page.goto('/');

    // Verify page loaded
    await expect(page.getByText('SocioGraph')).toBeVisible();

    // Perform search
    await page.fill('[placeholder*="Ask a question"]', 'What is machine learning?');
    await page.click('button[type="submit"]');

    // Verify loading state
    await expect(page.getByText('Searching...')).toBeVisible();

    // Wait for results
    await expect(page.getByTestId('search-results')).toBeVisible({ timeout: 10000 });

    // Verify answer is displayed
    await expect(page.getByTestId('search-answer')).toContainText('machine learning');

    // Verify search is in history
    await page.click('[data-testid="history-tab"]');
    await expect(page.getByText('What is machine learning?')).toBeVisible();
  });

  test('handles search errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('/api/v1/search', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    await page.goto('/');
    await page.fill('[placeholder*="Ask a question"]', 'test query');
    await page.click('button[type="submit"]');

    // Verify error message
    await expect(page.getByText(/error occurred/i)).toBeVisible();
  });
});
```

**`e2e/file-upload.spec.ts`:**
```typescript
import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('File Upload', () => {
  test('uploads PDF file successfully', async ({ page }) => {
    await page.goto('/');

    // Navigate to upload section
    await page.click('[data-testid="upload-tab"]');

    // Select file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(__dirname, 'fixtures/sample.pdf'));

    // Verify upload progress
    await expect(page.getByText('Uploading...')).toBeVisible();

    // Verify completion
    await expect(page.getByText('Upload complete')).toBeVisible({ timeout: 30000 });

    // Verify file appears in saved documents
    await page.click('[data-testid="saved-tab"]');
    await expect(page.getByText('sample.pdf')).toBeVisible();
  });
});
```

## 🌍 Accessibility Testing

### Automated Accessibility Tests
**`src/test/accessibility.test.tsx`:**
```typescript
import { render } from '@testing-library/preact';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';
import { SearchBar } from '../components/SearchBar';

expect.extend(toHaveNoViolations);

describe('Accessibility', () => {
  it('SearchBar has no accessibility violations', async () => {
    const { container } = render(
      <SearchBar onSearch={() => {}} onUpload={() => {}} isLoading={false} />
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Navigation has proper ARIA labels', async () => {
    const { container } = render(<Navigation />);
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

### Manual Accessibility Checklist
- [ ] Keyboard navigation works for all interactive elements
- [ ] Screen reader announces content changes
- [ ] Color contrast meets WCAG AA standards
- [ ] Focus indicators are visible
- [ ] ARIA labels are descriptive
- [ ] Form validation is accessible

## 📱 Mobile Testing

### Responsive Design Tests
**`e2e/mobile.spec.ts`:**
```typescript
import { test, expect, devices } from '@playwright/test';

test.describe('Mobile Experience', () => {
  test.use({ ...devices['iPhone 12'] });

  test('navigation works on mobile', async ({ page }) => {
    await page.goto('/');

    // Mobile menu should be visible
    await expect(page.getByTestId('mobile-menu-button')).toBeVisible();

    // Click menu button
    await page.click('[data-testid="mobile-menu-button"]');

    // Menu should open
    await expect(page.getByTestId('mobile-menu')).toBeVisible();

    // Navigation items should be clickable
    await page.click('[data-testid="nav-history"]');
    await expect(page).toHaveURL(/.*history/);
  });

  test('touch interactions work correctly', async ({ page }) => {
    await page.goto('/');

    // Test swipe gestures (if implemented)
    const searchArea = page.getByTestId('search-area');
    await searchArea.hover();
    
    // Simulate touch
    await page.touchscreen.tap(100, 100);
    
    // Verify touch interaction
    await expect(page.getByPlaceholderText(/ask a question/i)).toBeFocused();
  });
});
```

## 🔄 Performance Testing

### Bundle Size Testing
**`src/test/bundle-size.test.ts`:**
```typescript
import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('Bundle Size', () => {
  it('main bundle should be under 300KB', () => {
    const distPath = path.join(__dirname, '../../dist');
    
    if (!fs.existsSync(distPath)) {
      console.warn('No build found. Run `npm run build` first.');
      return;
    }

    const files = fs.readdirSync(distPath);
    const jsFiles = files.filter(file => file.endsWith('.js'));
    
    let totalSize = 0;
    jsFiles.forEach(file => {
      const stats = fs.statSync(path.join(distPath, file));
      totalSize += stats.size;
    });

    expect(totalSize).toBeLessThan(300 * 1024); // 300KB
  });
});
```

### Loading Performance
**`e2e/performance.spec.ts`:**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Performance', () => {
  test('page loads within 3 seconds', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(3000);
  });

  test('search completes within 10 seconds', async ({ page }) => {
    await page.goto('/');
    
    const startTime = Date.now();
    
    await page.fill('[placeholder*="Ask a question"]', 'test query');
    await page.click('button[type="submit"]');
    
    await page.waitForSelector('[data-testid="search-results"]', { timeout: 10000 });
    
    const searchTime = Date.now() - startTime;
    expect(searchTime).toBeLessThan(10000);
  });
});
```

## 🔧 Test Utilities

### Custom Render Helper
**`src/test/utils.tsx`:**
```typescript
import { render, RenderOptions } from '@testing-library/preact';
import { ComponentChildren } from 'preact';

// Mock providers for testing
const AllProviders = ({ children }: { children: ComponentChildren }) => {
  return (
    <div data-theme="light" dir="ltr">
      {children}
    </div>
  );
};

const customRender = (ui: ComponentChildren, options?: RenderOptions) =>
  render(ui, { wrapper: AllProviders, ...options });

export * from '@testing-library/preact';
export { customRender as render };
```

### Mock Data Factory
**`src/test/factories.ts`:**
```typescript
export const createMockSearchResult = (overrides = {}) => ({
  id: 'search-123',
  query: 'test query',
  answer: 'Test answer',
  sources: [],
  timestamp: new Date().toISOString(),
  ...overrides
});

export const createMockDocument = (overrides = {}) => ({
  id: 'doc-123',
  filename: 'test.pdf',
  status: 'processed',
  uploadedAt: new Date().toISOString(),
  size: 1024,
  ...overrides
});
```

## 📊 Test Coverage

### Coverage Goals
- **Unit Tests**: 80%+ line coverage
- **Integration Tests**: 70%+ critical paths
- **E2E Tests**: 90%+ user workflows

### Coverage Report
```bash
# Generate coverage report
npm run test:coverage

# View coverage in browser
open coverage/index.html
```

### Coverage Configuration
```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: 'c8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        global: {
          lines: 80,
          functions: 80,
          branches: 80,
          statements: 80
        }
      }
    }
  }
});
```

## 🚀 CI/CD Integration

### GitHub Actions Testing
**`.github/workflows/test.yml`:**
```yaml
name: Test Frontend

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: ui/package-lock.json
    
    - name: Install dependencies
      run: cd ui && npm ci
    
    - name: Run unit tests
      run: cd ui && npm run test:run
    
    - name: Run E2E tests
      run: cd ui && npm run test:e2e
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./ui/coverage/coverage-final.json
```

## 🔍 Debugging Tests

### Debug Configuration
**`.vscode/launch.json`:**
```json
{
  "configurations": [
    {
      "name": "Debug Tests",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/ui/node_modules/vitest/vitest.mjs",
      "args": ["run", "--reporter=verbose"],
      "cwd": "${workspaceFolder}/ui",
      "console": "integratedTerminal"
    }
  ]
}
```

### Test Debugging Tips
```typescript
// Use debug utilities
import { screen, debug } from '@testing-library/preact';

test('debug example', () => {
  render(<Component />);
  
  // Print current DOM
  debug();
  
  // Print specific element
  debug(screen.getByRole('button'));
});
```

## 📝 Best Practices

### Test Organization
- Group related tests in `describe` blocks
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Keep tests independent and isolated

### Mock Strategy
- Mock external dependencies
- Use MSW for API mocking
- Mock only what you need
- Reset mocks between tests

### Performance
- Run tests in parallel
- Use snapshot testing sparingly
- Mock expensive operations
- Clean up after tests

## 🔗 Related Documentation
- [Frontend Development Guide](frontend_development_guide.md)
- [UI Component Documentation](ui_component_documentation.md)
- [API Documentation](api_documentation.md)
- [Frontend Deployment Guide](frontend_deployment_guide.md)
