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
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
            <div className="max-w-md w-full">
                <div className="bg-white rounded-lg shadow-md p-8 text-center">
                    <div className="mb-6">
                        <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900 mb-2">Регистрация завершена!</h1>
                        <p className="text-gray-600">
                            Ваш аккаунт успешно создан. Теперь вы можете пользоваться всеми возможностями платформы.
                        </p>
                    </div>

                    <div className="space-y-4">
                        <div className="bg-green-50 border border-green-200 rounded-md p-4">
                            <h3 className="text-sm font-medium text-green-800 mb-1">Что дальше?</h3>
                            <p className="text-sm text-green-700">
                                Вы будете перенаправлены на главную страницу через несколько секунд
                            </p>
                        </div>

                        <button
                            onClick={() => router.push("/")}
                            className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2.5 px-4 rounded-md transition-colors"
                        >
                            Перейти на главную
                        </button>
                    </div>

                    <div className="mt-6 pt-6 border-t border-gray-200">
                        <p className="text-xs text-gray-500">
                            Автоматическое перенаправление через 3 секунды...
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
