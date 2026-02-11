"use client";

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import Link from 'next/link';

function VerifyingContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const depositId = searchParams.get('id');
    const [dots, setDots] = useState('');
    const [status, setStatus] = useState<string>('awaiting_confirmation');
    const [message, setMessage] = useState<string>('');

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
                const result = await api.topup.status(parseInt(depositId));
                setStatus(result.status);

                if (result.status === 'completed') {
                    setMessage('Баланс успешно пополнен!');
                    clearInterval(pollInterval);
                } else if (result.status === 'rejected') {
                    setMessage('Перевод не найден. Попробуйте ещё раз или свяжитесь с поддержкой.');
                    clearInterval(pollInterval);
                } else if (result.status === 'expired' || result.status === 'cancelled') {
                    router.push('/');
                }
            } catch (err) {
                console.error('Status poll error:', err);
            }
        }, 2000);

        return () => clearInterval(pollInterval);
    }, [depositId, router]);

    // Show result screen
    if (status === 'completed' || status === 'rejected') {
        return (
            <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center p-4">
                <div className="text-center max-w-md">
                    {status === 'completed' ? (
                        <>
                            <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-green-500">
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                            </div>
                            <h1 className="text-2xl font-bold text-white mb-2">Успешно!</h1>
                            <p className="text-gray-400 mb-8">{message}</p>
                        </>
                    ) : (
                        <>
                            <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-500">
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </div>
                            <h1 className="text-2xl font-bold text-white mb-2">Не найден</h1>
                            <p className="text-gray-400 mb-8">{message}</p>
                        </>
                    )}

                    <Link
                        href="/"
                        className="inline-block bg-[#E60000] hover:bg-red-600 text-white font-medium py-3 px-8 rounded-lg transition-colors"
                    >
                        ОК
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center p-4">
            <div className="text-center">
                <div className="mb-8">
                    <div className="w-16 h-16 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                </div>

                <h1 className="text-2xl font-bold text-white mb-2">
                    Проверяем оплату{dots}
                </h1>
                <p className="text-gray-400">
                    Мы ищем вашу операцию. Это может занять несколько минут.
                </p>

                <div className="mt-8 text-sm text-gray-500">
                    Не закрывайте эту страницу
                </div>
            </div>
        </div>
    );
}

export default function VerifyingPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center">
                <div className="text-gray-400">Загрузка...</div>
            </div>
        }>
            <VerifyingContent />
        </Suspense>
    );
}
