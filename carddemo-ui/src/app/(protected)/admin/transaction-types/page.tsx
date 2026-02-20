'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { TransactionType, PaginatedResponse, MessageResponse } from '@/lib/types';
import ProtectedRoute from '@/components/ProtectedRoute';

function TransactionTypesContent() {
  const [items, setItems] = useState<TransactionType[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [codeFilt, setCodeFilt] = useState('');
  const [descFilt, setDescFilt] = useState('');

  const fetchData = useCallback(async (p: number) => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.set('page', p.toString());
      params.set('page_size', '10');
      if (codeFilt) params.set('type_cd_filter', codeFilt);
      if (descFilt) params.set('type_desc_filter', descFilt);
      const data = await api.get<PaginatedResponse<TransactionType>>(`/api/transaction-types?${params}`);
      setItems(data.items);
      setTotal(data.total);
      setHasMore(data.has_more);
      setPage(data.page);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [codeFilt, descFilt]);

  useEffect(() => { fetchData(1); }, [fetchData]);

  const handleDelete = async (typeCd: string) => {
    if (!confirm(`Delete transaction type ${typeCd}?`)) return;
    try {
      await api.delete<MessageResponse>(`/api/transaction-types/${typeCd}`);
      fetchData(page);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Transaction Types</h1>
        <Link href="/admin/transaction-types/new" className="bg-slate-800 text-white px-4 py-2 rounded text-sm hover:bg-slate-700">Add Type</Link>
      </div>
      <form onSubmit={(e) => { e.preventDefault(); fetchData(1); }} className="flex gap-3 mb-6">
        <input type="text" value={codeFilt} onChange={(e) => setCodeFilt(e.target.value)} placeholder="Type Code" maxLength={2} className="border border-slate-300 rounded px-3 py-2 text-sm w-32" />
        <input type="text" value={descFilt} onChange={(e) => setDescFilt(e.target.value)} placeholder="Description" className="border border-slate-300 rounded px-3 py-2 text-sm w-48" />
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
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Code</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Description</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {items.map((t) => (
                  <tr key={t.type_cd} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono font-medium">{t.type_cd}</td>
                    <td className="px-4 py-3">{t.type_description || '-'}</td>
                    <td className="px-4 py-3 space-x-2">
                      <Link href={`/admin/transaction-types/${t.type_cd}/edit`} className="text-blue-600 hover:underline text-sm">Edit</Link>
                      <button onClick={() => handleDelete(t.type_cd)} className="text-red-600 hover:underline text-sm">Delete</button>
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr><td colSpan={3} className="px-4 py-8 text-center text-slate-500">No transaction types found</td></tr>
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

export default function TransactionTypesPage() {
  return <ProtectedRoute adminOnly><TransactionTypesContent /></ProtectedRoute>;
}
