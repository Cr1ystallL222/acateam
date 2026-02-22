"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';

export default function TopUpPage() {
    const { user, loading } = useAuth();
    const router = useRouter();

    const [activeTab, setActiveTab] = useState<'topup' | 'history'>('topup');

    // Topup Form State
    const [amount, setAmount] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // History State
    const [history, setHistory] = useState<any[]>([]);
    const [isHistoryLoading, setIsHistoryLoading] = useState(false);

    useEffect(() => {
        if (activeTab === 'history' && user) {
            fetchHistory();
        }
    }, [activeTab, user]);

    const fetchHistory = async () => {
        setIsHistoryLoading(true);
        try {
            const data = await api.topup.history();
            setHistory(data.history || []);
        } catch (err) {
            console.error('Failed to fetch history:', err);
        } finally {
            setIsHistoryLoading(false);
        }
    };

    const handleCancel = async (id: number) => {
        try {
            await api.topup.cancel(id);
            // Refresh history
            fetchHistory();
        } catch (err: any) {
            alert(err.message || 'Ошибка отмены');
        }
    };

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

    const getStatusText = (status: string) => {
        switch (status) {
            case 'pending': return { text: 'Ожидает', color: 'text-yellow-500', bg: 'bg-yellow-500/10' };
            case 'awaiting_requisites': return { text: 'Ожидает реквизитов', color: 'text-yellow-500', bg: 'bg-yellow-500/10' };
            case 'requisites_sent': return { text: 'Ожидает оплаты', color: 'text-blue-500', bg: 'bg-blue-500/10' };
            case 'awaiting_confirmation': return { text: 'Проверка', color: 'text-orange-500', bg: 'bg-orange-500/10' };
            case 'completed': return { text: 'Успешно', color: 'text-green-500', bg: 'bg-green-500/10' };
            case 'expired': return { text: 'Истекла', color: 'text-gray-500', bg: 'bg-gray-500/10' };
            case 'cancelled': return { text: 'Отменена', color: 'text-red-500', bg: 'bg-red-500/10' };
            default: return { text: status, color: 'text-gray-500', bg: 'bg-gray-500/10' };
        }
    };

    return (
        <div className="min-h-screen bg-[#1A1A1A] flex flex-col items-center py-12 px-4">
            <div className="w-full max-w-lg">
                <div className="bg-[#2E2E2E] rounded-2xl p-6 md:p-8 shadow-2xl border border-white/10">
                    <div className="flex justify-between items-center mb-6">
                        <h1 className="text-2xl font-bold text-white">Баланс</h1>
                        <span className="text-white font-medium bg-[#1A1A1A] px-4 py-2 rounded-lg border border-white/5">
                            {(user.balance || 0).toLocaleString('ru-RU')} ₽
                        </span>
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-2 mb-8 bg-[#1A1A1A] p-1 rounded-xl">
                        <button
                            onClick={() => setActiveTab('topup')}
                            className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-colors ${activeTab === 'topup' ? 'bg-[#2E2E2E] text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}
                        >
                            Пополнение
                        </button>
                        <button
                            onClick={() => setActiveTab('history')}
                            className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-colors ${activeTab === 'history' ? 'bg-[#2E2E2E] text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}
                        >
                            История заявок
                        </button>
                    </div>

                    {activeTab === 'topup' && (
                        <div className="animate-in fade-in duration-300">
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
                                            className="w-full bg-[#1A1A1A] border border-white/10 rounded-xl px-4 py-3.5 text-white text-lg placeholder:text-gray-600 focus:outline-none focus:border-[#E60000] focus:ring-1 focus:ring-[#E60000] transition-all"
                                        />
                                        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 font-medium">₽</span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-2 ml-1">Минимальная сумма — 2000 ₽</p>
                                </div>

                                {error && (
                                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-sm flex items-center gap-3">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></svg>
                                        {error}
                                    </div>
                                )}

                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="w-full bg-gradient-to-r from-[#E60000] to-red-600 hover:from-red-600 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3.5 rounded-xl transition-all active:scale-[0.98] shadow-lg shadow-red-900/20"
                                >
                                    {isSubmitting ? 'Создание заявки...' : 'Продолжить'}
                                </button>
                            </form>
                        </div>
                    )}

                    {activeTab === 'history' && (
                        <div className="animate-in fade-in duration-300">
                            {isHistoryLoading ? (
                                <div className="py-12 flex justify-center">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#E60000]"></div>
                                </div>
                            ) : history.length === 0 ? (
                                <div className="text-center py-12">
                                    <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-500"><path d="M12 2v20" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>
                                    </div>
                                    <p className="text-gray-400">История пополнений пуста</p>
                                </div>
                            ) : (
                                <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                                    {history.map((item) => {
                                        const statusInfo = getStatusText(item.status);
                                        const isActionable = ['pending', 'awaiting_requisites', 'requisites_sent'].includes(item.status);

                                        return (
                                            <div key={item.id} className="bg-[#1A1A1A] p-4 rounded-xl border border-white/5 flex items-center justify-between group">
                                                <div>
                                                    <div className="flex items-center gap-3 mb-1">
                                                        <span className="text-white font-medium">{item.amount.toLocaleString('ru-RU')} ₽</span>
                                                        <span className={`text-[10px] uppercase tracking-wider font-semibold px-2.5 py-1 rounded-full ${statusInfo.bg} ${statusInfo.color}`}>
                                                            {statusInfo.text}
                                                        </span>
                                                    </div>
                                                    <div className="text-xs text-gray-500">
                                                        {new Date(item.created_at).toLocaleString('ru-RU', {
                                                            day: '2-digit', month: 'short', year: 'numeric',
                                                            hour: '2-digit', minute: '2-digit'
                                                        })}
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-2">
                                                    {isActionable && (
                                                        <>
                                                            <Link href={`/topup/pending?id=${item.id}`} className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors" title="Перейти к оплате">
                                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14" /><path d="M12 5v14" /></svg>
                                                            </Link>
                                                            <button
                                                                onClick={() => {
                                                                    if (confirm('Вы уверены, что хотите отменить эту заявку?')) {
                                                                        handleCancel(item.id);
                                                                    }
                                                                }}
                                                                className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                                                                title="Отменить заявку"
                                                            >
                                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                                                            </button>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )}

                    <div className="mt-8 text-center">
                        <Link href="/" className="text-gray-500 hover:text-white text-sm transition-colors border-b border-transparent hover:border-white/30 pb-0.5">
                            В главное меню
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
