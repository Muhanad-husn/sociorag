import { useState, useEffect } from 'preact/hooks';
import { Home, History, Save, Settings, Menu, X, Moon, Sun } from 'lucide-preact';
import { route } from 'preact-router';
import { useAppStore } from '../hooks/useLocalState';
import { t } from '../lib/i18n';

const navItems = [
  { id: 'home', icon: Home, path: '/' },
  { id: 'history', icon: History, path: '/history' },
  { id: 'saved', icon: Save, path: '/saved' },
  { id: 'settings', icon: Settings, path: '/settings' },
];

interface NavigationProps {
  currentPath: string;
}

export function Navigation({ currentPath }: NavigationProps) {
  const { theme, language, toggleTheme } = useAppStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Close mobile menu when route changes
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [currentPath]);

  const handleNavigation = (path: string) => {
    route(path);
    setIsMobileMenuOpen(false);
  };

  const getCurrentPageId = () => {
    if (currentPath === '/') return 'home';
    const path = currentPath.split('/')[1];
    return navItems.find(item => item.path.includes(path))?.id || 'home';
  };

  const currentPageId = getCurrentPageId();
  const isRTL = language === 'ar';

  return (
    <>
      {/* Desktop Navigation */}
      <nav className="hidden md:flex fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className={`flex justify-between items-center h-16 ${isRTL ? 'flex-row-reverse' : ''}`}>
            {/* Logo */}
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                SocioGraph
              </h1>
            </div>

            {/* Navigation Items */}
            <div className="flex items-center space-x-8 rtl:space-x-reverse">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPageId === item.id;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavigation(item.path)}
                    className={`flex items-center space-x-2 rtl:space-x-reverse px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30'
                        : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}                  >
                    <Icon className="w-4 h-4" />
                    <span>{t(`navigation.${item.id}`, language)}</span>
                  </button>
                );
              })}
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              aria-label={t('navigation.toggleTheme', language)}
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <nav className="md:hidden fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
        <div className="px-4 sm:px-6">
          <div className={`flex justify-between items-center h-16 ${isRTL ? 'flex-row-reverse' : ''}`}>
            {/* Logo */}
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">
              SocioGraph
            </h1>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              aria-label={t('navigation.menu', language)}
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu Overlay */}
        {isMobileMenuOpen && (
          <div className="absolute top-16 left-0 right-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 shadow-lg">
            <div className="px-4 py-2 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPageId === item.id;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavigation(item.path)}
                    className={`w-full flex items-center space-x-3 rtl:space-x-reverse px-3 py-3 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30'
                        : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800'
                    } ${isRTL ? 'text-right' : 'text-left'}`}                  >
                    <Icon className="w-5 h-5" />
                    <span>{t(`navigation.${item.id}`, language)}</span>
                  </button>
                );
              })}
              
              {/* Theme Toggle for Mobile */}
              <button
                onClick={toggleTheme}
                className={`w-full flex items-center space-x-3 rtl:space-x-reverse px-3 py-3 rounded-md text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                  isRTL ? 'text-right' : 'text-left'
                }`}
              >
                {theme === 'dark' ? (
                  <>
                    <Sun className="w-5 h-5" />
                    <span>{t('navigation.lightMode', language)}</span>
                  </>
                ) : (
                  <>
                    <Moon className="w-5 h-5" />
                    <span>{t('settings.darkMode', language)}</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </nav>

      {/* Mobile Menu Backdrop */}
      {isMobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/20"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </>
  );
}
