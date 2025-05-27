import { useState } from 'preact/hooks';
import { Router, Route } from 'preact-router';
import { Toaster } from 'sonner';
import { useAppStore } from './hooks/useLocalState';
import { Home } from './pages/Home';
import { History } from './pages/History';
import { Saved } from './pages/Saved';
import { Settings } from './pages/Settings';
import { Navigation } from './components/Navigation';
import { getDirection } from './lib/i18n';

export function App() {
  const { theme, language } = useAppStore();
  const [currentPath, setCurrentPath] = useState('/');

  const handleRoute = (e: any) => {
    setCurrentPath(e.url);
  };

  return (
    <div 
      className={`min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors ${theme}`}
      dir={getDirection(language)}
    >
      {/* Navigation */}
      <Navigation currentPath={currentPath} />
      
      {/* Main Content */}
      <main className="pt-16">
        <Router onChange={handleRoute}>
          <Route path="/" component={Home} />
          <Route path="/history" component={History} />
          <Route path="/saved" component={Saved} />
          <Route path="/settings" component={Settings} />
        </Router>
      </main>

      {/* Toast Notifications */}
      <Toaster 
        position={language === 'ar' ? 'bottom-left' : 'bottom-right'}
        theme={theme === 'dark' ? 'dark' : 'light'}
        richColors
      />
    </div>
  );
}
