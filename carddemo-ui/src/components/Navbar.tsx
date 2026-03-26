'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { clearToken, getUserId, getUserType } from '@/lib/api';

export default function Navbar() {
  const router = useRouter();
  const [userId, setUserId] = useState<string | null>(null);
  const [userType, setUserType] = useState<string | null>(null);

  useEffect(() => {
    setUserId(getUserId());
    setUserType(getUserType());
  }, []);

  const handleLogout = () => {
    clearToken();
    router.push('/login');
  };

  return (
    <nav className="bg-slate-800 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="text-xl font-bold tracking-tight">
            CardDemo
          </Link>
          <div className="flex items-center gap-6">
            {userId && (
              <>
                <span className="text-sm text-slate-300">
                  {userId} ({userType === 'A' ? 'Admin' : 'User'})
                </span>
                <button
                  onClick={handleLogout}
                  className="text-sm bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded transition-colors"
                >
                  Sign Out
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
