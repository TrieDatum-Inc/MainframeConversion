'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getUserId, isAdmin } from '@/lib/api';

interface Props {
  children: React.ReactNode;
  adminOnly?: boolean;
}

export default function ProtectedRoute({ children, adminOnly = false }: Props) {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    const userId = getUserId();
    if (!userId) {
      router.push('/login');
      return;
    }
    if (adminOnly && !isAdmin()) {
      router.push('/');
      return;
    }
    setAuthorized(true);
  }, [router, adminOnly]);

  if (!authorized) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800" />
      </div>
    );
  }

  return <>{children}</>;
}
