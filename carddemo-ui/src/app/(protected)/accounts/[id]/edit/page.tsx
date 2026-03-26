'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { AccountDetail } from '@/lib/types';

export default function AccountEditPage() {
  const params = useParams();
  const router = useRouter();
  const acctId = params.id as string;
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState({
    acct_id: 0,
    active_status: '',
    curr_bal: '',
    credit_limit: '',
    cash_credit_limit: '',
    open_date: '',
    expiration_date: '',
    reissue_date: '',
    curr_cyc_credit: '',
    curr_cyc_debit: '',
    addr_zip: '',
    group_id: '',
    cust_first_name: '',
    cust_middle_name: '',
    cust_last_name: '',
    cust_addr_line_1: '',
    cust_addr_line_2: '',
    cust_addr_line_3: '',
    cust_addr_state_cd: '',
    cust_addr_country_cd: '',
    cust_addr_zip: '',
    cust_phone_num_1: '',
    cust_phone_num_2: '',
    cust_ssn: '',
    cust_govt_issued_id: '',
    cust_dob_yyyymmdd: '',
    cust_eft_account_id: '',
    cust_pri_card_holder_ind: '',
    cust_fico_credit_score: '',
  });

  useEffect(() => {
    api.get<AccountDetail>(`/api/accounts/${acctId}`)
      .then((data) => {
        const a = data.account;
        const c = data.customer;
        setForm({
          acct_id: a.acct_id,
          active_status: a.active_status || '',
          curr_bal: a.curr_bal?.toString() || '',
          credit_limit: a.credit_limit?.toString() || '',
          cash_credit_limit: a.cash_credit_limit?.toString() || '',
          open_date: a.open_date || '',
          expiration_date: a.expiration_date || '',
          reissue_date: a.reissue_date || '',
          curr_cyc_credit: a.curr_cyc_credit?.toString() || '',
          curr_cyc_debit: a.curr_cyc_debit?.toString() || '',
          addr_zip: a.addr_zip || '',
          group_id: a.group_id || '',
          cust_first_name: c?.first_name || '',
          cust_middle_name: c?.middle_name || '',
          cust_last_name: c?.last_name || '',
          cust_addr_line_1: c?.addr_line_1 || '',
          cust_addr_line_2: c?.addr_line_2 || '',
          cust_addr_line_3: c?.addr_line_3 || '',
          cust_addr_state_cd: c?.addr_state_cd || '',
          cust_addr_country_cd: c?.addr_country_cd || '',
          cust_addr_zip: c?.addr_zip || '',
          cust_phone_num_1: c?.phone_num_1 || '',
          cust_phone_num_2: c?.phone_num_2 || '',
          cust_ssn: c?.ssn?.toString() || '',
          cust_govt_issued_id: c?.govt_issued_id || '',
          cust_dob_yyyymmdd: c?.dob_yyyymmdd || '',
          cust_eft_account_id: c?.eft_account_id || '',
          cust_pri_card_holder_ind: c?.pri_card_holder_ind || '',
          cust_fico_credit_score: c?.fico_credit_score?.toString() || '',
        });
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [acctId]);

  const handleChange = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);
    try {
      const payload: Record<string, unknown> = { acct_id: Number(acctId) };
      if (form.active_status) payload.active_status = form.active_status;
      if (form.curr_bal) payload.curr_bal = Number(form.curr_bal);
      if (form.credit_limit) payload.credit_limit = Number(form.credit_limit);
      if (form.cash_credit_limit) payload.cash_credit_limit = Number(form.cash_credit_limit);
      if (form.open_date) payload.open_date = form.open_date;
      if (form.expiration_date) payload.expiration_date = form.expiration_date;
      if (form.reissue_date) payload.reissue_date = form.reissue_date;
      if (form.addr_zip) payload.addr_zip = form.addr_zip;
      if (form.group_id) payload.group_id = form.group_id;
      if (form.cust_first_name) payload.cust_first_name = form.cust_first_name;
      if (form.cust_middle_name) payload.cust_middle_name = form.cust_middle_name;
      if (form.cust_last_name) payload.cust_last_name = form.cust_last_name;
      if (form.cust_addr_line_1) payload.cust_addr_line_1 = form.cust_addr_line_1;
      if (form.cust_addr_line_2) payload.cust_addr_line_2 = form.cust_addr_line_2;
      if (form.cust_addr_line_3) payload.cust_addr_line_3 = form.cust_addr_line_3;
      if (form.cust_addr_state_cd) payload.cust_addr_state_cd = form.cust_addr_state_cd;
      if (form.cust_addr_country_cd) payload.cust_addr_country_cd = form.cust_addr_country_cd;
      if (form.cust_addr_zip) payload.cust_addr_zip = form.cust_addr_zip;
      if (form.cust_phone_num_1) payload.cust_phone_num_1 = form.cust_phone_num_1;
      if (form.cust_phone_num_2) payload.cust_phone_num_2 = form.cust_phone_num_2;
      if (form.cust_ssn) payload.cust_ssn = Number(form.cust_ssn);
      if (form.cust_govt_issued_id) payload.cust_govt_issued_id = form.cust_govt_issued_id;
      if (form.cust_dob_yyyymmdd) payload.cust_dob_yyyymmdd = form.cust_dob_yyyymmdd;
      if (form.cust_eft_account_id) payload.cust_eft_account_id = form.cust_eft_account_id;
      if (form.cust_pri_card_holder_ind) payload.cust_pri_card_holder_ind = form.cust_pri_card_holder_ind;
      if (form.cust_fico_credit_score) payload.cust_fico_credit_score = Number(form.cust_fico_credit_score);

      await api.put(`/api/accounts/${acctId}`, payload);
      setSuccess('Account updated successfully');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800 mx-auto mt-8" />;

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Edit Account #{acctId}</h1>
        <button onClick={() => router.back()} className="text-sm text-slate-600 hover:text-slate-800">Back</button>
      </div>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      {success && <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded text-sm mb-4">{success}</div>}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="border border-slate-200 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Account Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Status</label><select value={form.active_status} onChange={(e) => handleChange('active_status', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2"><option value="Y">Active</option><option value="N">Inactive</option></select></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Current Balance</label><input type="number" step="0.01" value={form.curr_bal} onChange={(e) => handleChange('curr_bal', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Credit Limit</label><input type="number" step="0.01" value={form.credit_limit} onChange={(e) => handleChange('credit_limit', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Cash Credit Limit</label><input type="number" step="0.01" value={form.cash_credit_limit} onChange={(e) => handleChange('cash_credit_limit', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Open Date</label><input type="text" value={form.open_date} onChange={(e) => handleChange('open_date', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2" placeholder="YYYY-MM-DD" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Expiration Date</label><input type="text" value={form.expiration_date} onChange={(e) => handleChange('expiration_date', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2" placeholder="YYYY-MM-DD" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Reissue Date</label><input type="text" value={form.reissue_date} onChange={(e) => handleChange('reissue_date', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2" placeholder="YYYY-MM-DD" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">ZIP Code</label><input type="text" value={form.addr_zip} onChange={(e) => handleChange('addr_zip', e.target.value)} maxLength={10} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Group ID</label><input type="text" value={form.group_id} onChange={(e) => handleChange('group_id', e.target.value)} maxLength={10} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          </div>
        </div>

        <div className="border border-slate-200 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Customer Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium text-slate-700 mb-1">First Name</label><input type="text" value={form.cust_first_name} onChange={(e) => handleChange('cust_first_name', e.target.value)} maxLength={25} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Middle Name</label><input type="text" value={form.cust_middle_name} onChange={(e) => handleChange('cust_middle_name', e.target.value)} maxLength={25} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Last Name</label><input type="text" value={form.cust_last_name} onChange={(e) => handleChange('cust_last_name', e.target.value)} maxLength={25} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Address Line 1</label><input type="text" value={form.cust_addr_line_1} onChange={(e) => handleChange('cust_addr_line_1', e.target.value)} maxLength={50} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Address Line 2</label><input type="text" value={form.cust_addr_line_2} onChange={(e) => handleChange('cust_addr_line_2', e.target.value)} maxLength={50} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Address Line 3</label><input type="text" value={form.cust_addr_line_3} onChange={(e) => handleChange('cust_addr_line_3', e.target.value)} maxLength={50} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">State</label><input type="text" value={form.cust_addr_state_cd} onChange={(e) => handleChange('cust_addr_state_cd', e.target.value)} maxLength={2} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Country</label><input type="text" value={form.cust_addr_country_cd} onChange={(e) => handleChange('cust_addr_country_cd', e.target.value)} maxLength={3} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">ZIP</label><input type="text" value={form.cust_addr_zip} onChange={(e) => handleChange('cust_addr_zip', e.target.value)} maxLength={10} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Phone 1</label><input type="text" value={form.cust_phone_num_1} onChange={(e) => handleChange('cust_phone_num_1', e.target.value)} maxLength={15} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Phone 2</label><input type="text" value={form.cust_phone_num_2} onChange={(e) => handleChange('cust_phone_num_2', e.target.value)} maxLength={15} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">SSN</label><input type="number" value={form.cust_ssn} onChange={(e) => handleChange('cust_ssn', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Govt Issued ID</label><input type="text" value={form.cust_govt_issued_id} onChange={(e) => handleChange('cust_govt_issued_id', e.target.value)} maxLength={20} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Date of Birth</label><input type="text" value={form.cust_dob_yyyymmdd} onChange={(e) => handleChange('cust_dob_yyyymmdd', e.target.value)} maxLength={10} className="w-full border border-slate-300 rounded px-3 py-2" placeholder="YYYY-MM-DD" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">EFT Account ID</label><input type="text" value={form.cust_eft_account_id} onChange={(e) => handleChange('cust_eft_account_id', e.target.value)} maxLength={10} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">Primary Holder</label><select value={form.cust_pri_card_holder_ind} onChange={(e) => handleChange('cust_pri_card_holder_ind', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2"><option value="Y">Yes</option><option value="N">No</option></select></div>
            <div><label className="block text-sm font-medium text-slate-700 mb-1">FICO Score</label><input type="number" value={form.cust_fico_credit_score} onChange={(e) => handleChange('cust_fico_credit_score', e.target.value)} className="w-full border border-slate-300 rounded px-3 py-2" /></div>
          </div>
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700 disabled:opacity-50">
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button type="button" onClick={() => router.back()} className="border border-slate-300 px-6 py-2 rounded hover:bg-slate-50">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
