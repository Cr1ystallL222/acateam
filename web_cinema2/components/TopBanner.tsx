"use client";

import { useState, useEffect } from 'react';

export default function TopBanner() {
    const [isVisible, setIsVisible] = useState(true);
    const [lastScrollY, setLastScrollY] = useState(0);

    useEffect(() => {
        const handleScroll = () => {
            const currentScrollY = window.scrollY;

            // Hide banner after 50px of scroll down
            if (currentScrollY > 50) {
                setIsVisible(false);
            } else {
                setIsVisible(true);
            }

            setLastScrollY(currentScrollY);
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, [lastScrollY]);

    return (
        <div
            className={`w-full bg-black transition-all duration-300 ease-in-out overflow-hidden z-[60] relative ${isVisible ? 'max-h-[80px] opacity-100' : 'max-h-0 opacity-0'
                }`}
        >
            <div className="relative w-full aspect-[1440/80] md:aspect-auto md:h-[80px]">
                <img
                    src="/main_files/r197.jpg"
                    alt="Banner"
                    className="w-full h-full object-cover"
                />
            </div>
        </div>
    );
}
