"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';

export default function CouponsPage() {
    const { user, loading, refreshUser } = useAuth();
    const router = useRouter();

    const [code, setCode] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (!code.trim()) {
            setError('Введите код купона');
            return;
        }

        setIsSubmitting(true);
        try {
            const result = await api.coupons.activate(code.trim());
            setSuccess(result.message || 'Купон успешно активирован!');
            setCode('');
            await refreshUser();
        } catch (err: any) {
            setError(err.message || 'Произошла ошибка при активации');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#111111] flex items-center justify-center">
                <div className="text-gray-400">Загрузка...</div>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="min-h-screen bg-[#111111] flex flex-col items-center justify-center px-4">
                <div className="text-center">
                    <p className="text-gray-400 mb-4">Для активации купонов необходимо войти в аккаунт</p>
                    <Link href="/auth/telegram" className="bg-[#E60000] hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                        Войти
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#111111] flex flex-col items-center py-12 px-4">
            <div className="w-full max-w-lg">
                <div className="bg-[#1A1A1A] rounded-2xl p-6 md:p-8 shadow-2xl border border-white/5">
                    <div className="mb-8">
                        <h1 className="text-2xl font-bold text-white mb-2">Промокоды</h1>
                        <p className="text-gray-400 text-sm">Здесь вы можете активировать купон на пополнение баланса или получение скидки.</p>
                    </div>

                    <form onSubmit={handleSubmit}>
                        <div className="mb-6">
                            <label className="block text-sm text-gray-400 mb-2">
                                Код купона
                            </label>
                            <input
                                type="text"
                                value={code}
                                onChange={(e) => setCode(e.target.value.toUpperCase())}
                                placeholder="C-XXXX-XXXX"
                                className="w-full bg-[#111111] border border-white/10 rounded-xl px-4 py-3.5 text-white text-lg placeholder:text-gray-600 focus:outline-none focus:border-[#E60000] focus:ring-1 focus:ring-[#E60000] transition-all uppercase tracking-wider"
                            />
                        </div>

                        {error && (
                            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
                                {error}
                            </div>
                        )}

                        {success && (
                            <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-green-500 text-sm font-medium">
                                {success}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isSubmitting || !code.trim()}
                            className="w-full bg-[#E60000] hover:bg-red-600 active:bg-red-700 text-white font-medium py-3.5 rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {isSubmitting ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                    Активация...
                                </>
                            ) : (
                                'Активировать'
                            )}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
