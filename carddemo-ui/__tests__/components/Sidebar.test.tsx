/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

jest.mock('next/navigation', () => ({
  usePathname: () => '/',
}));

import Sidebar from '@/components/Sidebar';

beforeEach(() => {
  localStorage.clear();
});

describe('Sidebar', () => {
  it('renders main nav items', () => {
    render(<Sidebar />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Accounts')).toBeInTheDocument();
    expect(screen.getByText('Cards')).toBeInTheDocument();
    expect(screen.getByText('Transactions')).toBeInTheDocument();
    expect(screen.getByText('Bill Payment')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
    expect(screen.getByText('Authorizations')).toBeInTheDocument();
  });

  it('does not show admin items for regular user', () => {
    localStorage.setItem('user_type', 'U');
    render(<Sidebar />);
    expect(screen.queryByText('User Management')).not.toBeInTheDocument();
    expect(screen.queryByText('Transaction Types')).not.toBeInTheDocument();
  });

  it('shows admin items for admin user', () => {
    localStorage.setItem('user_type', 'A');
    render(<Sidebar />);
    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('Transaction Types')).toBeInTheDocument();
  });

  it('renders correct links', () => {
    render(<Sidebar />);
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink).toHaveAttribute('href', '/');
    const accountsLink = screen.getByText('Accounts').closest('a');
    expect(accountsLink).toHaveAttribute('href', '/accounts');
  });
});
