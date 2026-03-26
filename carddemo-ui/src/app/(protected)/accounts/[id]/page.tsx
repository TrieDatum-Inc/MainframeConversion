'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { AccountDetail } from '@/lib/types';

export default function AccountDetailPage() {
  const params = useParams();
  const acctId = params.id as string;
  const [data, setData] = useState<AccountDetail | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AccountDetail>(`/api/accounts/${acctId}`)
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [acctId]);

  if (loading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto mt-8" />;
  if (error) return <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">{error}</div>;
  if (!data) return null;

  const { account, customer } = data;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Account #{account.acct_id}</h1>
        <Link href={`/accounts/${acctId}/edit`} className="bg-slate-800 text-white px-4 py-2 rounded hover:bg-slate-700 text-sm">
          Edit Account
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border border-slate-200 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Account Information</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Status</dt><dd className="font-medium">{account.active_status === 'Y' ? 'Active' : 'Inactive'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Current Balance</dt><dd className="font-medium">${Number(account.curr_bal || 0).toFixed(2)}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Credit Limit</dt><dd className="font-medium">${Number(account.credit_limit || 0).toFixed(2)}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Cash Credit Limit</dt><dd className="font-medium">${Number(account.cash_credit_limit || 0).toFixed(2)}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Open Date</dt><dd className="font-medium">{account.open_date || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Expiration Date</dt><dd className="font-medium">{account.expiration_date || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Reissue Date</dt><dd className="font-medium">{account.reissue_date || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Cycle Credit</dt><dd className="font-medium">${Number(account.curr_cyc_credit || 0).toFixed(2)}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Cycle Debit</dt><dd className="font-medium">${Number(account.curr_cyc_debit || 0).toFixed(2)}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">ZIP Code</dt><dd className="font-medium">{account.addr_zip || '-'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Group ID</dt><dd className="font-medium">{account.group_id || '-'}</dd></div>
          </dl>
        </div>

        {customer && (
          <div className="border border-slate-200 rounded-lg p-5">
            <h2 className="text-lg font-semibold mb-4">Customer Information</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-slate-500">Customer ID</dt><dd className="font-medium">{customer.cust_id}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Name</dt><dd className="font-medium">{[customer.first_name, customer.middle_name, customer.last_name].filter(Boolean).join(' ')}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Address</dt><dd className="font-medium text-right">{[customer.addr_line_1, customer.addr_line_2, customer.addr_line_3].filter(Boolean).join(', ')}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">State</dt><dd className="font-medium">{customer.addr_state_cd || '-'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Country</dt><dd className="font-medium">{customer.addr_country_cd || '-'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">ZIP</dt><dd className="font-medium">{customer.addr_zip || '-'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Phone 1</dt><dd className="font-medium">{customer.phone_num_1 || '-'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Phone 2</dt><dd className="font-medium">{customer.phone_num_2 || '-'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">SSN</dt><dd className="font-medium">{customer.ssn || '-'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Govt ID</dt><dd className="font-medium">{customer.govt_issued_id || '-'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">DOB</dt><dd className="font-medium">{customer.dob_yyyymmdd || '-'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">EFT Account</dt><dd className="font-medium">{customer.eft_account_id || '-'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Primary Holder</dt><dd className="font-medium">{customer.pri_card_holder_ind || '-'}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">FICO Score</dt><dd className="font-medium">{customer.fico_credit_score || '-'}</dd></div>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}
