import { useState } from 'preact/hooks';
import { SearchBar } from '../components/SearchBar';
import { StreamAnswer } from '../components/StreamAnswer';
import { FileUploader } from '../components/FileUploader';
import { ProgressBar } from '../components/ProgressBar';
import { useAsyncRequest } from '../hooks/useAsyncRequest';
import { useAppStore } from '../hooks/useLocalState';
import { askQuestion, type AskResponse } from '../lib/api';
import { t } from '../lib/i18n';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/Tabs';
import { Card } from '../components/ui/Card';
import clsx from 'clsx';

export function Home() {
  const { currentQuery, setCurrentQuery, settings, isProcessing, setIsProcessing, language } = useAppStore();  const [activeTab, setActiveTab] = useState('search');
  const [answer, setAnswer] = useState('');
  const [answerHtml, setAnswerHtml] = useState('');
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  
  const { execute: executeSearch, loading: isSearching, error } = useAsyncRequest<AskResponse>();
  const handleSearch = async () => {
    if (!currentQuery.trim()) return;
    
    try {
      // Clear previous results when starting a new search
      setAnswer('');
      setAnswerHtml('');
      setPdfUrl(null);
      
      const response = await executeSearch(() => askQuestion(currentQuery, settings));
      if (response) {
        setAnswer(response.answer);
        setAnswerHtml(response.answer_html || '');
        setPdfUrl(response.pdf_url || null);
      }
    } catch (err) {
      console.error('Search error:', err);
      setAnswer('');
      setAnswerHtml('');
      setPdfUrl(null);
    }
  };

  const handleUploadStart = () => {
    setIsProcessing(true);
  };

  const handleUploadComplete = (filename: string) => {
    console.log('Upload completed:', filename);
    // Switch to the search tab automatically after file upload
    setActiveTab('search');
    // Processing will continue in background, ProgressBar will handle it
  };

  const handleProcessingComplete = () => {
    setIsProcessing(false);
    // UI components will automatically be re-enabled when isProcessing is set to false
  };  // Determine if the UI should be in a loading state
  const isLoading = isSearching || isProcessing;
  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="space-y-8">{/* Header */}
        <div className="text-center space-y-2">
          <div className="flex justify-center mb-2">
            <img 
              src="/socioRAG-logo.png" 
              alt="SocioRAG Logo" 
              className="h-16 w-16" 
            />
          </div>          <h1 className="text-4xl font-bold sm:prose-base lg:prose-lg">{t('appTitle', language)}</h1>
          <p className="text-lg text-muted-foreground sm:prose-base lg:prose-lg">
            {t('home.subtitle', language)}
          </p>
        </div>

        {/* Progress Bar */}
        <ProgressBar
          isVisible={isProcessing}
          onComplete={handleProcessingComplete}
        />        {/* Main Tabs */}        <Tabs 
          value={activeTab} 
          onValueChange={(value) => {
            // Only allow tab changes if not loading or processing
            if (!isLoading) {
              setActiveTab(value);
            }
          }}
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger 
              value="search" 
              className={clsx(
                "hover-lift active-press focus-ring-enhanced",
                isLoading ? "pointer-events-none opacity-60" : ""
              )}
            >
              {t('home.searchTab', language)}
            </TabsTrigger>
            <TabsTrigger 
              value="upload" 
              className={clsx(
                "hover-lift active-press focus-ring-enhanced",
                isLoading ? "pointer-events-none opacity-60" : ""
              )}
            >
              {t('home.uploadTab', language)}
            </TabsTrigger>
          </TabsList>          <TabsContent value="search" className="space-y-6">
            {/* Search Section */}            <Card className={clsx(
              "p-6 card-interactive",
              isLoading ? 'opacity-80 pointer-events-none' : ''
            )}>
              <SearchBar
                value={currentQuery}
                onChange={setCurrentQuery}
                onSubmit={handleSearch}
                disabled={isLoading}
                language={language}
              />
            </Card>{/* Results Section */}
            {(answer || error || isSearching) && (
              <StreamAnswer
                html={answerHtml}
                markdown={answer}
                isComplete={!isSearching}
                error={error}
                pdfUrl={pdfUrl || undefined}
                isLoading={isSearching}
              />
            )}            {/* Quick Start Guide */}
            {!answer && !error && !isSearching && (
              <Card className="p-6 surface-2 card-interactive">
                <h3 className="text-lg font-semibold mb-3">{t('home.quickStart', language)}</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>• {t('home.quickStart1', language)}</li>
                  <li>• {t('home.quickStart2', language)}</li>
                  <li>• {t('home.quickStart3', language)}</li>
                  <li>• {t('home.quickStart4', language)}</li>
                </ul>
              </Card>
            )}
          </TabsContent>          <TabsContent value="upload" className="space-y-6">
            <Card className={clsx(
              "p-6 card-interactive",
              isLoading ? 'opacity-80 pointer-events-none' : ''
            )}>
              <h2 className="text-xl font-semibold mb-4">{t('upload.title', language)}</h2>
              <FileUploader
                onUploadStart={handleUploadStart}
                onUploadComplete={handleUploadComplete}
                disabled={isLoading}
              />
            </Card>            {/* Upload Instructions */}
            <Card className="p-6 surface-2 card-interactive">
              <h3 className="text-lg font-semibold mb-3">{t('home.uploadInstructions', language)}</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• {t('home.uploadInstr1', language)}</li>
                <li>• {t('home.uploadInstr2', language)}</li>
                <li>• {t('home.uploadInstr3', language)}</li>
                <li>• {t('home.uploadInstr4', language)}</li>
                <li>• {t('home.uploadInstr5', language)}</li>
              </ul>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
