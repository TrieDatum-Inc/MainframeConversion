'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { ReportSubmitResponse } from '@/lib/types';

export default function ReportsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<ReportSubmitResponse | null>(null);
  const [form, setForm] = useState({
    report_type: 'monthly_transaction',
    start_month: '',
    start_year: '',
    end_month: '',
    end_year: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const res = await api.post<ReportSubmitResponse>('/api/reports/submit', {
        report_type: form.report_type,
        start_month: Number(form.start_month),
        start_year: Number(form.start_year),
        end_month: Number(form.end_month),
        end_year: Number(form.end_year),
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Submit failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Submit Report</h1>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-4">{error}</div>}
      {result && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded text-sm mb-4">
          <p className="font-medium">{result.message}</p>
          <p>Report: {result.report_type} | Period: {result.start_date} to {result.end_date}</p>
          {result.job_id && <p>Job ID: {result.job_id}</p>}
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Report Type</label>
          <select value={form.report_type} onChange={(e) => setForm({ ...form, report_type: e.target.value })} className="w-full border border-slate-300 rounded px-3 py-2">
            <option value="monthly_transaction">Monthly Transaction Report</option>
            <option value="daily_transaction">Daily Transaction Report</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Start Month</label>
            <input type="number" value={form.start_month} onChange={(e) => setForm({ ...form, start_month: e.target.value })} min={1} max={12} required className="w-full border border-slate-300 rounded px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Start Year</label>
            <input type="number" value={form.start_year} onChange={(e) => setForm({ ...form, start_year: e.target.value })} min={2000} required className="w-full border border-slate-300 rounded px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">End Month</label>
            <input type="number" value={form.end_month} onChange={(e) => setForm({ ...form, end_month: e.target.value })} min={1} max={12} required className="w-full border border-slate-300 rounded px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">End Year</label>
            <input type="number" value={form.end_year} onChange={(e) => setForm({ ...form, end_year: e.target.value })} min={2000} required className="w-full border border-slate-300 rounded px-3 py-2" />
          </div>
        </div>
        <button type="submit" disabled={loading} className="bg-slate-800 text-white px-6 py-2 rounded hover:bg-slate-700 disabled:opacity-50">
          {loading ? 'Submitting...' : 'Submit Report'}
        </button>
      </form>
    </div>
  );
}
