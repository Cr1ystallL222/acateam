"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';

export default function TopUpPage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [amount, setAmount] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        const numAmount = parseInt(amount);
        if (isNaN(numAmount) || numAmount < 2000) {
            setError('Минимальная сумма пополнения — 2000₽');
            return;
        }

        setIsSubmitting(true);
        try {
            const result = await api.topup.create(numAmount);
            // Redirect to pending page with deposit_id
            router.push(`/topup/pending?id=${result.deposit_id}`);
        } catch (err: any) {
            setError(err.message || 'Произошла ошибка');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center">
                <div className="text-gray-400">Загрузка...</div>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center">
                <div className="text-center">
                    <p className="text-gray-400 mb-4">Для пополнения необходимо войти в аккаунт</p>
                    <Link href="/auth/telegram" className="text-[#E60000] hover:underline">
                        Войти
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="bg-[#2E2E2E] rounded-2xl p-8 shadow-2xl border border-white/10">
                    <h1 className="text-2xl font-bold text-white mb-2">Пополнение баланса</h1>
                    <p className="text-gray-400 text-sm mb-6">
                        Текущий баланс: <span className="text-white font-medium">{(user.balance || 0).toLocaleString('ru-RU')} ₽</span>
                    </p>

                    <form onSubmit={handleSubmit}>
                        <div className="mb-6">
                            <label className="block text-sm text-gray-400 mb-2">
                                Сумма пополнения
                            </label>
                            <div className="relative">
                                <input
                                    type="number"
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    placeholder="2000"
                                    min="2000"
                                    className="w-full bg-[#1A1A1A] border border-white/10 rounded-lg px-4 py-3 text-white text-lg placeholder:text-gray-500 focus:outline-none focus:border-[#E60000] transition-colors"
                                />
                                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">₽</span>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">Минимум 2000₽</p>
                        </div>

                        {error && (
                            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full bg-[#E60000] hover:bg-red-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg transition-colors"
                        >
                            {isSubmitting ? 'Создание заявки...' : 'Пополнить'}
                        </button>
                    </form>

                    <div className="mt-6 pt-6 border-t border-white/10">
                        <Link href="/" className="text-gray-400 hover:text-white text-sm transition-colors">
                            ← Вернуться на главную
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
