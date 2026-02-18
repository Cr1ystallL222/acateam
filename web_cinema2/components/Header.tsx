"use client";

import Link from 'next/link';
import { useState, useEffect } from 'react';

export default function Header() {
    const [top, setTop] = useState(0);

    useEffect(() => {
        const handleScroll = () => {
            const currentScrollY = window.scrollY;
            if (currentScrollY > 50) {
                setTop(0);
            } else {
                // Approximate banner height - could be more dynamic but this is simple
                setTop(Math.max(0, 80 - currentScrollY));
            }
        };

        // Initial set
        handleScroll();

        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <header
            className="fixed left-0 w-full z-50 bg-[#1A1A1A] border-b border-[#333] transition-all duration-300 ease-in-out"
            style={{ top: `${top}px` }}
        >
            <div className="container mx-auto px-4 h-16 flex items-center justify-between relative">

                {/* Mobile: Use order to keep it left. Desktop: Centered absolutely */}
                <div className="flex-1 md:flex-none flex items-center">
                    <Link href="/" className="md:absolute md:left-1/2 md:-translate-x-1/2 md:top-1/2 md:-translate-y-1/2 z-20">
                        <div className="text-2xl font-bold tracking-wider hover:opacity-80 transition-opacity whitespace-nowrap">
                            <span className="text-white">AFISHON</span>
                            <span className="text-[#E60000]">.RU</span>
                        </div>
                    </Link>
                </div>

                {/* Right Side: Auth / User - kept on the right for both */}
                <div className="flex items-center gap-6 ml-auto z-10">
                    <Link href="#" className="flex items-center gap-2 text-white hover:text-[#E60000] transition-colors">
                        <span className="hidden md:inline text-sm font-medium">Личный кабинет</span>
                        <div className="w-8 h-8 rounded-full border border-gray-600 flex items-center justify-center bg-[#222]">
                            <svg className="w-4 h-4 fill-current">
                                <use href="#icon-user" />
                            </svg>
                        </div>
                    </Link>
                </div>
            </div>
        </header>
    );
}
