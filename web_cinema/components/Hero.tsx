"use client";

import Image from 'next/image';

export default function Hero() {
    return (
        <section className="relative w-full bg-[#111]">
            <div className="container mx-auto px-4 py-6 md:py-8">
                {/* Mobile: Aspect ratio container to prevent layout shift */}
                <div className="relative w-full aspect-[16/9] md:aspect-[3/1] rounded-2xl overflow-hidden shadow-2xl border border-[#333]">
                    <Image
                        src="/main_files/r197.jpg"
                        alt="Уже в кино"
                        fill
                        className="object-cover"
                        priority
                    />
                    {/* Gradient overlay for better text readability if needed in future */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent md:hidden"></div>

                    <div className="absolute bottom-4 left-4 md:hidden text-white">
                        <h2 className="text-xl font-bold mb-1">Уже в кино</h2>
                        <p className="text-xs text-gray-300">Смотрите новинки проката</p>
                    </div>
                </div>
            </div>
        </section>
    );
}
