'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { BillPaymentResponse } from '@/lib/types';

export default function BillPaymentPage() {
  const [acctId, setAcctId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<BillPaymentResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const res = await api.post<BillPaymentResponse>('/api/bill-payments', {
        acct_id: Number(acctId),
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Bill Payment</h1>
      <p className="text-sm text-slate-500 mb-4">Pay the full current balance on an account.</p>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      {result && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded text-sm mb-4">
          <p className="font-medium">{result.message}</p>
          <p>Account: {result.acct_id}</p>
          <p>Payment: ${Number(result.payment_amount).toFixed(2)}</p>
          <p>New Balance: ${Number(result.new_balance).toFixed(2)}</p>
          <p>Transaction ID: {result.tran_id}</p>
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Account ID</label>
          <input
            type="number"
            value={acctId}
            onChange={(e) => setAcctId(e.target.value)}
            required
            min={1}
            className="w-full border border-slate-300 rounded px-3 py-2"
            placeholder="e.g. 10000000001"
          />
        </div>
        <button type="submit" disabled={loading} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700 disabled:opacity-50">
          {loading ? 'Processing...' : 'Pay Full Balance'}
        </button>
      </form>
    </div>
  );
}
