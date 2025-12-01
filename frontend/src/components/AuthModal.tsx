import { useEffect, useRef, useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth, TelegramAuthData } from '../hooks/useAuth';
import './AuthModal.css';

// Bot username - should match your Telegram bot
const BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || '';

export default function AuthModal() {
  const { showAuthModal, closeAuthModal, login, isLoading } = useAuth();
  const containerRef = useRef<HTMLDivElement>(null);
  const [widgetError, setWidgetError] = useState(false);

  const isBotConfigured = BOT_USERNAME && BOT_USERNAME !== 'your_bot_username';

  const handleTelegramAuth = useCallback(async (user: TelegramAuthData) => {
    try {
      await login(user);
    } catch (error) {
      console.error('Login failed:', error);
      alert('Ошибка авторизации. Попробуйте ещё раз.');
    }
  }, [login]);

  // Dev mode login - creates a fake user for local development
  const handleDevLogin = useCallback(async () => {
    const devUser: TelegramAuthData = {
      id: 123456789,
      first_name: 'Test',
      last_name: 'User',
      username: 'testuser',
      photo_url: '',
      auth_date: Math.floor(Date.now() / 1000),
      hash: 'dev_mode_hash',
    };
    
    try {
      await login(devUser);
    } catch (error) {
      console.error('Dev login failed:', error);
      alert('Ошибка входа. Проверьте, что бэкенд запущен.');
    }
  }, [login]);

  // Set up the global callback for Telegram widget
  useEffect(() => {
    (window as unknown as { TelegramLoginWidget?: { dataOnauth: (user: TelegramAuthData) => void } }).TelegramLoginWidget = {
      dataOnauth: handleTelegramAuth,
    };

    return () => {
      delete (window as unknown as { TelegramLoginWidget?: unknown }).TelegramLoginWidget;
    };
  }, [handleTelegramAuth]);

  // Load Telegram widget when modal opens
  useEffect(() => {
    if (!showAuthModal || !containerRef.current || !isBotConfigured) return;

    setWidgetError(false);
    
    // Clear any existing widget
    containerRef.current.innerHTML = '';

    // Create Telegram Login Widget script
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', BOT_USERNAME);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-radius', '4');
    script.setAttribute('data-onauth', 'TelegramLoginWidget.dataOnauth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;
    
    // Handle script errors
    script.onerror = () => setWidgetError(true);

    containerRef.current.appendChild(script);
    
    // Check if widget loaded correctly after a delay
    const timeout = setTimeout(() => {
      if (containerRef.current && containerRef.current.querySelector('iframe') === null) {
        setWidgetError(true);
      }
    }, 3000);
    
    return () => clearTimeout(timeout);
  }, [showAuthModal, isBotConfigured]);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeAuthModal();
    };
    
    if (showAuthModal) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [showAuthModal, closeAuthModal]);

  return (
    <AnimatePresence>
      {showAuthModal && (
        <motion.div
          className="auth-modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={closeAuthModal}
        >
          <motion.div
            className="auth-modal"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            onClick={(e) => e.stopPropagation()}
          >
            <button className="auth-modal-close" onClick={closeAuthModal}>
              ✕
            </button>
            
            <div className="auth-modal-content">
              <div className="auth-modal-icon">🥊</div>
              <h2 className="auth-modal-title">Войти в аккаунт</h2>
              <p className="auth-modal-subtitle">
                Авторизуйтесь через Telegram, чтобы делать прогнозы на бои
              </p>
              
              <div className="auth-modal-widget">
                {isLoading ? (
                  <div className="auth-modal-loading">
                    <div className="loading-spinner" />
                    <span>Авторизация...</span>
                  </div>
                ) : !isBotConfigured ? (
                  <div className="auth-modal-dev-mode">
                    <p className="dev-mode-title">🛠 Режим разработки</p>
                    <p className="dev-mode-text">
                      Telegram Login требует публичный домен с HTTPS.
                      Для локальной разработки используйте тестовый вход:
                    </p>
                    <button 
                      className="dev-login-btn"
                      onClick={() => handleDevLogin()}
                    >
                      Войти как тестовый пользователь
                    </button>
                    <p className="dev-mode-hint">
                      Для продакшена настройте VITE_TELEGRAM_BOT_USERNAME
                    </p>
                  </div>
                ) : widgetError ? (
                  <div className="auth-modal-config-error">
                    <p className="config-error-title">❌ Ошибка загрузки виджета</p>
                    <p className="config-error-text">
                      Проверьте настройки бота в @BotFather
                    </p>
                  </div>
                ) : (
                  <div ref={containerRef} className="telegram-widget-container" />
                )}
              </div>
              
              {isBotConfigured && !widgetError && (
                <p className="auth-modal-hint">
                  Нажмите кнопку выше для авторизации через Telegram
                </p>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

