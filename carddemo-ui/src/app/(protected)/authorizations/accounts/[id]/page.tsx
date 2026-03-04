'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { PendingAuthSummary, PendingAuthDetail } from '@/lib/types';

export default function AuthSummaryPage() {
  const params = useParams();
  const router = useRouter();
  const initialAcctId = params.id as string;
  const [acctId, setAcctId] = useState(initialAcctId === '0' ? '' : initialAcctId);
  const [data, setData] = useState<PendingAuthSummary | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async (p: number, id?: string) => {
    const lookupId = id || acctId;
    if (!lookupId || lookupId === '0') return;
    setLoading(true);
    setError('');
    try {
      const res = await api.get<PendingAuthSummary>(`/api/authorizations/accounts/${lookupId}?page=${p}&page_size=5`);
      setData(res);
      setPage(res.page);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialAcctId && initialAcctId !== '0') fetchData(1, initialAcctId);
  }, [initialAcctId]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (acctId) {
      router.push(`/authorizations/accounts/${acctId}`);
      fetchData(1);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Pending Authorization Summary</h1>
      <form onSubmit={handleSearch} className="flex gap-3 mb-6">
        <input type="number" value={acctId} onChange={(e) => setAcctId(e.target.value)} placeholder="Account ID" required min={1} className="border border-slate-300 rounded px-3 py-2 text-sm w-48" />
        <button type="submit" className="bg-slate-800 text-white px-4 py-2 rounded text-sm hover:bg-slate-700">Search</button>
      </form>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      {loading && <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto mt-8" />}

      {data && !loading && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-500">Account</p>
              <p className="text-lg font-bold">{data.acct_id}</p>
            </div>
            <div className="border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-500">Customer</p>
              <p className="text-lg font-bold">{data.customer_name || '-'}</p>
            </div>
            <div className="border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-500">Credit Limit</p>
              <p className="text-lg font-bold">${Number(data.credit_limit || 0).toFixed(2)}</p>
            </div>
            <div className="border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-500">Credit Balance</p>
              <p className="text-lg font-bold">${Number(data.credit_balance || 0).toFixed(2)}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="border border-green-200 bg-green-50 rounded-lg p-4">
              <p className="text-xs text-green-600">Approved Count</p>
              <p className="text-lg font-bold text-green-700">{data.approved_count}</p>
            </div>
            <div className="border border-green-200 bg-green-50 rounded-lg p-4">
              <p className="text-xs text-green-600">Approved Amount</p>
              <p className="text-lg font-bold text-green-700">${Number(data.approved_amount || 0).toFixed(2)}</p>
            </div>
            <div className="border border-red-200 bg-red-50 rounded-lg p-4">
              <p className="text-xs text-red-600">Declined Count</p>
              <p className="text-lg font-bold text-red-700">{data.declined_count}</p>
            </div>
            <div className="border border-red-200 bg-red-50 rounded-lg p-4">
              <p className="text-xs text-red-600">Declined Amount</p>
              <p className="text-lg font-bold text-red-700">${Number(data.declined_amount || 0).toFixed(2)}</p>
            </div>
          </div>

          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">ID</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Card</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Date</th>
                  <th className="text-right px-4 py-3 font-medium text-slate-600">Amount</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Response</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Fraud</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {data.authorizations.map((a: PendingAuthDetail) => (
                  <tr key={a.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">{a.id}</td>
                    <td className="px-4 py-3 font-mono text-xs">{a.card_num}</td>
                    <td className="px-4 py-3 text-xs">{a.auth_date || '-'}</td>
                    <td className="px-4 py-3 text-right">${Number(a.transaction_amt || 0).toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${a.auth_resp_code === '00' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {a.auth_resp_reason || a.auth_resp_code || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${a.fraud_confirmed === 'Y' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'}`}>
                        {a.fraud_confirmed === 'Y' ? 'Fraud' : 'No'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/authorizations/${a.id}`} className="text-blue-600 hover:underline text-sm">Detail</Link>
                    </td>
                  </tr>
                ))}
                {data.authorizations.length === 0 && (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500">No pending authorizations</td></tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button onClick={() => fetchData(page - 1)} disabled={page <= 1} className="px-3 py-1 border border-slate-300 rounded text-sm disabled:opacity-30 hover:bg-slate-50">Prev</button>
            <span className="px-3 py-1 text-sm">Page {page}</span>
            <button onClick={() => fetchData(page + 1)} disabled={!data.has_more} className="px-3 py-1 border border-slate-300 rounded text-sm disabled:opacity-30 hover:bg-slate-50">Next</button>
          </div>
        </>
      )}
    </div>
  );
}
