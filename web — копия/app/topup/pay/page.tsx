"use client";

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';

function PayContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const depositId = searchParams.get('id');

    const [deposit, setDeposit] = useState<any>(null);
    const [timeLeft, setTimeLeft] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);
    const [isPaying, setIsPaying] = useState(false);

    useEffect(() => {
        if (!depositId) {
            router.push('/topup');
            return;
        }

        const fetchStatus = async () => {
            try {
                const status = await api.topup.status(parseInt(depositId));

                if (status.status === 'expired' || status.status === 'cancelled') {
                    router.push('/?expired=1');
                    return;
                }

                if (status.status === 'awaiting_confirmation' || status.status === 'completed' || status.status === 'rejected') {
                    router.push(`/topup/verifying?id=${depositId}`);
                    return;
                }

                if (status.status !== 'requisites_sent') {
                    router.push(`/topup/pending?id=${depositId}`);
                    return;
                }

                setDeposit(status);

                // Calculate time left
                if (status.expires_at) {
                    const expiresAt = new Date(status.expires_at + 'Z').getTime(); // treat as UTC
                    const now = Date.now();
                    const diff = Math.max(0, Math.floor((expiresAt - now) / 1000));
                    setTimeLeft(diff);
                } else {
                    setTimeLeft(600); // fallback 10 min
                }

                setLoading(false);
            } catch (err) {
                console.error('Status error:', err);
                router.push('/topup');
            }
        };

        fetchStatus();
    }, [depositId, router]);

    // Countdown timer - only starts after timeLeft is set from API
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

    const handlePaid = async () => {
        if (!depositId || isPaying) return;

        setIsPaying(true);
        try {
            await api.topup.paid(parseInt(depositId));
            router.push(`/topup/verifying?id=${depositId}`);
        } catch (err: any) {
            alert(err.message || 'Ошибка');
            setIsPaying(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center">
                <div className="text-gray-400">Загрузка...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center p-4">
            <div className="w-full max-w-lg">
                <div className="bg-[#2E2E2E] rounded-2xl p-8 shadow-2xl border border-white/10">
                    {/* Timer */}
                    <div className="text-center mb-6">
                        <div className={`text-4xl font-bold ${(timeLeft ?? 600) < 60 ? 'text-red-500' : 'text-white'}`}>
                            {formatTime(timeLeft ?? 0)}
                        </div>
                        <p className="text-gray-400 text-sm mt-1">Осталось времени</p>
                    </div>

                    <div className="border-t border-white/10 pt-6">
                        <h1 className="text-xl font-bold text-white mb-4">
                            Переведите точную сумму
                        </h1>

                        {/* Amount */}
                        <div className="bg-gradient-to-br from-[#E60000]/20 to-[#E60000]/5 rounded-xl p-4 mb-4 border border-[#E60000]/30">
                            <div className="text-sm text-gray-400 mb-1">Сумма к оплате</div>
                            <div className="text-3xl font-bold text-white">
                                {deposit?.exact_amount?.toLocaleString('ru-RU')} ₽
                            </div>
                        </div>

                        {/* Requisites */}
                        <div className="bg-[#1A1A1A] rounded-xl p-4 mb-4 border border-white/10">
                            <div className="text-sm text-gray-400 mb-1">Реквизиты</div>
                            <div className="text-lg font-mono text-white select-all">
                                {deposit?.requisites}
                            </div>
                            <button
                                onClick={() => navigator.clipboard.writeText(deposit?.requisites || '')}
                                className="mt-2 text-xs text-[#E60000] hover:text-red-400 transition-colors"
                            >
                                Скопировать
                            </button>
                        </div>

                        {/* Bank */}
                        <div className="bg-[#1A1A1A] rounded-xl p-4 mb-6 border border-white/10">
                            <div className="text-sm text-gray-400 mb-1">Банк</div>
                            <div className="text-lg text-white">
                                {deposit?.bank_name}
                            </div>
                        </div>

                        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 text-yellow-200 text-sm mb-6 flex items-start gap-3">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                                <line x1="12" y1="9" x2="12" y2="13" />
                                <line x1="12" y1="17" x2="12.01" y2="17" />
                            </svg>
                            <span>Переведите <b>точную сумму</b> на указанные реквизиты до истечения таймера.</span>
                        </div>

                        {/* I Paid Button */}
                        <button
                            onClick={handlePaid}
                            disabled={isPaying}
                            className="w-full bg-green-600 hover:bg-green-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-4 rounded-xl transition-colors flex items-center justify-center gap-3 text-lg"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="20 6 9 17 4 12" />
                            </svg>
                            {isPaying ? 'Отправка...' : 'Я оплатил'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function PayPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center">
                <div className="text-gray-400">Загрузка...</div>
            </div>
        }>
            <PayContent />
        </Suspense>
    );
}
