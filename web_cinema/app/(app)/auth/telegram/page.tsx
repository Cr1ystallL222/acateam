"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const TelegramIcon = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
    </svg>
);

function TelegramAuthContent() {
    const [botLink, setBotLink] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [opened, setOpened] = useState(false);
    const router = useRouter();
    const params = useSearchParams();
    const mode = params.get('mode') === 'register' ? 'register' : 'login';
    const { refreshUser, user } = useAuth();

    useEffect(() => {
        if (user) {
            router.push('/');
        }
    }, [user, router]);

    const startAuth = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await api.auth.start(mode);
            setBotLink(res.bot_link);
            window.open(res.bot_link, '_blank');
            setOpened(true);
        } catch (e: any) {
            setError(e.message || 'Ошибка при запуске авторизации');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#0d0d12] flex items-center justify-center py-12 px-4">
            <div className="w-full max-w-md">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 mb-4">
                        <TelegramIcon className="w-8 h-8 text-blue-400" />
                    </div>
                    <h1 className="text-2xl font-bold text-white mb-2">
                        {mode === 'register' ? 'Регистрация' : 'Вход'} через Telegram
                    </h1>
                    <p className="text-gray-400 text-sm">
                        {mode === 'register'
                            ? 'Зарегистрируйтесь через наш Telegram бот'
                            : 'Войдите в аккаунт через наш Telegram бот'}
                    </p>
                </div>

                {/* Card */}
                <div className="bg-[#17181f] border border-white/5 rounded-2xl p-6 shadow-xl">
                    {error && (
                        <div className="mb-5 p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                            <p className="text-red-400 text-sm">{error}</p>
                        </div>
                    )}

                    {!opened ? (
                        <div className="text-center">
                            <div className="mb-6">
                                <h3 className="text-lg font-semibold text-white mb-2">
                                    Авторизация через бот
                                </h3>
                                <p className="text-gray-400 text-sm leading-relaxed">
                                    Нажмите кнопку ниже — откроется Telegram бот.<br />
                                    <span className="text-gray-500">Поделитесь номером телефона и получите ссылку для входа.</span>
                                </p>
                            </div>

                            <button
                                id="open-telegram-btn"
                                onClick={startAuth}
                                disabled={loading}
                                className="w-full bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white font-semibold py-3 px-4 rounded-xl transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2.5"
                            >
                                <TelegramIcon className="w-5 h-5 flex-shrink-0" />
                                {loading ? "Открываем..." : "Открыть Telegram бот"}
                            </button>
                        </div>
                    ) : (
                        <div className="text-center space-y-5">
                            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-green-500/10 border border-green-500/20 mb-1">
                                <svg className="w-7 h-7 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white mb-2">Бот открыт!</h3>
                                <p className="text-gray-400 text-sm leading-relaxed">
                                    Перейдите в Telegram бот и поделитесь своим номером телефона.<br />
                                    <span className="text-white font-medium">Если ваш номер есть в базе</span> — бот пришлёт ссылку для входа.
                                </p>
                            </div>

                            <a
                                id="reopen-bot-link"
                                href={botLink}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-4 rounded-xl transition-all duration-150 flex items-center justify-center gap-2.5"
                            >
                                <TelegramIcon className="w-5 h-5 flex-shrink-0" />
                                Открыть бот снова
                            </a>

                            <button
                                onClick={() => setOpened(false)}
                                className="text-gray-500 hover:text-gray-300 text-sm underline underline-offset-2 transition-colors"
                            >
                                Начать заново
                            </button>
                        </div>
                    )}

                    <div className="mt-6 pt-5 border-t border-white/5 text-center">
                        <p className="text-sm text-gray-500">
                            {mode === 'register' ? 'Уже есть аккаунт?' : 'Нет аккаунта?'}{" "}
                            <a
                                href={mode === 'register' ? '/auth/telegram' : '/auth/telegram?mode=register'}
                                className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
                            >
                                {mode === 'register' ? 'Войти' : 'Зарегистрироваться'}
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function TelegramAuthPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#0d0d12] flex items-center justify-center">
                <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        }>
            <TelegramAuthContent />
        </Suspense>
    );
}
