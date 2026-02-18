"use client";

import { useRef } from 'react';
import Link from 'next/link';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import EventCard from './EventCard';

export default function Hero() {
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    const scroll = (direction: 'left' | 'right') => {
        if (scrollContainerRef.current) {
            const isMobile = window.innerWidth < 768;
            const scrollAmount = isMobile ? 316 : 401;
            scrollContainerRef.current.scrollBy({
                left: direction === 'left' ? -scrollAmount : scrollAmount,
                behavior: 'smooth'
            });
        }
    };

    const events = [
        {
            id: 1,
            title: "Квиз «Знатоки родного края»",
            place: "Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы",
            image: "/main_files/p7232.jpg",
            price: "от 200 руб.",
            date: "19 Февр",
            day: "Чт",
            time: "14:00"
        },
        {
            id: 2,
            title: "Спектакль «На всякого мудреца...»",
            place: "Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова",
            image: "/main_files/p7217.jpg",
            price: "от 800 руб.",
            date: "20 Февр",
            day: "Пт",
            time: "18:30"
        },
        {
            id: 3,
            title: "Диво дивное — слово русское!",
            place: "Краснодарская краевая детская библиотека им.братьев Игнатовых",
            image: "/main_files/p7210.jpg",
            price: "от 150 руб.",
            date: "18 Февр",
            day: "Ср",
            time: "11:00"
        },
        {
            id: 4,
            title: "День кубанского кобзаря",
            place: "Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы",
            image: "/main_files/p7167.jpg",
            price: "от 200 руб.",
            date: "19 Февр",
            day: "Чт",
            time: "14:00"
        },
        {
            id: 5,
            title: "Фестиваль науки в КГИК",
            place: "Краснодарский государственный институт культуры",
            image: "/main_files/p7231.jpg",
            price: "от 500 руб.",
            date: "20 Февр",
            day: "Пт",
            time: "11:00"
        },
        {
            id: 6,
            title: "Спектакль «Доктор Айболит»",
            place: "Пашковский городской дом культуры г. Краснодара",
            image: "/main_files/p7200.jpg",
            price: "от 400 руб.",
            date: "20 Февр",
            day: "Пт",
            time: "14:00"
        },
        {
            id: 7,
            title: "Спектакль «Сквозь огонь войны»",
            place: "Театр защитников Отечества",
            image: "/main_files/p7180.jpg",
            price: "от 500 руб.",
            date: "18 Февр",
            day: "Ср",
            time: "17:00"
        },
        {
            id: 8,
            title: "Опера «Царская невеста»",
            place: "Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова",
            image: "/main_files/p7230.jpg",
            price: "от 1 000 руб.",
            date: "19 Февр",
            day: "Чт",
            time: "17:00"
        },
        {
            id: 9,
            title: "Спектакль «В стране дорожных знаков»",
            place: "Краснодарский краевой театр кукол",
            image: "/main_files/p7013.jpg",
            price: "от 300 руб.",
            date: "20 Февр",
            day: "Пт",
            time: "11:00"
        },
        {
            id: 10,
            title: "Концерт «Овеяна славой родная Кубань»",
            place: "Центральный концертный зал",
            image: "/main_files/p7252.jpg",
            price: "от 600 руб.",
            date: "18 Февр",
            day: "Ср",
            time: "14:00"
        },
        {
            id: 11,
            title: "Концерт «Песни Победы вместе поем»",
            place: "Центральный концертный зал",
            image: "/main_files/p7229.jpg",
            price: "от 400 руб.",
            date: "20 Февр",
            day: "Пт",
            time: "15:00"
        },
        {
            id: 12,
            title: "Концерт «Маленький принц»",
            place: "Краснодарская филармония им. Г.Ф. Пономаренко",
            image: "/main_files/p6620.jpg",
            price: "от 500 руб.",
            date: "18 Февр",
            day: "Ср",
            time: "17:00"
        }
    ];

    return (
        <section className="container mx-auto px-4 py-8">
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-bold text-white">Театральные события</h1>
                <div className="flex gap-2">
                    <button
                        onClick={() => scroll('left')}
                        className="p-2 rounded-full bg-[#333] hover:bg-[#555] transition-colors cursor-pointer text-white"
                        aria-label="Scroll left"
                    >
                        <ChevronLeft size={24} />
                    </button>
                    <button
                        onClick={() => scroll('right')}
                        className="p-2 rounded-full bg-[#333] hover:bg-[#555] transition-colors cursor-pointer text-white"
                        aria-label="Scroll right"
                    >
                        <ChevronRight size={24} />
                    </button>
                </div>
            </div>

            <div
                ref={scrollContainerRef}
                className="flex gap-4 overflow-x-auto pb-6 scrollbar-hide snap-x scroll-smooth"
                style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
            >
                {events.map((event) => (
                    <div key={event.id} className="snap-start w-[300px] md:w-[385px] shrink-0 h-[550px]">
                        <Link href={`#`} className="block h-full">
                            <EventCard {...event} />
                        </Link>
                    </div>
                ))}
            </div>

            <style jsx global>{`
                .scrollbar-hide::-webkit-scrollbar {
                    display: none;
                }
            `}</style>
        </section>
    );
}
