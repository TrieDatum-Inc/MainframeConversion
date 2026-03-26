'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Transaction } from '@/lib/types';

export default function AddTransactionPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState({
    type_cd: '',
    cat_cd: '',
    source: '',
    description: '',
    amount: '',
    card_num: '',
    acct_id: '',
    merchant_id: '',
    merchant_name: '',
    merchant_city: '',
    merchant_zip: '',
  });

  const handleChange = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        type_cd: form.type_cd,
        cat_cd: Number(form.cat_cd),
        source: form.source,
        description: form.description,
        amount: Number(form.amount),
        card_num: form.card_num,
        acct_id: Number(form.acct_id),
      };
      if (form.merchant_id) payload.merchant_id = Number(form.merchant_id);
      if (form.merchant_name) payload.merchant_name = form.merchant_name;
      if (form.merchant_city) payload.merchant_city = form.merchant_city;
      if (form.merchant_zip) payload.merchant_zip = form.merchant_zip;

      const result = await api.post<Transaction>('/api/transactions', payload);
      setSuccess(`Transaction ${result.tran_id} created successfully`);
      setForm({ type_cd: '', cat_cd: '', source: '', description: '', amount: '', card_num: '', acct_id: '', merchant_id: '', merchant_name: '', merchant_city: '', merchant_zip: '' });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Add Transaction</h1>
        <button onClick={() => router.back()} className="text-sm text-slate-600 hover:text-slate-800">Back</button>
      </div>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded text-sm mb-4">{success}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Account ID *</label><input type="number" value={form.acct_id} onChange={(e) => handleChange('acct_id', e.target.value)} required className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Card Number *</label><input type="text" value={form.card_num} onChange={(e) => handleChange('card_num', e.target.value)} required maxLength={16} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Type Code *</label><input type="text" value={form.type_cd} onChange={(e) => handleChange('type_cd', e.target.value)} required maxLength={2} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Category Code *</label><input type="number" value={form.cat_cd} onChange={(e) => handleChange('cat_cd', e.target.value)} required min={0} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Source *</label><input type="text" value={form.source} onChange={(e) => handleChange('source', e.target.value)} required maxLength={10} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Amount *</label><input type="number" step="0.01" value={form.amount} onChange={(e) => handleChange('amount', e.target.value)} required min={0.01} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        </div>
        <div><label className="block text-sm font-medium text-slate-700 mb-1">Description *</label><input type="text" value={form.description} onChange={(e) => handleChange('description', e.target.value)} required maxLength={100} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Merchant ID</label><input type="number" value={form.merchant_id} onChange={(e) => handleChange('merchant_id', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Merchant Name</label><input type="text" value={form.merchant_name} onChange={(e) => handleChange('merchant_name', e.target.value)} maxLength={50} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Merchant City</label><input type="text" value={form.merchant_city} onChange={(e) => handleChange('merchant_city', e.target.value)} maxLength={50} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Merchant ZIP</label><input type="text" value={form.merchant_zip} onChange={(e) => handleChange('merchant_zip', e.target.value)} maxLength={10} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        </div>
        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700 disabled:opacity-50">
            {saving ? 'Creating...' : 'Create Transaction'}
          </button>
          <button type="button" onClick={() => router.back()} className="border border-slate-300 px-6 py-2 rounded hover:bg-slate-50">Cancel</button>
        </div>
      </form>
    </div>
  );
}
