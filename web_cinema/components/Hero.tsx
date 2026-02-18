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
            id: "grozovoy-pereval",
            title: "Грозовой перевал",
            image: "/movies_files/s7185.jpg",
            place: "мелодрама, драма",
            time: "19:00",
            age: "18+",
            format: "2D",
            price: 450,
            labels: [{ text: "Премьера" }]
        },
        {
            id: "uvolit-zhoru",
            title: "Уволить Жору",
            image: "/main_files/p7232.jpg",
            place: "комедия",
            time: "14:10",
            age: "16+",
            format: "2D",
            price: 350,
            labels: [{ text: "Меморандум", icon: "/main_files/memo.svg" }]
        },
        {
            id: "ubezhishche",
            title: "Убежище",
            image: "/main_files/p7217.jpg",
            place: "триллер, экшн",
            time: "16:30",
            age: "18+",
            format: "2D",
            price: 650
        },
        {
            id: "zdes-byl-yura",
            title: "Здесь был Юра",
            image: "/main_files/p7210.jpg",
            place: "комедия, драма, музыка",
            time: "16:45",
            age: "18+",
            format: "2D",
            price: 350
        },
        {
            id: "gornichnaya",
            title: "Горничная",
            image: "/main_files/p7167.jpg",
            place: "триллер",
            time: "17:10",
            age: "18+",
            format: "2D",
            price: 430
        },
        {
            id: "schastliv-kogda-ty-net",
            title: "Счастлив, когда ты нет",
            image: "/main_files/p7231.jpg",
            place: "романтическая комедия",
            time: "21:45",
            age: "18+",
            format: "2D",
            price: 750
        },
        {
            id: "greenland-2",
            title: "Гренландия 2: Миграция",
            image: "/main_files/p7200.jpg",
            place: "триллер, экшн",
            time: "21:50",
            age: "18+",
            format: "2D",
            price: 430
        },
        {
            id: "avatar-fire-ash",
            title: "Аватар: Пламя и пепел",
            image: "/main_files/p7013.jpg",
            place: "боевик, триллер, фантастика",
            time: "15:45",
            age: "16+",
            format: "2D",
            price: 1300,
            labels: [{ text: "То Кино!", icon: "/main_files/tokino.svg" }]
        },
        {
            id: "stray-kids",
            title: "Stray Kids: The dominATE Experience",
            image: "/main_files/p7252.jpg",
            place: "музыка, концерт",
            time: "16:10",
            age: "12+",
            format: "2D",
            price: 350,
            labels: [{ text: "То Кино!", icon: "/main_files/tokino.svg" }]
        },
        {
            id: "pervaya",
            title: "Первая",
            image: "/main_files/p7229.jpg",
            place: "романтическая драма",
            time: "14:25",
            age: "16+",
            format: "2D",
            price: 650
        },
        {
            id: "ravioli-oli",
            title: "Равиоли Оли",
            image: "/main_files/p7213.jpg",
            place: "романтическая комедия",
            time: "14:45",
            age: "16+",
            format: "2D",
            price: 200,
            labels: [{ text: "Фильм недели", icon: "/main_files/fn.svg" }]
        },
        {
            id: "lotr-fellowship",
            title: "Властелин колец: Братство Кольца",
            image: "/main_files/p7228.jpg",
            place: "фэнтези, приключения",
            time: "18:00",
            age: "12+",
            format: "IMAX",
            price: 500,
            labels: [{ text: "Классика" }]
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
                    <div key={event.id} className="snap-start w-[300px] md:w-[385px] shrink-0">
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
