'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { TransactionType } from '@/lib/types';
import ProtectedRoute from '@/components/ProtectedRoute';

function CreateTypeContent() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ type_cd: '', type_description: '' });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await api.post<TransactionType>('/api/transaction-types', form);
      router.push('/admin/transaction-types');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Create failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-lg">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Create Transaction Type</h1>
        <button onClick={() => router.back()} className="text-sm text-slate-600 hover:text-slate-800">Back</button>
      </div>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div><label className="block text-sm font-medium text-slate-700 mb-1">Type Code *</label><input type="text" value={form.type_cd} onChange={(e) => setForm({ ...form, type_cd: e.target.value })} required maxLength={2} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div><label className="block text-sm font-medium text-slate-700 mb-1">Description *</label><input type="text" value={form.type_description} onChange={(e) => setForm({ ...form, type_description: e.target.value })} required maxLength={50} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700 disabled:opacity-50">{saving ? 'Creating...' : 'Create'}</button>
          <button type="button" onClick={() => router.back()} className="border border-slate-300 px-6 py-2 rounded hover:bg-slate-50">Cancel</button>
        </div>
      </form>
    </div>
  );
}

export default function CreateTypePage() {
  return <ProtectedRoute adminOnly><CreateTypeContent /></ProtectedRoute>;
}
