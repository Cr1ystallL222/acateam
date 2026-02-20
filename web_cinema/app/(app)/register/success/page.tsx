"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function RegisterSuccessPage() {
    const router = useRouter();

    useEffect(() => {
        const timer = setTimeout(() => {
            router.push("/");
        }, 3000);
        return () => clearTimeout(timer);
    }, [router]);

    return (
        <div className="min-h-screen bg-[#1A1A1A] flex items-center justify-center px-4">
            <div className="max-w-md w-full">
                <div className="bg-[#111] rounded-lg shadow-xl p-8 text-center border border-white/5">
                    <div className="mb-6">
                        <div className="mx-auto w-16 h-16 bg-green-900/20 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h1 className="text-2xl font-bold text-white mb-2">Регистрация завершена!</h1>
                        <p className="text-gray-400">
                            Ваш аккаунт успешно создан. Теперь вы можете пользоваться всеми возможностями платформы.
                        </p>
                    </div>

                    <div className="space-y-4">
                        <div className="bg-green-900/20 shadow-[0_0_10px_rgba(34,197,94,0.1)] border border-green-500/30 rounded-md p-4">
                            <h3 className="text-sm font-medium text-green-400 mb-1">Что дальше?</h3>
                            <p className="text-sm text-green-500/80">
                                Вы будете перенаправлены на главную страницу через несколько секунд
                            </p>
                        </div>

                        <button
                            onClick={() => router.push("/")}
                            className="w-full bg-[#E60000] hover:bg-red-700 text-white font-medium py-2.5 px-4 rounded-md transition-colors shadow-lg shadow-red-500/20"
                        >
                            Перейти на главную
                        </button>
                    </div>

                    <div className="mt-6 pt-6 border-t border-white/10">
                        <p className="text-xs text-gray-500">
                            Автоматическое перенаправление через 3 секунды...
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
