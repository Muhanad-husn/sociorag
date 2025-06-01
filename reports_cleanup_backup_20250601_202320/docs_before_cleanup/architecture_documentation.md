# SocioGraph Architecture Documentation

## System Architecture Overview

SocioGraph is designed as a modular, scalable system for analyzing social dynamics in texts. The architecture follows a layered approach with clear separation of concerns, enabling maintainability, testability, and future extensibility.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Web UI    │  │ Mobile App  │  │  External Clients   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket/SSE
┌─────────────────────┴───────────────────────────────────────┐
│                   API Gateway                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              FastAPI Application                       │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │ │
│  │  │    Q&A   │ │Document  │ │  Search  │ │    Export    │ │ │
│  │  │Endpoints │ │Management│ │Endpoints │ │  Endpoints   │ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │ Internal API Calls
┌─────────────────────┴───────────────────────────────────────┐
│                 Business Logic Layer                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │   Answer     │ │  Retriever   │ │    Ingestion         │ │
│  │ Generation   │ │   Module     │ │    Pipeline          │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │ Data Access
┌─────────────────────┴───────────────────────────────────────┐
│                   Data Layer                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │   Vector     │ │    Graph     │ │     File System      │ │
│  │   Store      │ │  Database    │ │     Storage          │ │
│  │ (SQLite-vec) │ │  (SQLite)    │ │   (Documents/PDFs)   │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Layer (`backend/app/api/`)

The API layer provides RESTful endpoints and real-time communication interfaces.

**Key Components:**
- **Q&A Router** (`qa.py`): Handles question-answering with streaming responses
- **Document Router** (future): Document upload and management
- **Search Router** (future): Entity and relationship search
- **Export Router** (future): PDF and data export functionality

**Technologies:**
- FastAPI for REST API framework
- Server-Sent Events (SSE) for real-time streaming
- Pydantic for request/response validation
- uvicorn for ASGI server

```python
# API Layer Structure
backend/app/api/
├── __init__.py           # API module initialization
├── qa.py                 # Q&A endpoints with SSE streaming
├── documents.py          # Document management (future)
├── search.py             # Search endpoints (future)
└── export.py             # Export endpoints (future)
```

### 2. Answer Generation Module (`backend/app/answer/`)

Handles the complete answer generation pipeline with streaming, citations, and export.

**Key Components:**
- **Prompt Builder** (`prompt.py`): Constructs system and user prompts
- **Generator** (`generator.py`): Streams LLM responses with citations
- **PDF Generator** (`pdf.py`): Creates formatted PDF reports
- **History Tracker** (`history.py`): Logs queries and generates analytics

**Data Flow:**
1. Question received → Prompt construction
2. Context retrieval → Prompt enhancement
3. LLM streaming → Token-by-token response
4. Citation injection → Source linking
5. History logging → Analytics update

```python
# Answer Module Architecture
backend/app/answer/
├── __init__.py           # Module exports
├── prompt.py             # Prompt building and templates
├── generator.py          # Streaming answer generation
├── pdf.py                # PDF export with WeasyPrint
└── history.py            # Query history and analytics
```

### 3. Retrieval System (`backend/app/retriever/`)

Manages document search, context retrieval, and relevance ranking.

**Key Components:**
- **Vector Search**: Semantic similarity using embeddings
- **Reranking**: Improves relevance with cross-encoder models
- **Context Assembly**: Combines multiple sources into coherent context
- **Caching**: Optimizes repeated queries

**Technologies:**
- SQLite-vec for vector storage and similarity search
- Sentence Transformers for embeddings
- Cross-encoder models for reranking
- LRU caching for performance optimization

### 4. Data Ingestion Pipeline (`backend/app/ingest/`)

Processes documents and extracts structured information for storage.

**Key Components:**
- **Document Parser**: Extracts text from various formats
- **Entity Extraction**: LLM-powered entity and relationship extraction
- **Chunking Strategy**: Intelligent text segmentation
- **Embedding Generation**: Vector representations for search

**Enhanced Features:**
- Retry mechanisms for API reliability
- Response caching for performance
- Batch processing with concurrency control
- Multiple JSON parsing strategies

### 5. Core Infrastructure (`backend/app/core/`)

Provides shared services and cross-cutting concerns.

**Key Components:**
- **Singleton Pattern**: Manages shared resources (DB, LLM, Logger)
- **Configuration Management**: Centralized settings with overrides
- **Logging System**: Structured logging with multiple levels
- **Database Connections**: Connection pooling and management

