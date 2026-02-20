'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { CardDetail } from '@/lib/types';

export default function CardDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const cardNum = params.num as string;
  const acctId = searchParams.get('acct_id') || '';
  const [data, setData] = useState<CardDetail | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!acctId) {
      setError('Account ID is required');
      setLoading(false);
      return;
    }
    api.get<CardDetail>(`/api/cards/${cardNum}/${acctId}`)
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [cardNum, acctId]);

  if (loading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto mt-8" />;
  if (error) return <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">{error}</div>;
  if (!data) return null;

  const { card, account, customer } = data;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Card Detail</h1>
        <div className="flex gap-3">
          <Link href="/cards" className="text-sm text-slate-600 hover:text-slate-800">Back to List</Link>
          <Link href={`/cards/${cardNum}/edit?acct_id=${acctId}`} className="bg-slate-800 text-white px-4 py-2 rounded hover:bg-slate-700 text-sm">Edit Card</Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border border-slate-200 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Card Information</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Card Number</dt><dd className="font-mono font-medium">{card.card_num}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Account ID</dt><dd className="font-medium">{card.acct_id}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Embossed Name</dt><dd className="font-medium">{card.embossed_name || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">CVV</dt><dd className="font-medium">{card.cvv_cd || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Expiration</dt><dd className="font-medium">{card.expiration_date || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Status</dt><dd><span className={`px-2 py-0.5 rounded text-xs font-medium ${card.active_status === 'Y' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{card.active_status === 'Y' ? 'Active' : 'Inactive'}</span></dd></div>
          </dl>
        </div>

        {account && (
          <div className="border border-slate-200 rounded-lg p-5">
            <h2 className="text-lg font-semibold mb-4">Account Information</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-slate-500">Account ID</dt><dd className="font-medium">{account.acct_id}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Balance</dt><dd className="font-medium">${Number(account.curr_bal || 0).toFixed(2)}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Credit Limit</dt><dd className="font-medium">${Number(account.credit_limit || 0).toFixed(2)}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Status</dt><dd className="font-medium">{account.active_status === 'Y' ? 'Active' : 'Inactive'}</dd></div>
            </dl>
          </div>
        )}

        {customer && (
          <div className="border border-slate-200 rounded-lg p-5">
            <h2 className="text-lg font-semibold mb-4">Customer Information</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-slate-500">Name</dt><dd className="font-medium">{[customer.first_name, customer.last_name].filter(Boolean).join(' ')}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Phone</dt><dd className="font-medium">{customer.phone_num_1 || '-'}</dd></div>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}
