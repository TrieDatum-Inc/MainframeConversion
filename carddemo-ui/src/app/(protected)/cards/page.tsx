'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Card, PaginatedResponse } from '@/lib/types';

export default function CardsPage() {
  const [cards, setCards] = useState<Card[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [acctIdFilter, setAcctIdFilter] = useState('');
  const [cardNumFilter, setCardNumFilter] = useState('');

  const fetchCards = useCallback(async (p: number) => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.set('page', p.toString());
      params.set('page_size', '10');
      if (acctIdFilter) params.set('acct_id', acctIdFilter);
      if (cardNumFilter) params.set('card_num', cardNumFilter);
      const data = await api.get<PaginatedResponse<Card>>(`/api/cards?${params}`);
      setCards(data.items);
      setTotal(data.total);
      setHasMore(data.has_more);
      setPage(data.page);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load cards');
    } finally {
      setLoading(false);
    }
  }, [acctIdFilter, cardNumFilter]);

  useEffect(() => { fetchCards(1); }, [fetchCards]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchCards(1);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Credit Cards</h1>
      <form onSubmit={handleSearch} className="flex gap-3 mb-6">
        <input type="text" value={acctIdFilter} onChange={(e) => setAcctIdFilter(e.target.value)} placeholder="Account ID" className="border border-slate-300 rounded px-3 py-2 text-sm w-48" />
        <input type="text" value={cardNumFilter} onChange={(e) => setCardNumFilter(e.target.value)} placeholder="Card Number" className="border border-slate-300 rounded px-3 py-2 text-sm w-48" />
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
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Card Number</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Account ID</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Name</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Expiry</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {cards.map((card) => (
                  <tr key={card.card_num} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono">{card.card_num}</td>
                    <td className="px-4 py-3">{card.acct_id}</td>
                    <td className="px-4 py-3">{card.embossed_name || '-'}</td>
                    <td className="px-4 py-3">{card.expiration_date || '-'}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${card.active_status === 'Y' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {card.active_status === 'Y' ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3 space-x-2">
                      <Link href={`/cards/${card.card_num}?acct_id=${card.acct_id}`} className="text-blue-600 hover:underline text-sm">View</Link>
                      <Link href={`/cards/${card.card_num}/edit?acct_id=${card.acct_id}`} className="text-blue-600 hover:underline text-sm">Edit</Link>
                    </td>
                  </tr>
                ))}
                {cards.length === 0 && (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No cards found</td></tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between mt-4 text-sm">
            <span className="text-slate-500">Total: {total} cards</span>
            <div className="flex gap-2">
              <button onClick={() => fetchCards(page - 1)} disabled={page <= 1} className="px-3 py-1 border border-slate-300 rounded disabled:opacity-30 hover:bg-slate-50">Prev</button>
              <span className="px-3 py-1">Page {page}</span>
              <button onClick={() => fetchCards(page + 1)} disabled={!hasMore} className="px-3 py-1 border border-slate-300 rounded disabled:opacity-30 hover:bg-slate-50">Next</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
