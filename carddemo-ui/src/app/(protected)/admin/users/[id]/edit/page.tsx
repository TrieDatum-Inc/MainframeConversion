'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { User } from '@/lib/types';
import ProtectedRoute from '@/components/ProtectedRoute';

function EditUserContent() {
  const params = useParams();
  const router = useRouter();
  const userId = params.id as string;
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState({
    user_id: '',
    first_name: '',
    last_name: '',
    password: '',
    user_type: 'U',
  });

  useEffect(() => {
    api.get<User>(`/api/users/${userId}`)
      .then((u) => {
        setForm({
          user_id: u.user_id,
          first_name: u.first_name || '',
          last_name: u.last_name || '',
          password: '',
          user_type: u.user_type,
        });
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);
    try {
      const payload: Record<string, string> = { user_id: form.user_id };
      if (form.first_name) payload.first_name = form.first_name;
      if (form.last_name) payload.last_name = form.last_name;
      if (form.password) payload.password = form.password;
      if (form.user_type) payload.user_type = form.user_type;
      await api.put<User>(`/api/users/${userId}`, payload);
      setSuccess('User updated successfully');
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
        <h1 className="text-2xl font-bold">Edit User: {userId}</h1>
        <button onClick={() => router.back()} className="text-sm text-slate-600 hover:text-slate-800">Back</button>
      </div>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded text-sm mb-4">{success}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div><label className="block text-sm font-medium text-slate-700 mb-1">First Name</label><input type="text" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} maxLength={20} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div><label className="block text-sm font-medium text-slate-700 mb-1">Last Name</label><input type="text" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} maxLength={20} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div><label className="block text-sm font-medium text-slate-700 mb-1">New Password (leave blank to keep)</label><input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} maxLength={8} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">User Type</label>
          <select value={form.user_type} onChange={(e) => setForm({ ...form, user_type: e.target.value })} className="w-full border border-slate-300 rounded px-3 py-2">
            <option value="U">Regular User</option>
            <option value="A">Admin</option>
          </select>
        </div>
        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700 disabled:opacity-50">
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button type="button" onClick={() => router.back()} className="border border-slate-300 px-6 py-2 rounded hover:bg-slate-50">Cancel</button>
        </div>
      </form>
    </div>
  );
}

export default function EditUserPage() {
  return <ProtectedRoute adminOnly><EditUserContent /></ProtectedRoute>;
}
