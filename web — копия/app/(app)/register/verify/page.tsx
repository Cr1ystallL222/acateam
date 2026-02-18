"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useState, Suspense } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

function VerifyContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { refreshUser } = useAuth();

    const session_id = searchParams.get("session_id");
    const bot_link = searchParams.get("bot_link");

    const [code, setCode] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleVerify = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            if (!session_id) throw new Error("Отсутствует ID сессии");

            await api.register.verify(session_id, code);
            await refreshUser();
            router.push("/register/success");
        } catch (err: any) {
            setError(err.message || "Неверный код");
        } finally {
            setLoading(false);
        }
    };

    if (!session_id) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-gray-900 mb-2">Ошибка сессии</h1>
                    <p className="text-gray-600">Неверная ссылка верификации</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4">
            <div className="max-w-md mx-auto">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Верификация через Telegram</h1>
                    <p className="text-gray-600">Подтвердите свою личность через наш Telegram бот</p>
                </div>

                <div className="bg-white rounded-lg shadow-md p-6">
                    {/* Step 1: Open Bot */}
                    <div className="mb-6">
                        <div className="flex items-center mb-3">
                            <div className="flex-shrink-0 w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                                1
                            </div>
                            <h3 className="ml-3 text-lg font-medium text-gray-900">Откройте Telegram бот</h3>
                        </div>
                        <p className="text-gray-600 mb-4 ml-11">
                            Нажмите на кнопку ниже, чтобы открыть наш бот и получить код верификации
                        </p>
                        <div className="ml-11">
                            <a
                                href={bot_link || "#"}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-md transition-colors"
                            >
                                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M12 0C5.374 0 0 5.373 0 12s5.374 12 12 12 12-5.373 12-12S18.626 0 12 0zm5.568 8.16c-.169 1.858-.896 6.728-.896 6.728-.896 6.728-1.268 8.368-1.268 8.368-.159.708-.534.708-.534.708s-2.97-.3-4.317-.3c-1.347 0-4.317.3-4.317.3s-.375 0-.534-.708c0 0-.372-1.64-1.268-8.368 0 0-.727-4.87-.896-6.728-.024-.26.07-.472.32-.472.25 0 .463.212.487.472.169 1.858.896 6.728.896 6.728.896 6.728 1.268 8.368 1.268 8.368.159.708.534.708.534.708s2.97-.3 4.317-.3c1.347 0 4.317.3 4.317.3s.375 0 .534-.708c0 0 .372-1.64 1.268-8.368 0 0 .727-4.87.896-6.728.024-.26-.237-.472-.487-.472-.25 0-.344.212-.32.472z"/>
                                </svg>
                                Открыть Telegram бот
                            </a>
                        </div>
                    </div>

                    {/* Step 2: Enter Code */}
                    <div className="border-t border-gray-200 pt-6">
                        <div className="flex items-center mb-3">
                            <div className="flex-shrink-0 w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                                2
                            </div>
                            <h3 className="ml-3 text-lg font-medium text-gray-900">Введите код</h3>
                        </div>
                        <p className="text-gray-600 mb-4 ml-11">
                            Введите 4-значный код, который вы получили от бота
                        </p>
                        
                        <form onSubmit={handleVerify} className="ml-11 space-y-4">
                            <div>
                                <input
                                    type="text"
                                    className="w-full px-4 py-3 text-center text-2xl font-mono tracking-widest border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                    value={code}
                                    onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 4))}
                                    placeholder="0000"
                                    maxLength={4}
                                />
                            </div>
                            
                            {error && (
                                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                                    <p className="text-red-800 text-sm">{error}</p>
                                </div>
                            )}

                            <button
                                type="submit"
                                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                disabled={loading || code.length < 4}
                            >
                                {loading ? "Проверка..." : "Подтвердить код"}
                            </button>
                        </form>
                    </div>

                    <div className="mt-6 pt-6 border-t border-gray-200 text-center">
                        <p className="text-sm text-gray-500">
                            Не получили код?{" "}
                            <a href={bot_link || "#"} target="_blank" className="text-red-600 hover:text-red-800 font-medium">
                                Открыть бот еще раз
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function RegisterVerifyPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Загрузка...</p>
                </div>
            </div>
        }>
            <VerifyContent />
        </Suspense>
    );
}
