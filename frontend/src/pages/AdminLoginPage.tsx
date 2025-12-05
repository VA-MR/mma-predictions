import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAdminAuth } from '../hooks/useAdminAuth';
import './AdminLoginPage.css';

export function AdminLoginPage() {
  const navigate = useNavigate();
  const { adminLogin, isLoading, error } = useAdminAuth();
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    
    if (!username.trim() || !password.trim()) {
      setLocalError('Please enter both username and password');
      return;
    }
    
    const success = await adminLogin(username, password);
    if (success) {
      navigate('/admin');
    }
  };

  return (
    <div className="admin-login-container">
      <div className="admin-login-card">
        <div className="admin-login-header">
          <div className="admin-logo">🥊</div>
          <h1>Admin Panel</h1>
          <p>MMA Scoring System</p>
        </div>
        
        <form className="admin-login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              autoComplete="username"
              autoFocus
              disabled={isLoading}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              autoComplete="current-password"
              disabled={isLoading}
            />
          </div>
          
          {(localError || error) && (
            <div className="error-message">
              {localError || error}
            </div>
          )}
          
          <button 
            type="submit" 
            className="login-button"
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="admin-login-footer">
          <a href="/" className="back-link">← Back to main site</a>
        </div>
      </div>
    </div>
  );
}

