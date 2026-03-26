'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Transaction } from '@/lib/types';

export default function TransactionDetailPage() {
  const params = useParams();
  const tranId = params.id as string;
  const [data, setData] = useState<Transaction | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Transaction>(`/api/transactions/${tranId}`)
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [tranId]);

  if (loading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto mt-8" />;
  if (error) return <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">{error}</div>;
  if (!data) return null;

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Transaction Detail</h1>
        <Link href="/transactions" className="text-sm text-slate-600 hover:text-slate-800">Back to List</Link>
      </div>
      <div className="border border-slate-200 rounded-lg p-5">
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between"><dt className="text-slate-500">Transaction ID</dt><dd className="font-mono font-medium">{data.tran_id}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Type Code</dt><dd className="font-medium">{data.type_cd || '-'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Category Code</dt><dd className="font-medium">{data.cat_cd ?? '-'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Source</dt><dd className="font-medium">{data.source || '-'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Description</dt><dd className="font-medium">{data.description || '-'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Amount</dt><dd className="font-medium text-lg">${Number(data.amount || 0).toFixed(2)}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Card Number</dt><dd className="font-mono font-medium">{data.card_num}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Merchant ID</dt><dd className="font-medium">{data.merchant_id || '-'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Merchant Name</dt><dd className="font-medium">{data.merchant_name || '-'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Merchant City</dt><dd className="font-medium">{data.merchant_city || '-'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Merchant ZIP</dt><dd className="font-medium">{data.merchant_zip || '-'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Originated</dt><dd className="font-medium">{data.orig_ts || '-'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Processed</dt><dd className="font-medium">{data.proc_ts || '-'}</dd></div>
        </dl>
      </div>
    </div>
  );
}