## Data Architecture

### Vector Storage Strategy

```
Document Processing Flow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Raw Text   │───▶│   Chunks    │───▶│ Embeddings  │
└─────────────┘    └─────────────┘    └─────────────┘
                          │                    │
                          ▼                    ▼
                   ┌─────────────┐    ┌─────────────┐
                   │  Metadata   │    │SQLite-vec DB│
                   └─────────────┘    └─────────────┘
```

**Storage Schema:**
- **Chunks Table**: Text segments with metadata
- **Embeddings Table**: Vector representations
- **Documents Table**: Source document information
- **Index Table**: Efficient similarity search structures

### Graph Database Design

```
Entity-Relationship Model:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Entity    │───▶│Relationship │◀───│   Entity    │
│    Type     │    │    Type     │    │    Type     │
│  PERSON     │    │ WORKS_FOR   │    │ORGANIZATION │
│  LOCATION   │    │ LOCATED_IN  │    │  CONCEPT    │
│  EVENT      │    │ PART_OF     │    │  ARTIFACT   │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Graph Schema:**
- **Entities Table**: Named entities with types and confidence
- **Relationships Table**: Connections between entities
- **Occurrences Table**: Entity mentions in documents
- **Confidence Scores**: Reliability metrics for extraction

## Communication Patterns

### 1. Request-Response Pattern

Standard HTTP requests for stateless operations:
- Document upload and metadata retrieval
- History queries and statistics
- Configuration management

### 2. Streaming Pattern

Server-Sent Events for real-time data:
- Token-by-token answer generation
- Progress updates for long-running operations
- Live analytics and monitoring

```javascript
// Client-side SSE handling
const eventSource = new EventSource('/api/qa/ask');
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    handleStreamingResponse(data);
};
```

### 3. Async Processing Pattern

Background processing for heavy operations:
- Document ingestion and entity extraction
- Batch vector embedding generation
- Large-scale data exports

## Security Architecture

### Authentication & Authorization (Future)

```
Security Flow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│  API Key    │───▶│Authorization│
│             │    │Validation   │    │   Service   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Session    │    │Rate Limiting│    │   Access    │
│ Management  │    │  Service    │    │  Control    │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Security Features:**
- API key authentication
- Rate limiting per client
- Request validation and sanitization
- Secure file upload handling
- CORS configuration for web clients

### Data Privacy

- Local data processing (no external data transmission)
- Configurable data retention policies
- Secure file storage with access controls
- Audit logging for data access

## Scalability Considerations

### Horizontal Scaling

**Current Architecture:**
- Single-instance deployment with local storage
- In-memory caching for performance
- Local file system for document storage

**Future Scaling Options:**
- Database clustering with read replicas
- Distributed vector storage (Pinecone, Weaviate)
- Container orchestration (Kubernetes)
- Load balancing for API endpoints

### Performance Optimization

**Current Optimizations:**
- Singleton pattern for resource reuse
- Connection pooling for database access
- Async/await for I/O operations
- Streaming responses for large data

**Future Optimizations:**
- GPU acceleration for embeddings
- Distributed caching (Redis)
- Content Delivery Network (CDN) for static files
- Query optimization and indexing strategies

## Monitoring & Observability

### Logging Strategy

```python
# Structured logging with multiple levels
logger.info("Query processed", extra={
    "query_id": query_id,
    "response_time": elapsed_time,
    "sources_used": len(sources),
    "user_id": user_id
})
```

**Log Categories:**
- **Application Logs**: Business logic and user actions
- **Performance Logs**: Response times and resource usage
- **Error Logs**: Exceptions and failure scenarios
- **Audit Logs**: Security-related events

### Metrics Collection

**Current Metrics:**
- Query response times
- Document processing statistics
- Error rates and types
- Resource utilization

**Future Metrics:**
- User engagement analytics
- Model performance metrics
- System health indicators
- Business intelligence data

## Extension Points

### Plugin Architecture (Future)

```python
# Plugin interface for extensibility
class AnalysisPlugin:
    def analyze(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError
    
    def get_metadata(self) -> Dict[str, str]:
        raise NotImplementedError

# Registration system
plugin_manager.register("sentiment", SentimentPlugin())
plugin_manager.register("topic", TopicModelingPlugin())
```

### Custom Model Integration

- Support for different LLM providers
- Custom embedding model configuration
- Pluggable entity extraction strategies
- Configurable retrieval algorithms

