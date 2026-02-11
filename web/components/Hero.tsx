"use client";

import { motion } from 'framer-motion';
import Link from 'next/link';
import { ChevronRight } from 'lucide-react';

export default function Hero() {
    const cards = [
        {
            id: 1,
            title: "Участникам\nСВО",
            link: "#",
            image: "/images/main_page_svo.jpeg",
            bg: "bg-red-700",
            className: "col-span-1"
        },
        {
            id: 2,
            title: "Пушкинская\nкарта",
            link: "#",
            image: "/images/banner.jpeg",
            bg: "bg-gray-800",
            className: "col-span-1"
        },
        {
            id: 3,
            date: "16 Янв",
            title: "В Новой Третьяковке проходит выставка «Авангард и Икона»",
            link: "#",
            image: "/images/20251224_fl_avant-grade-and-icons_36_rez-jpg.jpeg",
            bg: "bg-orange-800",
            type: "event",
            className: "col-span-1"
        }
    ];

    return (
        <section className="container mx-auto px-4 py-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {cards.map((card, index) => (
                    <motion.div
                        key={card.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1, duration: 0.5 }}
                        className={`relative overflow-hidden rounded-[24px] aspect-[16/9] group cursor-pointer ${card.bg} ${card.className} shadow-sm`}
                    >
                        {/* Background Image */}
                        <div className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-105"
                            style={{ backgroundImage: `url(${card.image})` }}
                        />
                        {/* Gradient Overlay - Only needed for legibility if images are busy, but design shows clear cards. 
                            Adding slight gradient for text readability at bottom/top 
                        */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/30" />

                        <Link href={card.link} className="absolute inset-0 p-8 flex flex-col items-start justify-between text-white z-10 h-full">
                            {card.type === 'event' ? (
                                <>
                                    <div className="bg-white/20 backdrop-blur-md px-3 py-1 rounded-lg text-sm font-semibold">
                                        {card.date}
                                    </div>
                                    <h3 className="text-xl font-bold leading-tight line-clamp-3 mt-auto">
                                        {card.title}
                                    </h3>
                                </>
                            ) : (
                                <>
                                    <h2 className="text-4xl font-bold leading-none tracking-tight mb-2 whitespace-pre-line drop-shadow-md">
                                        {card.title}
                                    </h2>
                                    <span className="text-sm font-medium opacity-90 group-hover:opacity-100 transition-opacity flex items-center gap-1 mt-2">
                                        Подробнее <ChevronRight size={16} />
                                    </span>
                                </>
                            )}
                        </Link>
                    </motion.div>
                ))}
            </div>
        </section>
    );
}
