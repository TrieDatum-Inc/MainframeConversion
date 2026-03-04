'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { User } from '@/lib/types';
import ProtectedRoute from '@/components/ProtectedRoute';

function CreateUserContent() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    user_id: '',
    first_name: '',
    last_name: '',
    password: '',
    user_type: 'U',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await api.post<User>('/api/users', form);
      router.push('/admin/users');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Create failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-lg">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Create User</h1>
        <button onClick={() => router.back()} className="text-sm text-slate-600 hover:text-slate-800">Back</button>
      </div>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div><label className="block text-sm font-medium text-slate-700 mb-1">User ID *</label><input type="text" value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })} required maxLength={8} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div><label className="block text-sm font-medium text-slate-700 mb-1">First Name *</label><input type="text" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required maxLength={20} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div><label className="block text-sm font-medium text-slate-700 mb-1">Last Name *</label><input type="text" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required maxLength={20} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div><label className="block text-sm font-medium text-slate-700 mb-1">Password *</label><input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required maxLength={8} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">User Type *</label>
          <select value={form.user_type} onChange={(e) => setForm({ ...form, user_type: e.target.value })} className="w-full border border-slate-300 rounded px-3 py-2">
            <option value="U">Regular User</option>
            <option value="A">Admin</option>
          </select>
        </div>
        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700 disabled:opacity-50">
            {saving ? 'Creating...' : 'Create User'}
          </button>
          <button type="button" onClick={() => router.back()} className="border border-slate-300 px-6 py-2 rounded hover:bg-slate-50">Cancel</button>
        </div>
      </form>
    </div>
  );
}

export default function CreateUserPage() {
  return <ProtectedRoute adminOnly><CreateUserContent /></ProtectedRoute>;
}