### API Extensions

- Custom endpoint registration
- Middleware for cross-cutting concerns
- Event system for decoupled components
- Webhook support for external integrations

## Technology Stack Summary

### Backend Technologies
- **Framework**: FastAPI 0.104+ with async support
- **Language**: Python 3.12.9
- **Database**: SQLite with sqlite-vec extension
- **Vector Search**: sentence-transformers embeddings
- **LLM Integration**: LangChain with OpenRouter
- **PDF Generation**: WeasyPrint with HTML fallback
- **Testing**: pytest with async support

### Development Tools
- **Environment**: Conda/pip with virtual environments
- **Code Quality**: black, isort, flake8, mypy
- **Documentation**: Markdown with comprehensive guides
- **Version Control**: Git with conventional commits

### Deployment Options
- **Development**: Local uvicorn server
- **Production**: Docker containers (future)
- **Scaling**: Kubernetes orchestration (future)
- **Monitoring**: Structured logging with external tools

## Design Principles

### 1. Modularity
- Clear separation of concerns
- Minimal coupling between components
- Well-defined interfaces and contracts

### 2. Scalability
- Async processing for I/O operations
- Stateless design where possible
- Horizontal scaling readiness

### 3. Reliability
- Comprehensive error handling
- Graceful degradation strategies
- Retry mechanisms for transient failures

### 4. Performance
- Caching at multiple levels
- Streaming for large responses
- Efficient data structures and algorithms

### 5. Maintainability
- Consistent coding standards
- Comprehensive testing coverage
- Clear documentation and examples

This architecture provides a solid foundation for the current Phase 5 implementation while maintaining flexibility for future enhancements and scaling requirements.


---

# UI Component Documentation

# UI Component Documentation

## Overview
This document provides comprehensive documentation for all UI components in the SocioRAG frontend application. Each component is designed to be reusable, accessible, and support both light/dark themes with internationalization.

## Base UI Components

### Card Component
**Location**: `src/components/ui/Card.tsx`

A flexible container component for grouping related content.

```typescript
interface CardProps {
  children: ComponentChildren;
  className?: string;
}

// Usage
<Card className="p-6">
  <h3 className="text-lg font-semibold mb-4">Card Title</h3>
  <p className="text-gray-600 dark:text-gray-300">Card content goes here.</p>
</Card>
```

**Features**:
- Responsive design
- Dark mode support
- Custom styling via className
- Semantic HTML structure

**Styling**:
- Background: White (light) / Gray-800 (dark)
- Border: Gray-200 (light) / Gray-700 (dark)
- Shadow: Subtle drop shadow
- Border radius: 8px

### Tabs Component
**Location**: `src/components/ui/Tabs.tsx`

A tabbed interface for organizing content into switchable panels.

```typescript
interface TabsProps {
  defaultValue: string;
  children: ComponentChildren;
  className?: string;
}

// Usage
<Tabs defaultValue="search">
  <Tabs.List className="mb-4">
    <Tabs.Trigger value="search">Search</Tabs.Trigger>
    <Tabs.Trigger value="upload">Upload</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Content value="search">
    <SearchInterface />
  </Tabs.Content>
  <Tabs.Content value="upload">
    <FileUploader />
  </Tabs.Content>
</Tabs>
```

**Features**:
- Keyboard navigation (Arrow keys, Tab, Enter, Space)
- ARIA accessibility attributes
- Active state management
- Custom trigger and content styling

**Accessibility**:
- `role="tablist"` for tab container
- `role="tab"` for individual tabs
- `role="tabpanel"` for content panels
- `aria-selected` for active tab
- `tabindex` management

## Navigation Components

### Navigation Component
**Location**: `src/components/Navigation.tsx`

Main navigation component with responsive design and mobile menu support.

```typescript
interface NavigationProps {
  currentPath: string;
}

// Usage
<Navigation currentPath="/history" />
```

**Features**:
- Responsive design (desktop horizontal, mobile hamburger)
- Route highlighting
- Theme toggle integration
- RTL support for Arabic
- Mobile menu overlay

**Navigation Items**:
- Home (`/`)
- History (`/history`)
- Saved (`/saved`)
- Settings (`/settings`)

**Mobile Behavior**:
- Hamburger menu button
- Full-screen overlay menu
- Touch-friendly tap targets
- Auto-close on navigation

## Search Components

### SearchBar Component
**Location**: `src/components/SearchBar.tsx`

