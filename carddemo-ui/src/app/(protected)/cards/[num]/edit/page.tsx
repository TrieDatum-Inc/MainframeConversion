'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { CardDetail } from '@/lib/types';

export default function CardEditPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const cardNum = params.num as string;
  const acctId = searchParams.get('acct_id') || '';
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState({
    embossed_name: '',
    active_status: '',
    expiration_date: '',
  });

  useEffect(() => {
    if (!acctId) { setError('Account ID required'); setLoading(false); return; }
    api.get<CardDetail>(`/api/cards/${cardNum}/${acctId}`)
      .then((data) => {
        setForm({
          embossed_name: data.card.embossed_name || '',
          active_status: data.card.active_status || 'Y',
          expiration_date: data.card.expiration_date || '',
        });
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [cardNum, acctId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);
    try {
      await api.put(`/api/cards/${cardNum}/${acctId}`, {
        acct_id: Number(acctId),
        card_num: cardNum,
        embossed_name: form.embossed_name || undefined,
        active_status: form.active_status || undefined,
        expiration_date: form.expiration_date || undefined,
      });
      setSuccess('Card updated successfully');
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
        <h1 className="text-2xl font-bold">Edit Card</h1>
        <button onClick={() => router.back()} className="text-sm text-slate-600 hover:text-slate-800">Back</button>
      </div>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded text-sm mb-4">{success}</div>}

      <div className="text-sm text-slate-500 mb-4">
        Card: <span className="font-mono">{cardNum}</span> | Account: {acctId}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Embossed Name</label>
          <input type="text" value={form.embossed_name} onChange={(e) => setForm({ ...form, embossed_name: e.target.value })} maxLength={50} className="w-full border border-slate-300 rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Status</label>
          <select value={form.active_status} onChange={(e) => setForm({ ...form, active_status: e.target.value })} className="w-full border border-slate-300 rounded px-3 py-2">
            <option value="Y">Active</option>
            <option value="N">Inactive</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Expiration Date</label>
          <input type="text" value={form.expiration_date} onChange={(e) => setForm({ ...form, expiration_date: e.target.value })} className="w-full border border-slate-300 rounded px-3 py-2" placeholder="YYYY-MM-DD" />
        </div>
        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700 disabled:opacity-50">
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button type="button" onClick={() => router.back()} className="border border-slate-300 px-6 py-2 rounded hover:bg-slate-50">Cancel</button>
        </div>
      </form>
    </div>
  );
}
