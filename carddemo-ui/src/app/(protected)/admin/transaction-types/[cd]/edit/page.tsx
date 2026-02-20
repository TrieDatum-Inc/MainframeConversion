'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { TransactionType } from '@/lib/types';
import ProtectedRoute from '@/components/ProtectedRoute';

function EditTypeContent() {
  const params = useParams();
  const router = useRouter();
  const typeCd = params.cd as string;
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState({ type_cd: '', type_description: '' });

  useEffect(() => {
    api.get<TransactionType>(`/api/transaction-types/${typeCd}`)
      .then((t) => setForm({ type_cd: t.type_cd, type_description: t.type_description || '' }))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [typeCd]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);
    try {
      await api.put<TransactionType>(`/api/transaction-types/${typeCd}`, form);
      setSuccess('Updated successfully');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto mt-8" />;

  return (
    <div className="max-w-lg">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Edit Transaction Type: {typeCd}</h1>
        <button onClick={() => router.back()} className="text-sm text-slate-600 hover:text-slate-800">Back</button>
      </div>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded text-sm mb-4">{success}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div><label className="block text-sm font-medium text-slate-700 mb-1">Type Code</label><input type="text" value={form.type_cd} disabled className="w-full border border-slate-300 rounded px-3 py-2 bg-slate-50" /></div>
        <div><label className="block text-sm font-medium text-slate-700 mb-1">Description *</label><input type="text" value={form.type_description} onChange={(e) => setForm({ ...form, type_description: e.target.value })} required maxLength={50} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700 disabled:opacity-50">{saving ? 'Saving...' : 'Save'}</button>
          <button type="button" onClick={() => router.back()} className="border border-slate-300 px-6 py-2 rounded hover:bg-slate-50">Cancel</button>
        </div>
      </form>
    </div>
  );
}

export default function EditTypePage() {
  return <ProtectedRoute adminOnly><EditTypeContent /></ProtectedRoute>;
}
