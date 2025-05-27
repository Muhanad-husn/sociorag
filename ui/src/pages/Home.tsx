import { useState } from 'preact/hooks';
import { SearchBar } from '../components/SearchBar';
import { StreamAnswer } from '../components/StreamAnswer';
import { FileUploader } from '../components/FileUploader';
import { ProgressBar } from '../components/ProgressBar';
import { useSSE } from '../hooks/useSSE';
import { useAppStore } from '../hooks/useLocalState';
import { createSearchStream } from '../lib/api';
import { t } from '../lib/i18n';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/Tabs';
import { Card } from '../components/ui/Card';

export function Home() {
  const { currentQuery, setCurrentQuery, settings, isProcessing, setIsProcessing } = useAppStore();
  const [searchSource, setSearchSource] = useState<EventSource | null>(null);
  const [activeTab, setActiveTab] = useState('search');
  
  const { text: answer, isComplete, error } = useSSE(searchSource, {
    onComplete: () => {
      console.log('Search completed');
    },
    onError: (error) => {
      console.error('Search error:', error);
    }
  });

  const handleSearch = () => {
    if (!currentQuery.trim()) return;
    
    // Close existing search if any
    if (searchSource) {
      searchSource.close();
    }
    
    // Create new search stream
    const source = createSearchStream(currentQuery, settings);
    setSearchSource(source);
  };

  const handleUploadStart = () => {
    setIsProcessing(true);
  };

  const handleUploadComplete = (filename: string) => {
    console.log('Upload completed:', filename);
    // Processing will continue in background, ProgressBar will handle it
  };

  const handleProcessingComplete = () => {
    setIsProcessing(false);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold">{t('appTitle')}</h1>
          <p className="text-lg text-muted-foreground">
            Ask questions about your documents
          </p>
        </div>

        {/* Progress Bar */}
        <ProgressBar
          isVisible={isProcessing}
          onComplete={handleProcessingComplete}
        />

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="search">Search</TabsTrigger>
            <TabsTrigger value="upload">Upload</TabsTrigger>
          </TabsList>

          <TabsContent value="search" className="space-y-6">
            {/* Search Section */}
            <Card className="p-6">
              <SearchBar
                value={currentQuery}
                onChange={setCurrentQuery}
                onSubmit={handleSearch}
                disabled={!!searchSource && !isComplete}
              />
            </Card>

            {/* Results Section */}
            {(answer || error) && (
              <StreamAnswer
                markdown={answer}
                isComplete={isComplete}
                error={error}
              />
            )}

            {/* Quick Start Guide */}
            {!answer && !error && (
              <Card className="p-6 bg-accent/50">
                <h3 className="text-lg font-semibold mb-3">Quick Start</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>• Upload PDF documents using the Upload tab</li>
                  <li>• Wait for processing to complete</li>
                  <li>• Ask questions about your documents</li>
                  <li>• Toggle Arabic translation if needed</li>
                </ul>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="upload" className="space-y-6">
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">{t('upload.title')}</h2>
              <FileUploader
                onUploadStart={handleUploadStart}
                onUploadComplete={handleUploadComplete}
              />
            </Card>

            {/* Upload Instructions */}
            <Card className="p-6 bg-accent/50">
              <h3 className="text-lg font-semibold mb-3">Upload Instructions</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Only PDF files are supported</li>
                <li>• Maximum file size: 50MB</li>
                <li>• Files are processed automatically after upload</li>
                <li>• You can upload multiple files at once</li>
                <li>• Processing time depends on document size and complexity</li>
              </ul>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
