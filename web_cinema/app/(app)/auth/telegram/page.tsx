"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

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
        <div className="min-h-screen bg-gray-50 py-12 px-4">
            <div className="max-w-md mx-auto">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        {mode === 'register' ? 'Регистрация' : 'Вход'} через Telegram
                    </h1>
                    <p className="text-gray-600">
                        {mode === 'register'
                            ? 'Зарегистрируйтесь с помощью нашего Telegram бота'
                            : 'Войдите в свой аккаунт с помощью нашего Telegram бота'}
                    </p>
                </div>

                <div className="bg-white rounded-lg shadow-md p-6">
                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                            <p className="text-red-800 text-sm">{error}</p>
                        </div>
                    )}

                    {!opened ? (
                        <div className="text-center">
                            <div className="mb-6">
                                <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                                    <svg className="w-8 h-8 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-medium text-gray-900 mb-2">Авторизация через бот</h3>
                                <p className="text-gray-600">
                                    Нажмите кнопку ниже — откроется Telegram бот.
                                    <br />
                                    <span className="text-sm">Поделитесь номером телефона и получите ссылку для входа.</span>
                                </p>
                            </div>

                            <button
                                onClick={startAuth}
                                disabled={loading}
                                className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
                                </svg>
                                {loading ? "Открываем..." : "Открыть Telegram бот"}
                            </button>
                        </div>
                    ) : (
                        <div className="text-center space-y-6">
                            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="text-lg font-medium text-gray-900 mb-2">Бот открыт!</h3>
                                <p className="text-gray-600 mb-4">
                                    Перейдите в Telegram бот и поделитесь своим номером телефона.
                                    <br />
                                    <strong>Если ваш номер есть в базе</strong> — бот пришлёт ссылку для мгновенного входа.
                                </p>
                            </div>

                            <a
                                href={botLink}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-block w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-4 rounded-md transition-colors"
                            >
                                Открыть бот снова
                            </a>

                            <button
                                onClick={() => setOpened(false)}
                                className="text-gray-500 hover:text-gray-700 text-sm underline"
                            >
                                Начать заново
                            </button>
                        </div>
                    )}

                    <div className="mt-6 pt-6 border-t border-gray-200 text-center">
                        <p className="text-sm text-gray-600">
                            Нет аккаунта?{" "}
                            <a href="/register" className="text-red-600 hover:text-red-800 font-medium">
                                Зарегистрироваться
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
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        }>
            <TelegramAuthContent />
        </Suspense>
    );
}
