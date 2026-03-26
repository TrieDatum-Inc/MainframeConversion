/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

import Navbar from '@/components/Navbar';

beforeEach(() => {
  localStorage.clear();
  mockPush.mockClear();
});

describe('Navbar', () => {
  it('renders CardDemo link', () => {
    render(<Navbar />);
    expect(screen.getByText('CardDemo')).toBeInTheDocument();
  });

  it('shows user info when logged in', () => {
    localStorage.setItem('user_id', 'ADMIN001');
    localStorage.setItem('user_type', 'A');
    render(<Navbar />);
    expect(screen.getByText(/ADMIN001/)).toBeInTheDocument();
    expect(screen.getByText(/Admin/)).toBeInTheDocument();
  });

  it('shows User label for non-admin', () => {
    localStorage.setItem('user_id', 'USER0001');
    localStorage.setItem('user_type', 'U');
    render(<Navbar />);
    expect(screen.getByText(/User/)).toBeInTheDocument();
  });

  it('sign out clears token and redirects', () => {
    localStorage.setItem('user_id', 'ADMIN001');
    localStorage.setItem('user_type', 'A');
    localStorage.setItem('access_token', 'tok');
    render(<Navbar />);
    fireEvent.click(screen.getByText('Sign Out'));
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(mockPush).toHaveBeenCalledWith('/login');
  });

  it('does not show sign out when not logged in', () => {
    render(<Navbar />);
    expect(screen.queryByText('Sign Out')).not.toBeInTheDocument();
  });
});
