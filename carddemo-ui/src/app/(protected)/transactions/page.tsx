'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Transaction, PaginatedResponse } from '@/lib/types';

export default function TransactionsPage() {
  const [items, setItems] = useState<Transaction[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [acctIdFilter, setAcctIdFilter] = useState('');
  const [cardNumFilter, setCardNumFilter] = useState('');
  const [typeCdFilter, setTypeCdFilter] = useState('');

  const fetchData = useCallback(async (p: number) => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.set('page', p.toString());
      params.set('page_size', '10');
      if (acctIdFilter) params.set('acct_id', acctIdFilter);
      if (cardNumFilter) params.set('card_num', cardNumFilter);
      if (typeCdFilter) params.set('tran_type_cd', typeCdFilter);
      const data = await api.get<PaginatedResponse<Transaction>>(`/api/transactions?${params}`);
      setItems(data.items);
      setTotal(data.total);
      setHasMore(data.has_more);
      setPage(data.page);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [acctIdFilter, cardNumFilter, typeCdFilter]);

  useEffect(() => { fetchData(1); }, [fetchData]);

  const handleSearch = (e: React.FormEvent) => { e.preventDefault(); fetchData(1); };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Transactions</h1>
        <Link href="/transactions/new" className="bg-slate-800 text-white px-4 py-2 rounded text-sm hover:bg-slate-700">Add Transaction</Link>
      </div>
      <form onSubmit={handleSearch} className="flex gap-3 mb-6 flex-wrap">
        <input type="text" value={acctIdFilter} onChange={(e) => setAcctIdFilter(e.target.value)} placeholder="Account ID" className="border border-slate-300 rounded px-3 py-2 text-sm w-40" />
        <input type="text" value={cardNumFilter} onChange={(e) => setCardNumFilter(e.target.value)} placeholder="Card Number" className="border border-slate-300 rounded px-3 py-2 text-sm w-48" />
        <input type="text" value={typeCdFilter} onChange={(e) => setTypeCdFilter(e.target.value)} placeholder="Type Code" className="border border-slate-300 rounded px-3 py-2 text-sm w-32" />
        <button type="submit" className="bg-slate-800 text-white px-4 py-2 rounded text-sm hover:bg-slate-700">Search</button>
      </form>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      {loading ? (
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto mt-8" />
      ) : (
        <>
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">ID</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Type</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Description</th>
                  <th className="text-right px-4 py-3 font-medium text-slate-600">Amount</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Card</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Date</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {items.map((t) => (
                  <tr key={t.tran_id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono text-xs">{t.tran_id}</td>
                    <td className="px-4 py-3">{t.type_cd || '-'}</td>
                    <td className="px-4 py-3">{t.description || '-'}</td>
                    <td className="px-4 py-3 text-right font-medium">${Number(t.amount || 0).toFixed(2)}</td>
                    <td className="px-4 py-3 font-mono text-xs">{t.card_num}</td>
                    <td className="px-4 py-3 text-xs">{t.orig_ts || '-'}</td>
                    <td className="px-4 py-3">
                      <Link href={`/transactions/${t.tran_id}`} className="text-blue-600 hover:underline text-sm">View</Link>
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500">No transactions found</td></tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between mt-4 text-sm">
            <span className="text-slate-500">Total: {total}</span>
            <div className="flex gap-2">
              <button onClick={() => fetchData(page - 1)} disabled={page <= 1} className="px-3 py-1 border border-slate-300 rounded disabled:opacity-30 hover:bg-slate-50">Prev</button>
              <span className="px-3 py-1">Page {page}</span>
              <button onClick={() => fetchData(page + 1)} disabled={!hasMore} className="px-3 py-1 border border-slate-300 rounded disabled:opacity-30 hover:bg-slate-50">Next</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
