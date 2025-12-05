import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AdminAuthProvider, useAdminAuth } from './useAdminAuth';
import React from 'react';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

function wrapper({ children }: { children: React.ReactNode }) {
  return <AdminAuthProvider>{children}</AdminAuthProvider>;
}

describe('useAdminAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: not authenticated
    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
    });
  });

  it('should start with loading state', () => {
    const { result } = renderHook(() => useAdminAuth(), { wrapper });
    expect(result.current.isLoading).toBe(true);
  });

  it('should check session on mount', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    const { result } = renderHook(() => useAdminAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/admin/me',
      expect.objectContaining({ credentials: 'include' })
    );
  });

  it('should be authenticated if session check succeeds', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ authenticated: true }),
    });

    const { result } = renderHook(() => useAdminAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAdminAuthenticated).toBe(true);
  });

  it('should login successfully', async () => {
    // First call for session check (not authenticated)
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    const { result } = renderHook(() => useAdminAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Mock login success
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });

    let success: boolean = false;
    await act(async () => {
      success = await result.current.adminLogin('admin', 'password');
    });

    expect(success).toBe(true);
    expect(result.current.isAdminAuthenticated).toBe(true);
  });

  it('should handle login failure', async () => {
    // First call for session check
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    const { result } = renderHook(() => useAdminAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Mock login failure
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Invalid credentials' }),
    });

    let success: boolean = true;
    await act(async () => {
      success = await result.current.adminLogin('wrong', 'wrong');
    });

    expect(success).toBe(false);
    expect(result.current.isAdminAuthenticated).toBe(false);
    expect(result.current.error).toBe('Invalid credentials');
  });

  it('should logout successfully', async () => {
    // Start authenticated
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ authenticated: true }),
    });

    const { result } = renderHook(() => useAdminAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isAdminAuthenticated).toBe(true);
    });

    // Mock logout
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });

    await act(async () => {
      await result.current.adminLogout();
    });

    expect(result.current.isAdminAuthenticated).toBe(false);
  });

  it('should throw error when used outside provider', () => {
    // This should throw
    expect(() => {
      renderHook(() => useAdminAuth());
    }).toThrow('useAdminAuth must be used within an AdminAuthProvider');
  });
});

