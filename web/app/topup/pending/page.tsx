"use client";

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';

function PendingContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const depositId = searchParams.get('id');
    const [dots, setDots] = useState('');
    const [isCancelling, setIsCancelling] = useState(false);

    useEffect(() => {
        // Animated dots
        const dotsInterval = setInterval(() => {
            setDots(prev => prev.length >= 3 ? '' : prev + '.');
        }, 500);

        return () => clearInterval(dotsInterval);
    }, []);

    useEffect(() => {
        if (!depositId) {
            router.push('/topup');
            return;
        }

        // Poll for status
        const pollInterval = setInterval(async () => {
            try {
                const status = await api.topup.status(parseInt(depositId));

                if (status.status === 'requisites_sent') {
                    // Redirect to pay page
                    router.push(`/topup/pay?id=${depositId}`);
                } else if (status.status === 'expired' || status.status === 'cancelled') {
                    router.push('/');
                }
            } catch (err) {
                console.error('Status poll error:', err);
            }
        }, 2000);

        return () => clearInterval(pollInterval);
    }, [depositId, router]);

    const handleCancel = async () => {
        if (!depositId || isCancelling) return;

        if (!confirm('Вы уверены, что хотите отменить заявку?')) return;

        setIsCancelling(true);
        try {
            await api.topup.cancel(parseInt(depositId));
            router.push('/');
        } catch (err: any) {
            alert(err.message || 'Ошибка отмены');
            setIsCancelling(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center p-4">
            <div className="text-center">
                <div className="mb-8">
                    <div className="w-16 h-16 border-4 border-[#E60000] border-t-transparent rounded-full animate-spin mx-auto"></div>
                </div>

                <h1 className="text-2xl font-bold text-white mb-2">
                    Ищем реквизиты{dots}
                </h1>
                <p className="text-gray-400">
                    Пожалуйста, подождите. Это займёт несколько минут.
                </p>

                <div className="mt-8 text-sm text-gray-500">
                    Не закрывайте эту страницу
                </div>

                <button
                    onClick={handleCancel}
                    disabled={isCancelling}
                    className="mt-6 text-gray-500 hover:text-red-400 text-sm transition-colors disabled:opacity-50"
                >
                    {isCancelling ? 'Отмена...' : 'Отменить заявку'}
                </button>
            </div>
        </div>
    );
}

export default function PendingPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center">
                <div className="text-gray-400">Загрузка...</div>
            </div>
        }>
            <PendingContent />
        </Suspense>
    );
}
