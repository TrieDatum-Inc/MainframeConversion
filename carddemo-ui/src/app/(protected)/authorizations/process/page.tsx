'use client';

import { useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { AuthorizationResponse } from '@/lib/types';

export default function AuthProcessPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<AuthorizationResponse | null>(null);
  const [form, setForm] = useState({
    card_num: '',
    auth_date: '',
    auth_time: '',
    auth_type: '',
    card_expiry_date: '',
    message_type: '',
    message_source: '',
    processing_code: '',
    transaction_amt: '',
    merchant_category_code: '',
    acqr_country_code: '',
    pos_entry_mode: '',
    merchant_id: '',
    merchant_name: '',
    merchant_city: '',
    merchant_state: '',
    merchant_zip: '',
    transaction_id: '',
  });

  const handleChange = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const payload: Record<string, unknown> = {
        card_num: form.card_num,
        auth_date: form.auth_date,
        auth_time: form.auth_time,
        auth_type: form.auth_type,
        card_expiry_date: form.card_expiry_date,
        message_type: form.message_type,
        message_source: form.message_source,
        processing_code: form.processing_code,
        transaction_amt: Number(form.transaction_amt),
      };
      if (form.merchant_category_code) payload.merchant_category_code = form.merchant_category_code;
      if (form.acqr_country_code) payload.acqr_country_code = form.acqr_country_code;
      if (form.pos_entry_mode) payload.pos_entry_mode = form.pos_entry_mode;
      if (form.merchant_id) payload.merchant_id = form.merchant_id;
      if (form.merchant_name) payload.merchant_name = form.merchant_name;
      if (form.merchant_city) payload.merchant_city = form.merchant_city;
      if (form.merchant_state) payload.merchant_state = form.merchant_state;
      if (form.merchant_zip) payload.merchant_zip = form.merchant_zip;
      if (form.transaction_id) payload.transaction_id = form.transaction_id;

      const res = await api.post<AuthorizationResponse>('/api/authorizations/process', payload);
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authorization failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Process Authorization</h1>
        <Link href="/authorizations/accounts/0" className="text-sm text-blue-600 hover:underline">View Pending Auths</Link>
      </div>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      {result && (
        <div className={`border px-4 py-3 rounded text-sm mb-4 ${result.auth_resp_code === '00' ? 'bg-green-50 border-green-200 text-green-700' : 'bg-amber-50 border-amber-200 text-amber-700'}`}>
          <p className="font-medium">Response: {result.auth_resp_reason}</p>
          <p>Card: {result.card_num} | Auth Code: {result.auth_id_code} | Resp Code: {result.auth_resp_code}</p>
          <p>Approved Amount: ${Number(result.approved_amt).toFixed(2)}</p>
          {result.transaction_id && <p>Transaction ID: {result.transaction_id}</p>}
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Card Number *</label><input type="text" value={form.card_num} onChange={(e) => handleChange('card_num', e.target.value)} required maxLength={16} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Transaction Amount *</label><input type="number" step="0.01" value={form.transaction_amt} onChange={(e) => handleChange('transaction_amt', e.target.value)} required min={0.01} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Auth Date *</label><input type="text" value={form.auth_date} onChange={(e) => handleChange('auth_date', e.target.value)} required maxLength={10} placeholder="YYYY-MM-DD" className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Auth Time *</label><input type="text" value={form.auth_time} onChange={(e) => handleChange('auth_time', e.target.value)} required maxLength={10} placeholder="HH:MM:SS" className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Auth Type *</label><input type="text" value={form.auth_type} onChange={(e) => handleChange('auth_type', e.target.value)} required maxLength={2} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Card Expiry *</label><input type="text" value={form.card_expiry_date} onChange={(e) => handleChange('card_expiry_date', e.target.value)} required maxLength={4} placeholder="MMYY" className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Message Type *</label><input type="text" value={form.message_type} onChange={(e) => handleChange('message_type', e.target.value)} required maxLength={4} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Message Source *</label><input type="text" value={form.message_source} onChange={(e) => handleChange('message_source', e.target.value)} required maxLength={10} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Processing Code *</label><input type="text" value={form.processing_code} onChange={(e) => handleChange('processing_code', e.target.value)} required maxLength={2} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Merchant Category</label><input type="text" value={form.merchant_category_code} onChange={(e) => handleChange('merchant_category_code', e.target.value)} maxLength={4} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Acquirer Country</label><input type="text" value={form.acqr_country_code} onChange={(e) => handleChange('acqr_country_code', e.target.value)} maxLength={3} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">POS Entry Mode</label><input type="text" value={form.pos_entry_mode} onChange={(e) => handleChange('pos_entry_mode', e.target.value)} maxLength={3} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Merchant ID</label><input type="text" value={form.merchant_id} onChange={(e) => handleChange('merchant_id', e.target.value)} maxLength={15} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Merchant Name</label><input type="text" value={form.merchant_name} onChange={(e) => handleChange('merchant_name', e.target.value)} maxLength={50} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Merchant City</label><input type="text" value={form.merchant_city} onChange={(e) => handleChange('merchant_city', e.target.value)} maxLength={50} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Merchant State</label><input type="text" value={form.merchant_state} onChange={(e) => handleChange('merchant_state', e.target.value)} maxLength={2} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Merchant ZIP</label><input type="text" value={form.merchant_zip} onChange={(e) => handleChange('merchant_zip', e.target.value)} maxLength={10} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          <div><label className="block text-sm font-medium text-slate-700 mb-1">Transaction ID</label><input type="text" value={form.transaction_id} onChange={(e) => handleChange('transaction_id', e.target.value)} maxLength={16} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
        </div>
        <button type="submit" disabled={loading} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700 disabled:opacity-50">
          {loading ? 'Processing...' : 'Process Authorization'}
        </button>
      </form>
    </div>
  );
}
