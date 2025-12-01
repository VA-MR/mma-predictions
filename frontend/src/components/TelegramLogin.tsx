import { useEffect, useRef, useCallback } from 'react';
import { useAuth, useTelegramLogin } from '../hooks/useAuth';
import './TelegramLogin.css';

// Bot username - should match your Telegram bot
const BOT_USERNAME = 'your_bot_username'; // Replace with actual bot username

export default function TelegramLogin() {
  const { login, isLoading } = useAuth();
  const containerRef = useRef<HTMLDivElement>(null);

  const handleTelegramAuth = useCallback(async (user: {
    id: number;
    first_name: string;
    last_name?: string;
    username?: string;
    photo_url?: string;
    auth_date: number;
    hash: string;
  }) => {
    try {
      await login(user);
    } catch (error) {
      console.error('Login failed:', error);
      alert('Login failed. Please try again.');
    }
  }, [login]);

  useTelegramLogin(handleTelegramAuth);

  useEffect(() => {
    if (!containerRef.current) return;

    // Clear any existing widget
    containerRef.current.innerHTML = '';

    // Create Telegram Login Widget script
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', BOT_USERNAME);
    script.setAttribute('data-size', 'medium');
    script.setAttribute('data-radius', '8');
    script.setAttribute('data-onauth', 'TelegramLoginWidget.dataOnauth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;

    containerRef.current.appendChild(script);
  }, []);

  if (isLoading) {
    return <div className="telegram-login-loading">Loading...</div>;
  }

  return (
    <div className="telegram-login-container">
      <div ref={containerRef} className="telegram-widget" />
      <p className="telegram-hint">Sign in with Telegram to make picks</p>
    </div>
  );
}

