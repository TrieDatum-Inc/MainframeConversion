'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function AccountsPage() {
  const router = useRouter();
  const [acctId, setAcctId] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!acctId.trim()) {
      setError('Please enter an Account ID');
      return;
    }
    router.push(`/accounts/${acctId.trim()}`);
  };

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Account Lookup</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">{error}</div>
        )}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Account ID</label>
          <input
            type="text"
            value={acctId}
            onChange={(e) => setAcctId(e.target.value)}
            className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-500"
            placeholder="e.g. 10000000001"
          />
        </div>
        <button type="submit" className="bg-slate-800 text-white px-4 py-2 rounded hover:bg-slate-700 transition-colors">
          View Account
        </button>
      </form>
    </div>
  );
}
