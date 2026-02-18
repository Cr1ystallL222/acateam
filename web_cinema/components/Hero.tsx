"use client";


import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { ChevronLeft, ChevronRight, Play, Info } from 'lucide-react';

export default function Hero() {
    // Import movies data dynamically or define here if import fails in next step
    const movies = [
        {
            id: 1,
            title: "Дюна: Часть вторая",
            description: "Пол Атрейдес объединяется с Чани и фрименами...",
            image: "/images/banner.jpeg", // Using existing placeholder for now
            rating: 8.7,
            year: 2024,
            genre: "Фантастика",
            duration: "2ч 46мин"
        },
        {
            id: 2,
            title: "Оппенгеймер",
            description: "История жизни американского физика...",
            image: "/images/banner.jpeg",
            rating: 8.4,
            year: 2023,
            genre: "Биография",
            duration: "3ч 00мин"
        },
        {
            id: 3,
            title: "Бедные-несчастные",
            description: "Из-за жестокого мужа Белла Бакстер...",
            image: "/images/banner.jpeg",
            rating: 7.9,
            year: 2023,
            genre: "Драма",
            duration: "2ч 21мин"
        }
    ];

    return (
        <section className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-6 text-white">Сейчас в кино</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {movies.map((movie, index) => (
                    <motion.div
                        key={movie.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1, duration: 0.5 }}
                        className="relative overflow-hidden rounded-[24px] aspect-[2/3] group cursor-pointer bg-neutral-900 shadow-lg border border-neutral-800"
                    >
                        {/* Background Image */}
                        <div className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-105 opacity-60 group-hover:opacity-80"
                            style={{ backgroundImage: `url(${movie.image})` }}
                        />

                        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />

                        <Link href={`#`} className="absolute inset-0 p-6 flex flex-col justify-end text-white z-10 h-full">
                            <div className="transform transition-transform duration-300 group-hover:-translate-y-2">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="bg-red-600 text-white text-xs font-bold px-2 py-0.5 rounded">
                                        {movie.rating}
                                    </span>
                                    <span className="text-gray-300 text-xs">
                                        {movie.year}, {movie.genre}
                                    </span>
                                </div>
                                <h3 className="text-xl font-bold leading-tight mb-2">
                                    {movie.title}
                                </h3>
                                <p className="text-sm text-gray-400 line-clamp-2 mb-4 group-hover:text-gray-300 transition-colors">
                                    {movie.description}
                                </p>
                                <span className="inline-flex items-center gap-1 text-sm font-medium text-red-500 group-hover:text-red-400 transition-colors">
                                    Купить билет <ChevronRight size={16} />
                                </span>
                            </div>
                        </Link>
                    </motion.div>
                ))}
            </div>
        </section>
    );
}
