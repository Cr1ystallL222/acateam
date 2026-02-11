"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function LoginTokenContent() {
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [error, setError] = useState('');
    const router = useRouter();
    const searchParams = useSearchParams();

    useEffect(() => {
        const token = searchParams.get('token');
        if (!token) {
            setStatus('error');
            setError('Токен не указан');
            return;
        }

        verifyToken(token);
    }, [searchParams]);

    const verifyToken = async (token: string) => {
        try {
            const response = await fetch(`/api/auth/login-token?token=${encodeURIComponent(token)}`, {
                credentials: 'include'
            });

            if (response.ok) {
                setStatus('success');
                setTimeout(() => {
                    router.push('/');
                }, 2000);
            } else {
                const data = await response.json();
                setStatus('error');
                setError(data.detail || 'Ошибка входа');
            }
        } catch (e: any) {
            setStatus('error');
            setError(e.message || 'Ошибка сети');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
            <div className="max-w-md w-full">
                <div className="bg-white rounded-lg shadow-md p-8 text-center">
                    {status === 'loading' && (
                        <>
                            <div className="mx-auto w-16 h-16 mb-4">
                                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                            </div>
                            <h2 className="text-xl font-semibold text-gray-900 mb-2">Выполняется вход...</h2>
                            <p className="text-gray-600">Пожалуйста, подождите</p>
                        </>
                    )}

                    {status === 'success' && (
                        <>
                            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <h2 className="text-xl font-semibold text-green-800 mb-2">Успешно!</h2>
                            <p className="text-gray-600">Вы вошли в аккаунт. Перенаправляем...</p>
                        </>
                    )}

                    {status === 'error' && (
                        <>
                            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </div>
                            <h2 className="text-xl font-semibold text-red-800 mb-2">Ошибка входа</h2>
                            <p className="text-gray-600 mb-4">{error}</p>
                            <a
                                href="/auth/telegram"
                                className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
                            >
                                Попробовать снова
                            </a>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function LoginTokenPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        }>
            <LoginTokenContent />
        </Suspense>
    );
}