Advanced search interface with translation toggle and keyboard shortcuts.

```typescript
interface SearchBarProps {
  onSearch: (query: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

// Usage
<SearchBar 
  onSearch={handleSearch}
  disabled={isProcessing}
  placeholder="Ask a question..."
/>
```

**Features**:
- Multi-line text input
- Translation toggle button
- Enter to submit (Shift+Enter for new line)
- Loading states
- Character count (optional)
- Input validation

**Keyboard Shortcuts**:
- `Enter`: Submit search
- `Shift + Enter`: New line
- `Ctrl/Cmd + A`: Select all
- `Escape`: Clear focus

**Styling States**:
- Default: Gray border
- Focus: Blue border with shadow
- Error: Red border
- Disabled: Reduced opacity

### StreamAnswer Component
**Location**: `src/components/StreamAnswer.tsx`

Real-time answer display with markdown rendering and typing animation.

```typescript
interface StreamAnswerProps {
  markdown: string;
  isComplete: boolean;
  error?: string | null;
  language?: 'en' | 'ar';
}

// Usage
<StreamAnswer 
  markdown={responseText}
  isComplete={streamComplete}
  error={errorMessage}
  language="en"
/>
```

**Features**:
- Markdown rendering with syntax highlighting
- Typing animation effect
- RTL text support
- Error state display
- Loading indicators
- Scrollable content

**Markdown Support**:
- Headers (H1-H6)
- Bold and italic text
- Lists (ordered and unordered)
- Code blocks and inline code
- Links (external open in new tab)
- Blockquotes
- Tables

**RTL Handling**:
- Automatic text direction detection
- Mixed content support (Arabic + English)
- Proper alignment for different languages

## File Management Components

### FileUploader Component
**Location**: `src/components/FileUploader.tsx`

Drag-and-drop file upload with progress tracking and multiple file support.

```typescript
interface FileUploaderProps {
  onUpload: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  maxFiles?: number;
  maxSize?: number; // in bytes
}

// Usage
<FileUploader 
  onUpload={handleFileUpload}
  accept=".pdf"
  multiple={true}
  maxFiles={5}
  maxSize={10 * 1024 * 1024} // 10MB
/>
```

**Features**:
- Drag and drop interface
- Click to browse files
- File type validation
- File size validation
- Progress indicators
- Success/error feedback
- Preview of selected files

**Supported Events**:
- `dragover`: Visual feedback
- `dragleave`: Reset visual state
- `drop`: Handle file drop
- `change`: Handle file input

**Visual States**:
- Idle: Dashed border
- Drag over: Solid blue border
- Uploading: Progress bar
- Success: Green checkmark
- Error: Red error message

**File Validation**:
- MIME type checking
- File size limits
- File count limits
- Custom validation functions

### ProgressBar Component
**Location**: `src/components/ProgressBar.tsx`

Visual progress indicator for upload and processing operations.

```typescript
interface ProgressBarProps {
  progress: number; // 0-100
  status?: 'idle' | 'processing' | 'complete' | 'error';
  message?: string;
  showPercentage?: boolean;
}

// Usage
<ProgressBar 
  progress={uploadProgress}
  status="processing"
  message="Uploading document..."
  showPercentage={true}
/>
```

**Features**:
- Animated progress bar
- Status indicators
- Custom messages
- Percentage display
- Color coding by status

**Status Colors**:
- `idle`: Gray
- `processing`: Blue with animation
- `complete`: Green
- `error`: Red

**Animation**:
- Smooth progress transitions
- Pulse effect for processing
- Success celebration animation

## Page Components

### Home Page
**Location**: `src/pages/Home.tsx`

Main application page with search and upload functionality.

**Layout Structure**:
```typescript
<div className="container mx-auto px-4 py-8">  <header className="text-center mb-8">
    <h1>SocioRAG</h1>
    <p>Intelligent Document Analysis</p>
  </header>
  
  <Tabs defaultValue="search">
    <Tabs.List>
      <Tabs.Trigger value="search">Search</Tabs.Trigger>
      <Tabs.Trigger value="upload">Upload</Tabs.Trigger>
    </Tabs.List>
    
    <Tabs.Content value="search">
      <SearchBar onSearch={handleSearch} />
      {searchResults && (
        <StreamAnswer 
          markdown={searchResults}
          isComplete={isSearchComplete}
        />
      )}
    </Tabs.Content>
    
    <Tabs.Content value="upload">
      <FileUploader onUpload={handleUpload} />
      {uploadProgress > 0 && (
        <ProgressBar progress={uploadProgress} />
      )}
    </Tabs.Content>
  </Tabs>
</div>
```

