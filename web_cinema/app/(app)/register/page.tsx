"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function RegisterPage() {
    const router = useRouter();
    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        phone: "+7",
        email: "",
        consent_pd: false,
        consent_marketing: false,
    });
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    // Formatting Russian phone number
    const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        let val = e.target.value.replace(/\D/g, "");
        
        // Ensure it starts with 7 for Russian numbers
        if (val.length === 0) {
            val = "7";
        } else if (val[0] === "8") {
            val = "7" + val.slice(1);
        } else if (val[0] !== "7") {
            val = "7" + val;
        }
        
        // Limit to 11 digits (7 + 10)
        if (val.length > 11) {
            val = val.slice(0, 11);
        }
        
        // Format as +7 (XXX) XXX-XX-XX
        let formatted = "+7";
        if (val.length > 1) {
            formatted += " (" + val.slice(1, 4);
            if (val.length > 4) {
                formatted += ") " + val.slice(4, 7);
                if (val.length > 7) {
                    formatted += "-" + val.slice(7, 9);
                    if (val.length > 9) {
                        formatted += "-" + val.slice(9, 11);
                    }
                }
            }
        }
        
        setFormData({ ...formData, phone: formatted });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!formData.consent_pd) {
            setError("Необходимо согласие на обработку персональных данных");
            return;
        }
        
        if (!formData.first_name || !formData.last_name || !formData.email) {
            setError("Пожалуйста, заполните все обязательные поля");
            return;
        }
        
        // Extract digits from phone for validation
        const phoneDigits = formData.phone.replace(/\D/g, "");
        if (phoneDigits.length !== 11 || !phoneDigits.startsWith("7")) {
            setError("Введите корректный российский номер телефона");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const res = await api.register.draft({
                ...formData,
                phone: phoneDigits // Send clean phone number
            });
            
            // Redirect to Verify stage with session_id
            const query = new URLSearchParams({ 
                session_id: res.session_id, 
                bot_link: res.bot_link 
            });
            router.push(`/register/verify?${query.toString()}`);
        } catch (err: any) {
            setError(err.message || "Ошибка регистрации");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#1A1A1A] py-12 px-4">
            <div className="max-w-md mx-auto">
                <div className="text-center mb-8 pt-10">
                    <h1 className="text-3xl font-bold text-white mb-2">Регистрация</h1>
                    <p className="text-gray-400">Создайте аккаунт для доступа к культурным мероприятиям</p>
                </div>

                <div className="bg-white rounded-lg shadow-md p-6 text-gray-900">
                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                            <p className="text-red-800 text-sm">{error}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Имя <span className="text-red-500">*</span>
                                </label>
                                <input
                                    type="text"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                    value={formData.first_name}
                                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                                    placeholder="Иван"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Фамилия <span className="text-red-500">*</span>
                                </label>
                                <input
                                    type="text"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                    value={formData.last_name}
                                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                                    placeholder="Иванов"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Российский номер телефона <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="tel"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                value={formData.phone}
                                onChange={handlePhoneChange}
                                placeholder="+7 (999) 123-45-67"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Email <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="email"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                placeholder="ivan@example.com"
                                required
                            />
                        </div>

                        <div className="space-y-3 pt-4">
                            <label className="flex items-start gap-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="mt-1 h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                                    checked={formData.consent_pd}
                                    onChange={(e) => setFormData({ ...formData, consent_pd: e.target.checked })}
                                    required
                                />
                                <span className="text-sm text-gray-700">
                                    Я согласен(а) на{" "}
                                    <a href="#" className="text-red-600 hover:text-red-800 underline">
                                        обработку персональных данных
                                    </a>{" "}
                                    <span className="text-red-500">*</span>
                                </span>
                            </label>

                            <label className="flex items-start gap-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="mt-1 h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                                    checked={formData.consent_marketing}
                                    onChange={(e) => setFormData({ ...formData, consent_marketing: e.target.checked })}
                                />
                                <span className="text-sm text-gray-700">
                                    Я согласен(а) на получение информационных рассылок и{" "}
                                    <a href="#" className="text-red-600 hover:text-red-800 underline">
                                        политику конфиденциальности
                                    </a>
                                </span>
                            </label>
                        </div>

                        <button
                            type="submit"
                            className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2.5 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={loading || !formData.consent_pd}
                        >
                            {loading ? "Обработка..." : "Продолжить"}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-gray-600">
                            Уже есть аккаунт?{" "}
                            <a href="/auth/telegram" className="text-red-600 hover:text-red-800 font-medium">
                                Войти
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
