'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { isAdmin } from '@/lib/api';

const menuItems = [
  { title: 'Account View', desc: 'View account details and customer information', href: '/accounts', color: 'bg-blue-600' },
  { title: 'Card Management', desc: 'List, view and update credit cards', href: '/cards', color: 'bg-indigo-600' },
  { title: 'Transactions', desc: 'View, search and add transactions', href: '/transactions', color: 'bg-purple-600' },
  { title: 'Bill Payment', desc: 'Pay account balance in full', href: '/bill-payment', color: 'bg-green-600' },
  { title: 'Reports', desc: 'Submit transaction report requests', href: '/reports', color: 'bg-amber-600' },
  { title: 'Authorizations', desc: 'Process and view pending authorizations', href: '/authorizations/process', color: 'bg-red-600' },
];

const adminItems = [
  { title: 'User Management', desc: 'Create, update and delete users', href: '/admin/users', color: 'bg-slate-700' },
  { title: 'Transaction Types', desc: 'Manage transaction type codes', href: '/admin/transaction-types', color: 'bg-slate-600' },
];

export default function DashboardPage() {
  const [admin, setAdmin] = useState(false);

  useEffect(() => {
    setAdmin(isAdmin());
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {menuItems.map((item) => (
          <Link key={item.href} href={item.href}>
            <div className="border border-slate-200 rounded-lg p-5 hover:shadow-md transition-shadow cursor-pointer">
              <div className={`w-10 h-10 ${item.color} rounded-lg mb-3`} />
              <h2 className="text-lg font-semibold">{item.title}</h2>
              <p className="text-sm text-slate-500 mt-1">{item.desc}</p>
            </div>
          </Link>
        ))}
      </div>
      {admin && (
        <>
          <h2 className="text-xl font-bold mt-8 mb-4">Administration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {adminItems.map((item) => (
              <Link key={item.href} href={item.href}>
                <div className="border border-slate-200 rounded-lg p-5 hover:shadow-md transition-shadow cursor-pointer">
                  <div className={`w-10 h-10 ${item.color} rounded-lg mb-3`} />
                  <h2 className="text-lg font-semibold">{item.title}</h2>
                  <p className="text-sm text-slate-500 mt-1">{item.desc}</p>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
