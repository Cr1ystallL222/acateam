"use client";

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

export default function Header() {
    const { user, loading, refreshUser } = useAuth();
    const router = useRouter();
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    // Close menu on click outside
    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
                setMenuOpen(false);
            }
        }
        if (menuOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [menuOpen]);

    const handleLogout = async () => {
        try {
            setMenuOpen(false);
            await refreshUser();
            router.push('/');
        } catch (error) {
            console.error('Logout error:', error);
        }
    };

    return (
        <header className="sticky top-0 z-50 bg-[#2E2E2E] text-white py-4 shadow-md backdrop-blur-md bg-opacity-95">
            <div className="container mx-auto px-4 relative flex items-center justify-start md:justify-center h-14">
                {/* Logo */}
                <Link href="/" className="flex items-center gap-1 font-bold tracking-widest hover:opacity-90 transition-opacity">
                    <span className="uppercase text-white text-3xl">AFISHON</span>
                    <span className="text-[#E60000] text-3xl">.RU</span>
                </Link>

                {/* Auth Actions */}
                <div className="absolute right-4 flex items-center gap-3">
                    {loading ? (
                        <div className="text-gray-400 text-sm hidden sm:block">Загрузка...</div>
                    ) : user ? (
                        <div className="relative" ref={menuRef}>
                            <button
                                onClick={() => setMenuOpen(!menuOpen)}
                                className="flex items-center gap-3 hover:opacity-80 transition-opacity py-2"
                            >
                                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-white/20 to-white/5 flex items-center justify-center border border-white/10 shadow-sm shrink-0">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white/90">
                                        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
                                        <circle cx="12" cy="7" r="4" />
                                    </svg>
                                </div>
                                <span className="text-sm font-medium text-white hidden sm:block">
                                    {user.first_name || user.display_name}
                                </span>
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`text-gray-400 hidden sm:block transition-transform duration-200 ${menuOpen ? 'rotate-180' : ''}`}>
                                    <path d="m6 9 6 6 6-6" />
                                </svg>
                            </button>

                            {/* Dropdown */}
                            {menuOpen && (
                                <div className="absolute right-0 top-full pt-2 w-64 animate-in fade-in slide-in-from-top-2 duration-200 transform origin-top-right">
                                    <div className="bg-[#1A1A1A]/90 backdrop-blur-md border border-white/10 rounded-xl shadow-2xl overflow-hidden p-4 space-y-4">
                                        {/* Balance Card */}
                                        <div className="bg-gradient-to-br from-white/10 to-transparent p-3 rounded-lg border border-white/5">
                                            <div className="text-xs text-gray-400 mb-1">Ваш баланс</div>
                                            <div className="text-xl font-bold text-white tracking-tight">
                                                {(user.balance || 0).toLocaleString('ru-RU')} ₽
                                            </div>
                                        </div>

                                        {/* Actions */}
                                        <div className="space-y-2">
                                            <Link
                                                href="/topup"
                                                onClick={() => setMenuOpen(false)}
                                                className="w-full bg-[#E60000] hover:bg-red-600 text-white text-sm font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <path d="M5 12h14" />
                                                    <path d="M12 5v14" />
                                                </svg>
                                                Пополнить
                                            </Link>

                                            <Link
                                                href="/coupons"
                                                onClick={() => setMenuOpen(false)}
                                                className="w-full bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-sm font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z" />
                                                    <path d="M13 5v2" /><path d="M13 17v2" /><path d="M13 11v2" />
                                                </svg>
                                                Промокод
                                            </Link>

                                            <button
                                                onClick={handleLogout}
                                                className="w-full bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-sm font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                                    <path d="M16 17l5-5-5-5" />
                                                    <path d="M21 12H9" />
                                                </svg>
                                                Выйти
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="flex items-center gap-3">
                            <Link
                                href="/auth/telegram"
                                className="text-sm text-gray-300 hover:text-white transition-colors px-3 py-1.5 border border-gray-600 rounded hover:border-gray-500"
                            >
                                Вход
                            </Link>
                            <Link
                                href="/register"
                                className="text-sm bg-[#E60000] hover:bg-red-700 text-white px-3 py-1.5 rounded transition-colors"
                            >
                                Регистрация
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
