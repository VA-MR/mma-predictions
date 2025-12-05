import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface AdminAuthContextType {
  isAdminAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  checkAdminSession: () => Promise<boolean>;
  adminLogin: (username: string, password: string) => Promise<boolean>;
  adminLogout: () => Promise<void>;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

const API_BASE = '/api';

export function AdminAuthProvider({ children }: { children: React.ReactNode }) {
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkAdminSession = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/admin/me`, {
        credentials: 'include', // Include cookies
      });
      
      if (response.ok) {
        setIsAdminAuthenticated(true);
        return true;
      } else {
        setIsAdminAuthenticated(false);
        return false;
      }
    } catch {
      setIsAdminAuthenticated(false);
      return false;
    }
  }, []);

  const adminLogin = useCallback(async (username: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/admin/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies
        body: JSON.stringify({ username, password }),
      });
      
      if (response.ok) {
        setIsAdminAuthenticated(true);
        setIsLoading(false);
        return true;
      } else {
        const data = await response.json().catch(() => ({ detail: 'Login failed' }));
        setError(data.detail || 'Invalid username or password');
        setIsAdminAuthenticated(false);
        setIsLoading(false);
        return false;
      }
    } catch (err) {
      setError('Network error. Please try again.');
      setIsAdminAuthenticated(false);
      setIsLoading(false);
      return false;
    }
  }, []);

  const adminLogout = useCallback(async (): Promise<void> => {
    try {
      await fetch(`${API_BASE}/admin/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch {
      // Ignore errors during logout
    }
    setIsAdminAuthenticated(false);
  }, []);

  // Check session on mount
  useEffect(() => {
    const init = async () => {
      await checkAdminSession();
      setIsLoading(false);
    };
    init();
  }, [checkAdminSession]);

  return (
    <AdminAuthContext.Provider
      value={{
        isAdminAuthenticated,
        isLoading,
        error,
        checkAdminSession,
        adminLogin,
        adminLogout,
      }}
    >
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error('useAdminAuth must be used within an AdminAuthProvider');
  }
  return context;
}