**Features**:
- Tabbed interface for search/upload
- Real-time search results
- File upload with progress
- Responsive layout
- Loading states

### History Page
**Location**: `src/pages/History.tsx`

Query history management with copy-to-clipboard functionality.

**Key Components**:
- History item list
- Search result preview
- Copy-to-clipboard functionality
- Delete actions with confirmation dialogs
- Pagination

```typescript
interface HistoryItem {
  id: string;
  query: string;
  answer: string;
  timestamp: string;
  language: string;
}

// History Item Display
<Card className="p-4">
  <div className="flex justify-between items-start">
    <div className="flex-1">
      <p className="font-medium">{item.query}</p>
      <div className="text-sm text-gray-500">
        <Clock className="w-4 h-4 mr-1" />
        {formatTimestamp(item.timestamp)}
      </div>
    </div>
    
    <div className="flex space-x-2">
      <button onClick={() => copyQueryToClipboard(item.query)}>
        <Copy className="w-4 h-4" />
        Copy Query
      </button>
      <button onClick={() => deleteItem(item.id)}>
        <Trash2 className="w-4 h-4" />
        Delete
      </button>
    </div>
  </div>
  
  {item.answer && (
    <div className="mt-3 p-3 bg-gray-50 rounded">
      <p className="text-sm">{truncateText(item.answer, 200)}</p>
    </div>
  )}
</Card>
```

### Saved Page
**Location**: `src/pages/Saved.tsx`

Saved documents management with download functionality.

**Features**:
- Grid layout for documents
- File metadata display
- Download functionality
- Search/filter capabilities
- Bulk operations

```typescript
interface SavedFile {
  id: string;
  filename: string;
  size: number;
  uploadDate: string;
  downloadUrl: string;
}

// Document Grid Item
<Card className="p-4 hover:shadow-lg transition-shadow">
  <div className="flex items-center justify-between mb-3">
    <File className="w-8 h-8 text-blue-600" />
    <button onClick={() => downloadFile(file)}>
      <Download className="w-5 h-5" />
    </button>
  </div>
  
  <h3 className="font-medium truncate" title={file.filename}>
    {file.filename}
  </h3>
  
  <div className="text-sm text-gray-500 mt-2">
    <p>Size: {formatFileSize(file.size)}</p>
    <p>Uploaded: {formatDate(file.uploadDate)}</p>
  </div>
</Card>
```

### Settings Page
**Location**: `src/pages/Settings.tsx`

Application configuration and preferences with system administration capabilities.

**Settings Categories**:

1. **Appearance**
   - Theme toggle (Light/Dark)
   - Language selection (English/Arabic)
   - Font size preferences

2. **Search Settings**
   - Top K results
   - Top K rerank
   - Temperature setting
   - Translation preferences

3. **Data Management**
   - Corpus reset
   - Export settings
   - Cache management

4. **System Configuration** ⭐ NEW
   - OpenRouter API Key management with secure input
   - System health monitoring with real-time status
   - Configuration status indicators (green checkmark/red X)
   - One-click API key updates with persistence to .env file

```typescript
// Settings Form Structure
<div className="space-y-6">
  <Card className="p-6">
    <h3 className="text-lg font-semibold mb-4">Appearance</h3>
    
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label>Dark Mode</label>
        <button 
          onClick={toggleTheme}
          className={`toggle ${isDark ? 'active' : ''}`}
        >
          <span className="toggle-slider" />
        </button>
      </div>
      
      <div className="flex items-center justify-between">
        <label>Language</label>
        <select 
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="select"
        >
          <option value="en">English</option>
          <option value="ar">العربية</option>
        </select>
      </div>
    </div>
  </Card>
  
  <Card className="p-6">
    <h3 className="text-lg font-semibold mb-4">Search Settings</h3>
    
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-2">
          Top K Results: {settings.topK}
        </label>
        <input
          type="range"
          min="1"
          max="20"
          value={settings.topK}
          onChange={(e) => updateSettings({ topK: parseInt(e.target.value) })}
          className="range"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium mb-2">
          Temperature: {settings.temperature}
        </label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          value={settings.temperature}
          onChange={(e) => updateSettings({ temperature: parseFloat(e.target.value) })}
          className="range"
        />
      </div>
    </div>
  </Card>
</div>
```

## Accessibility Features

