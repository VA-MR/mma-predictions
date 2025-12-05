import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from '../test/test-utils';
import { AdminLoginPage } from './AdminLoginPage';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('AdminLoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: session check fails (not logged in)
    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
    });
  });

  it('should render login form', async () => {
    render(<AdminLoginPage />);

    await waitFor(() => {
      expect(screen.getByText('Admin Panel')).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('should show error for empty fields', async () => {
    render(<AdminLoginPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/please enter both/i)).toBeInTheDocument();
    });
  });

  it('should submit login form', async () => {
    const user = userEvent.setup();

    // First: session check
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    render(<AdminLoginPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    });

    // Mock successful login
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });

    await user.type(screen.getByLabelText(/username/i), 'admin');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/admin/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ username: 'admin', password: 'password123' }),
        })
      );
    });
  });

  it('should navigate to admin on successful login', async () => {
    const user = userEvent.setup();

    // Session check
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    render(<AdminLoginPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    });

    // Successful login
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });

    await user.type(screen.getByLabelText(/username/i), 'admin');
    await user.type(screen.getByLabelText(/password/i), 'password');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/admin');
    });
  });

  it('should show error on failed login', async () => {
    const user = userEvent.setup();

    // Session check
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    render(<AdminLoginPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    });

    // Failed login
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Invalid username or password' }),
    });

    await user.type(screen.getByLabelText(/username/i), 'wrong');
    await user.type(screen.getByLabelText(/password/i), 'wrong');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument();
    });
  });

  it('should have back link to main site', async () => {
    render(<AdminLoginPage />);

    await waitFor(() => {
      expect(screen.getByText(/back to main site/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/back to main site/i).closest('a')).toHaveAttribute('href', '/');
  });
});

