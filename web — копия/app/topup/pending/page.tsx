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
    const [timeLeft, setTimeLeft] = useState<number | null>(null);

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

        // Initial fetch to get time_remaining
        const fetchInitial = async () => {
            try {
                const status = await api.topup.status(parseInt(depositId));

                if (status.status === 'expired' || status.status === 'cancelled') {
                    router.push('/?expired=1');
                    return;
                }

                if (status.status === 'requisites_sent') {
                    router.push(`/topup/pay?id=${depositId}`);
                    return;
                }

                // Set countdown from server
                if (status.time_remaining !== null && status.time_remaining !== undefined) {
                    setTimeLeft(status.time_remaining);
                } else {
                    setTimeLeft(300); // default 5 min
                }
            } catch (err) {
                console.error('Status error:', err);
                router.push('/topup');
            }
        };

        fetchInitial();

        // Poll for status
        const pollInterval = setInterval(async () => {
            try {
                const status = await api.topup.status(parseInt(depositId));

                if (status.status === 'requisites_sent') {
                    router.push(`/topup/pay?id=${depositId}`);
                } else if (status.status === 'expired' || status.status === 'cancelled') {
                    router.push('/?expired=1');
                }
            } catch (err) {
                console.error('Status poll error:', err);
            }
        }, 2000);

        return () => clearInterval(pollInterval);
    }, [depositId, router]);

    // Countdown timer
    useEffect(() => {
        if (timeLeft === null) return;

        if (timeLeft <= 0) {
            router.push('/?expired=1');
            return;
        }

        const timer = setInterval(() => {
            setTimeLeft(prev => {
                if (prev === null || prev <= 1) {
                    router.push('/?expired=1');
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [timeLeft, router]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

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

                {/* Countdown */}
                {timeLeft !== null && (
                    <div className="mt-6">
                        <div className={`text-3xl font-bold ${timeLeft < 60 ? 'text-red-500' : 'text-white'}`}>
                            {formatTime(timeLeft)}
                        </div>
                        <p className="text-gray-500 text-xs mt-1">Осталось времени</p>
                    </div>
                )}

                <div className="mt-6 text-sm text-gray-500">
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
