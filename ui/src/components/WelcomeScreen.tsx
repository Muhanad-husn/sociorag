import { useState } from 'preact/hooks';
import { Card } from './ui/Card';

interface WelcomeScreenProps {
  onContinue: () => void;
}

export function WelcomeScreen({ onContinue }: WelcomeScreenProps) {
  const [loading, setLoading] = useState(false);

  const handleContinue = () => {
    setLoading(true);
    // Add any initialization logic here
    setTimeout(() => {
      onContinue();
    }, 1000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <Card className="w-full max-w-md p-8 shadow-lg">
        <div className="text-center space-y-6">
          <div className="flex justify-center">
            <img 
              src="/socioRAG-logo.png" 
              alt="SocioRAG Logo" 
              className="h-32 w-32 animate-fade-in" 
            />
          </div>
          
          <div className="space-y-2">
            <h1 className="text-3xl font-bold">SocioRAG</h1>
            <p className="text-lg text-muted-foreground">
              Intelligent Document Analysis
            </p>
          </div>
          
          <div className="pt-4">
            <button 
              onClick={handleContinue}
              disabled={loading}
              className="btn-primary w-full py-2"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span className="ml-2">Loading...</span>
                </div>
              ) : (
                'Get Started'
              )}
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
}
