'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { PendingAuthDetail, FraudToggleResponse } from '@/lib/types';

export default function AuthDetailPage() {
  const params = useParams();
  const router = useRouter();
  const authId = params.id as string;
  const [data, setData] = useState<PendingAuthDetail | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);

  useEffect(() => {
    api.get<PendingAuthDetail>(`/api/authorizations/${authId}`)
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [authId]);

  const handleToggleFraud = async () => {
    setToggling(true);
    setError('');
    try {
      const res = await api.put<FraudToggleResponse>(`/api/authorizations/${authId}/fraud`, {});
      setData((prev) => prev ? { ...prev, fraud_confirmed: res.fraud_confirmed, fraud_rpt_date: res.fraud_rpt_date } : prev);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Toggle failed');
    } finally {
      setToggling(false);
    }
  };

  if (loading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto mt-8" />;
  if (error && !data) return <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">{error}</div>;
  if (!data) return null;

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Authorization Detail #{data.id}</h1>
        <button onClick={() => router.back()} className="text-sm text-slate-600 hover:text-slate-800">Back</button>
      </div>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="border border-slate-200 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Authorization Info</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">ID</dt><dd className="font-medium">{data.id}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Account ID</dt><dd className="font-medium">{data.acct_id}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Card Number</dt><dd className="font-mono font-medium">{data.card_num}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Date/Time</dt><dd className="font-medium">{data.auth_date} {data.auth_time}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Type</dt><dd className="font-medium">{data.auth_type || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Auth ID Code</dt><dd className="font-medium">{data.auth_id_code || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Response Code</dt><dd className="font-medium">{data.auth_resp_code || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Response Reason</dt><dd className="font-medium">{data.auth_resp_reason || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Transaction Amount</dt><dd className="font-medium">${Number(data.transaction_amt || 0).toFixed(2)}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Approved Amount</dt><dd className="font-medium">${Number(data.approved_amt || 0).toFixed(2)}</dd></div>
          </dl>
        </div>

        <div className="border border-slate-200 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Merchant & Message Info</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Merchant ID</dt><dd className="font-medium">{data.merchant_id || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Merchant Name</dt><dd className="font-medium">{data.merchant_name || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Merchant City</dt><dd className="font-medium">{data.merchant_city || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Merchant State</dt><dd className="font-medium">{data.merchant_state || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Merchant ZIP</dt><dd className="font-medium">{data.merchant_zip || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Category Code</dt><dd className="font-medium">{data.merchant_category_code || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Message Type</dt><dd className="font-medium">{data.message_type || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Message Source</dt><dd className="font-medium">{data.message_source || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Processing Code</dt><dd className="font-medium">{data.processing_code || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Card Expiry</dt><dd className="font-medium">{data.card_expiry_date || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">POS Entry Mode</dt><dd className="font-medium">{data.pos_entry_mode || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Acquirer Country</dt><dd className="font-medium">{data.acqr_country_code || '-'}</dd></div>
          </dl>
        </div>
      </div>

      <div className="border border-slate-200 rounded-lg p-5 mt-6">
        <h2 className="text-lg font-semibold mb-4">Fraud Status</h2>
        <div className="flex items-center gap-4">
          <span className={`px-3 py-1 rounded text-sm font-medium ${data.fraud_confirmed === 'Y' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {data.fraud_confirmed === 'Y' ? 'Fraud Confirmed' : 'No Fraud'}
          </span>
          {data.fraud_rpt_date && <span className="text-sm text-slate-500">Reported: {data.fraud_rpt_date}</span>}
          <button
            onClick={handleToggleFraud}
            disabled={toggling}
            className="ml-auto bg-amber-600 text-white px-4 py-2 rounded text-sm hover:bg-amber-700 disabled:opacity-50"
          >
            {toggling ? 'Toggling...' : (data.fraud_confirmed === 'Y' ? 'Clear Fraud Flag' : 'Flag as Fraud')}
          </button>
        </div>
      </div>
    </div>
  );
}