### Keyboard Navigation
All components support keyboard navigation:

- **Tab**: Move focus between interactive elements
- **Enter/Space**: Activate buttons and controls
- **Arrow Keys**: Navigate within complex widgets (tabs, menus)
- **Escape**: Close modals and overlays

### ARIA Attributes
Components include appropriate ARIA labels:

```typescript
// Button with icon
<button 
  aria-label="Close dialog"
  className="btn-icon"
>
  <X className="w-4 h-4" />
</button>

// Form input
<input
  type="text"
  aria-describedby="search-help"
  aria-invalid={hasError}
  className="input"
/>
<div id="search-help" className="text-sm text-gray-500">
  Enter your search query
</div>

// Loading state
<div 
  role="status" 
  aria-live="polite"
  aria-label="Searching..."
>
  <Loader className="animate-spin" />
</div>
```

### Focus Management
- Visible focus indicators
- Logical tab order
- Focus trapping in modals
- Skip links for navigation

## Responsive Design

### Breakpoints
```css
/* Mobile: < 768px */
.container {
  padding: 1rem;
}

/* Tablet: 768px - 1024px */
@media (min-width: 768px) {
  .container {
    padding: 2rem;
    max-width: 768px;
  }
}

/* Desktop: > 1024px */
@media (min-width: 1024px) {
  .container {
    max-width: 1024px;
    margin: 0 auto;
  }
}
```

### Mobile Adaptations
- Touch-friendly button sizes (44px minimum)
- Simplified navigation menu
- Stacked layouts instead of side-by-side
- Larger text for readability
- Swipe gestures for tabs

### Component Responsive Behavior
```typescript
// Navigation: Desktop horizontal, mobile hamburger
<nav className="hidden md:flex">
  {/* Desktop navigation */}
</nav>
<nav className="md:hidden">
  {/* Mobile navigation */}
</nav>

// Cards: Grid on desktop, stack on mobile
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => <Card key={item.id}>{item.content}</Card>)}
</div>

// Search: Full width on mobile, constrained on desktop
<div className="w-full max-w-2xl mx-auto">
  <SearchBar />
</div>
```

## Styling Guidelines

### Color System
```css
/* Primary Colors */
--color-primary-50: #eff6ff;
--color-primary-100: #dbeafe;
--color-primary-500: #3b82f6;
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;

/* Semantic Colors */
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
--color-info: #3b82f6;
```

### Typography Scale
```css
/* Font Sizes */
.text-xs { font-size: 0.75rem; }    /* 12px */
.text-sm { font-size: 0.875rem; }   /* 14px */
.text-base { font-size: 1rem; }     /* 16px */
.text-lg { font-size: 1.125rem; }   /* 18px */
.text-xl { font-size: 1.25rem; }    /* 20px */
.text-2xl { font-size: 1.5rem; }    /* 24px */
.text-3xl { font-size: 1.875rem; }  /* 30px */

/* Font Weights */
.font-normal { font-weight: 400; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }
```

### Spacing System
```css
/* Spacing Scale (based on 0.25rem = 4px) */
.p-1 { padding: 0.25rem; }     /* 4px */
.p-2 { padding: 0.5rem; }      /* 8px */
.p-3 { padding: 0.75rem; }     /* 12px */
.p-4 { padding: 1rem; }        /* 16px */
.p-6 { padding: 1.5rem; }      /* 24px */
.p-8 { padding: 2rem; }        /* 32px */
```

## Performance Considerations

### Component Optimization
```typescript
// Memoize expensive components
import { memo } from 'preact/compat';

const ExpensiveComponent = memo(({ data }: { data: any[] }) => {
  return (
    <div>
      {data.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
});

// Use callback memoization for event handlers
import { useCallback } from 'preact/hooks';

function ParentComponent() {
  const handleClick = useCallback((id: string) => {
    // Handle click
  }, []);

  return <ChildComponent onClick={handleClick} />;
}
```

### Bundle Size Optimization
- Tree shaking for unused code
- Dynamic imports for large components
- Optimized icon loading
- Compressed images

### Loading States
All components handle loading states gracefully:

```typescript
function DataComponent() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="animate-spin w-6 h-6 mr-2" />
        <span>Loading...</span>
      </div>
    );
  }

  return <div>{/* Render data */}</div>;
}
```

---

This documentation covers all major UI components in the SocioRAG frontend. Each component is designed to be maintainable, accessible, and performant while providing a consistent user experience across the application.

