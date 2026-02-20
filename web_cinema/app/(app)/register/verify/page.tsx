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
            <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center text-white">
                <div className="text-center">
                    <h1 className="text-2xl font-bold mb-2">Ошибка сессии</h1>
                    <p className="text-gray-400">Неверная ссылка верификации</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#1A1A1A] py-12 px-4">
            <div className="max-w-md mx-auto">
                <div className="text-center mb-8 pt-10">
                    <h1 className="text-3xl font-bold text-white mb-2">Верификация через Telegram</h1>
                    <p className="text-gray-400">Подтвердите свою личность через наш Telegram бот</p>
                </div>

                <div className="bg-white rounded-lg shadow-md p-6 text-gray-900">
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
                                className="inline-flex items-center px-4 py-2 bg-[#0088cc] hover:bg-[#0077b5] text-white font-medium rounded-md transition-colors"
                            >
                                <svg className="w-5 h-5 mr-2 -ml-1" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.04-.18-.05-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.62-.2-1.11-.31-1.07-.66.02-.18.27-.36.75-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z" />
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
            <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto mb-4"></div>
                    <p className="text-gray-400">Загрузка...</p>
                </div>
            </div>
        }>
            <VerifyContent />
        </Suspense>
    );
}
