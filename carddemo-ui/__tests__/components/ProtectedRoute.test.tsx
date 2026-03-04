/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

import ProtectedRoute from '@/components/ProtectedRoute';

beforeEach(() => {
  localStorage.clear();
  mockPush.mockClear();
});

describe('ProtectedRoute', () => {
  it('redirects to login when not authenticated', () => {
    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );
    expect(mockPush).toHaveBeenCalledWith('/login');
  });

  it('renders children when authenticated', async () => {
    localStorage.setItem('user_id', 'USER0001');
    localStorage.setItem('user_type', 'U');
    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );
    expect(await screen.findByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects non-admin from admin-only route', () => {
    localStorage.setItem('user_id', 'USER0001');
    localStorage.setItem('user_type', 'U');
    render(
      <ProtectedRoute adminOnly>
        <div>Admin Content</div>
      </ProtectedRoute>
    );
    expect(mockPush).toHaveBeenCalledWith('/');
  });

  it('allows admin to access admin-only route', async () => {
    localStorage.setItem('user_id', 'ADMIN001');
    localStorage.setItem('user_type', 'A');
    render(
      <ProtectedRoute adminOnly>
        <div>Admin Content</div>
      </ProtectedRoute>
    );
    expect(await screen.findByText('Admin Content')).toBeInTheDocument();
  });
});
