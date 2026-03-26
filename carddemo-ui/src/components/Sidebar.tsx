'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { isAdmin } from '@/lib/api';

const navItems = [
  { label: 'Dashboard', href: '/', icon: '&#9632;' },
  { label: 'Accounts', href: '/accounts', icon: '&#9632;' },
  { label: 'Cards', href: '/cards', icon: '&#9632;' },
  { label: 'Transactions', href: '/transactions', icon: '&#9632;' },
  { label: 'Bill Payment', href: '/bill-payment', icon: '&#9632;' },
  { label: 'Reports', href: '/reports', icon: '&#9632;' },
  { label: 'Authorizations', href: '/authorizations/process', icon: '&#9632;' },
];

const adminItems = [
  { label: 'User Management', href: '/admin/users', icon: '&#9632;' },
  { label: 'Transaction Types', href: '/admin/transaction-types', icon: '&#9632;' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [admin, setAdmin] = useState(false);

  useEffect(() => {
    setAdmin(isAdmin());
  }, []);

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <aside className="w-64 bg-slate-50 border-r border-slate-200 min-h-[calc(100vh-4rem)]">
      <nav className="p-4 space-y-1">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">
          Main
        </p>
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`block px-3 py-2 rounded text-sm transition-colors ${
              isActive(item.href)
                ? 'bg-slate-800 text-white'
                : 'text-slate-700 hover:bg-slate-200'
            }`}
          >
            {item.label}
          </Link>
        ))}
        {admin && (
          <>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 mt-6 mb-2">
              Admin
            </p>
            {adminItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`block px-3 py-2 rounded text-sm transition-colors ${
                  isActive(item.href)
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-700 hover:bg-slate-200'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </>
        )}
      </nav>
    </aside>
  );
}
