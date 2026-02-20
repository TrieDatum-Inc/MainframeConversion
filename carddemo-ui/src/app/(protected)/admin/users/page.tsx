'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { User, PaginatedResponse, MessageResponse } from '@/lib/types';
import ProtectedRoute from '@/components/ProtectedRoute';

function UsersContent() {
  const [users, setUsers] = useState<User[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('');

  const fetchData = useCallback(async (p: number) => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.set('page', p.toString());
      params.set('page_size', '10');
      if (filter) params.set('user_id_filter', filter);
      const data = await api.get<PaginatedResponse<User>>(`/api/users?${params}`);
      setUsers(data.items);
      setTotal(data.total);
      setHasMore(data.has_more);
      setPage(data.page);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { fetchData(1); }, [fetchData]);

  const handleDelete = async (userId: string) => {
    if (!confirm(`Delete user ${userId}?`)) return;
    try {
      await api.delete<MessageResponse>(`/api/users/${userId}`);
      fetchData(page);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">User Management</h1>
        <Link href="/admin/users/new" className="bg-slate-800 text-white px-4 py-2 rounded text-sm hover:bg-slate-700">Add User</Link>
      </div>
      <form onSubmit={(e) => { e.preventDefault(); fetchData(1); }} className="flex gap-3 mb-6">
        <input type="text" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter by User ID" className="border border-slate-300 rounded px-3 py-2 text-sm w-48" />
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
                  <th className="text-left px-4 py-3 font-medium text-slate-600">User ID</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">First Name</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Last Name</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Type</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {users.map((u) => (
                  <tr key={u.user_id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono">{u.user_id}</td>
                    <td className="px-4 py-3">{u.first_name || '-'}</td>
                    <td className="px-4 py-3">{u.last_name || '-'}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${u.user_type === 'A' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'}`}>
                        {u.user_type === 'A' ? 'Admin' : 'User'}
                      </span>
                    </td>
                    <td className="px-4 py-3 space-x-2">
                      <Link href={`/admin/users/${u.user_id}/edit`} className="text-blue-600 hover:underline text-sm">Edit</Link>
                      <button onClick={() => handleDelete(u.user_id)} className="text-red-600 hover:underline text-sm">Delete</button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-500">No users found</td></tr>
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

export default function UsersPage() {
  return <ProtectedRoute adminOnly><UsersContent /></ProtectedRoute>;
}
