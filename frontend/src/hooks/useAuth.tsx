import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, getCurrentUser, telegramLogin, logout as apiLogout, setAuthToken, getAuthToken } from '../api/client';

export interface TelegramAuthData {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  showAuthModal: boolean;
  login: (data: TelegramAuthData) => Promise<void>;
  logout: () => void;
  openAuthModal: () => void;
  closeAuthModal: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getAuthToken();
      if (token) {
        try {
          const currentUser = await getCurrentUser();
          setUser(currentUser);
        } catch {
          // Token is invalid, clear it
          setAuthToken(null);
        }
      }
      setIsLoading(false);
    };
    checkAuth();
  }, []);

  const login = useCallback(async (data: TelegramAuthData) => {
    setIsLoading(true);
    try {
      const response = await telegramLogin(data);
      setUser(response.user);
      setShowAuthModal(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    apiLogout();
    setUser(null);
  }, []);

  const openAuthModal = useCallback(() => {
    setShowAuthModal(true);
  }, []);

  const closeAuthModal = useCallback(() => {
    setShowAuthModal(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        showAuthModal,
        login,
        logout,
        openAuthModal,
        closeAuthModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Telegram Login Widget integration
declare global {
  interface Window {
    TelegramLoginWidget?: {
      dataOnauth: (user: TelegramAuthData) => void;
    };
  }
}

export function useTelegramLogin(onSuccess: (data: TelegramAuthData) => void) {
  useEffect(() => {
    // This is called by the Telegram widget when auth completes
    window.TelegramLoginWidget = {
      dataOnauth: onSuccess,
    };

    return () => {
      delete window.TelegramLoginWidget;
    };
  }, [onSuccess]);
}

