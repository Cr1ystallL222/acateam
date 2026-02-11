"use client";

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, X, ChevronLeft, ChevronRight, Calendar, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

const categories = [
    "Все", "Выставки", "Концерты", "Спектакли", "Кино", "Обучение", "Встречи", "Экскурсии", "Праздники", "Прочие"
];

const tags = [
    "Для детей", "Участникам СВО", "Выставки Музеев2025", "Ночь искусств", "Бесплатно", "Для молодежи",
    "История", "Литература", "Доступная среда", "Книги", "Музыка"
];

const months = ["ЯНВ", "ФЕВР", "МАРТ", "АПР", "МАЙ", "ИЮН", "ИЮЛ", "АВГ", "СЕНТ", "ОКТ", "НОЯБ", "ДЕК"];
const weekDays = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];

interface DayItem {
    date: Date;
    num: number;
    name: string;
    month: string | null; // Uppercase month name if 1st of month or start
    weekend: boolean;
    active?: boolean;
    disabled?: boolean;
}

// Helper to get genitive form of city name for "Афиша [города]"
function getCityGenitive(city: string): string {
    const genitives: Record<string, string> = {
        "Краснодар": "Краснодара",
        "Москва": "Москвы",
        "Санкт-Петербург": "Санкт-Петербурга",
        "Новосибирск": "Новосибирска",
        "Екатеринбург": "Екатеринбурга",
        "Казань": "Казани",
        "Нижний Новгород": "Нижнего Новгорода",
        "Пермь": "Перми",
        "Самара": "Самары",
        "Ростов-на-Дону": "Ростова-на-Дону",
        "Воронеж": "Воронежа",
        "Волгоград": "Волгограда",
    };
    return genitives[city] || city;
}

export default function FilterBar() {
    const [activeCategory, setActiveCategory] = useState("Все");
    const [activeTag, setActiveTag] = useState("Все");
    const [days, setDays] = useState<DayItem[]>([]);
    const [city, setCity] = useState("Краснодар");
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    // Fetch city from API
    useEffect(() => {
        const fetchCity = async () => {
            try {
                const response = await fetch('/api/events/city-info', {
                    credentials: 'include'
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.city) {
                        setCity(data.city);
                    }
                }
            } catch (error) {
                console.error('Failed to fetch city:', error);
            }
        };
        fetchCity();
    }, []);

    useEffect(() => {
        const tempDays: DayItem[] = [];
        const today = new Date();
        const endDate = new Date();
        endDate.setMonth(today.getMonth() + 3);

        const currentIterDate = new Date(today); // Start from today

        while (currentIterDate <= endDate) {
            const dayNum = currentIterDate.getDate();
            const weekDayIndex = currentIterDate.getDay();
            const isWeekend = weekDayIndex === 0 || weekDayIndex === 6;

            let monthLabel: string | null = null;

            // Show month label if it's the 1st of the month OR the very first day in the list
            if (dayNum === 1 || tempDays.length === 0) {
                monthLabel = months[currentIterDate.getMonth()];
            }

            tempDays.push({
                date: new Date(currentIterDate),
                num: dayNum,
                name: weekDays[weekDayIndex],
                month: monthLabel,
                weekend: isWeekend,
                active: tempDays.length === 0 // Make today active by default
            });

            currentIterDate.setDate(currentIterDate.getDate() + 1);
        }
        setDays(tempDays);
    }, []);

    const [activeIndex, setActiveIndex] = useState(0);

    const handleDateClick = (index: number) => {
        setActiveIndex(index);
        // You would typically filter events here
    };

    return (
        <section className="container mx-auto px-4 py-8 space-y-8">
            {/* Title */}
            <h1 className="text-3xl font-bold text-[#171717]">Афиша {getCityGenitive(city)}</h1>

            {/* Categories */}
            <div className="flex items-center gap-6 overflow-x-auto pb-2 scrollbar-hide">
                {categories.map((cat, idx) => (
                    <button
                        key={cat}
                        onClick={() => setActiveCategory(cat)}
                        className={cn(
                            "text-lg font-medium whitespace-nowrap transition-colors relative pb-1",
                            activeCategory === cat ? "text-[#E60000]" : "text-gray-600 hover:text-black"
                        )}
                    >
                        {cat}
                        {activeCategory === cat && (
                            <motion.div
                                layoutId="underline"
                                className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#E60000]"
                            />
                        )}
                    </button>
                ))}
            </div>

            {/* Filters Row */}
            <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2 bg-[#E60000] text-white px-3 py-1.5 rounded-full text-sm font-medium">
                    <button className="hover:bg-white/20 rounded-full p-0.5 transition-colors"><X size={14} /></button>
                    <span>{city}</span>
                </div>

                {["Все учреждения", "Все места", "Стоимость"].map(label => (
                    <button key={label} className="text-gray-600 hover:text-black text-sm flex items-center gap-1 transition-colors">
                        {label} <ChevronDown size={10} />
                    </button>
                ))}

                <div className="flex items-center gap-3 ml-2">
                    <div className="w-10 h-5 bg-gray-300 rounded-full relative cursor-pointer hover:bg-gray-400 transition-colors">
                        <div className="absolute left-1 top-1 w-3 h-3 bg-white rounded-full shadow-sm"></div>
                    </div>
                    <span className="text-gray-600 text-sm">Пушкинская карта</span>
                </div>

                <div className="ml-auto w-full md:w-auto relative group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-hover:text-black transition-colors" size={16} />
                    <input
                        type="text"
                        placeholder="Поиск по событиям"
                        className="w-full md:w-[240px] bg-[#F5F5F5] text-black text-sm py-2 pl-9 pr-4 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#E60000]"
                    />
                </div>
            </div>

            {/* Date Picker */}
            <div className="flex items-center gap-4 bg-white border border-gray-100 p-2 rounded-xl overflow-x-auto shadow-sm">
                <button className="p-2 text-gray-500 hover:text-black hover:bg-gray-100 rounded-full shrink-0"><ChevronLeft size={20} /></button>
                <button className="p-2 text-gray-500 hover:text-black hover:bg-gray-100 rounded-lg shrink-0"><Calendar size={20} /></button>

                {/* Dynamically Rendered Days */}
                <div className="flex flex-1 items-center gap-1 overflow-x-auto scrollbar-hide px-2 relative" ref={scrollContainerRef}>
                    {days.map((day, i) => (
                        <div key={i} className="flex items-center">
                            {/* Month Label acts as separator, inserted BEFORE the day if it's the start of a month or first item */}
                            {day.month && (
                                <div className="flex flex-col items-start justify-center px-3 border-l border-gray-200 h-8 mx-1">
                                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest leading-none">
                                        {day.month}
                                    </span>
                                </div>
                            )}

                            <div className="relative flex-shrink-0">
                                <button
                                    onClick={() => handleDateClick(i)}
                                    className={cn(
                                        "flex flex-col items-center justify-center w-10 h-12 rounded-lg shrink-0 transition-colors italic relative group",
                                        activeIndex === i ? "text-[#E60000]" : "text-gray-400 hover:text-black",
                                        day.disabled && "opacity-30 cursor-not-allowed"
                                    )}
                                >
                                    <span className={cn("text-lg font-bold leading-none", activeIndex === i && "scale-110")}>{day.num}</span>
                                    <span className={cn("text-[10px] uppercase font-medium", day.weekend ? "text-red-500/70" : "")}>{day.name}</span>
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                <button className="p-2 text-gray-500 hover:text-black hover:bg-gray-100 rounded-full shrink-0"><ChevronRight size={20} /></button>
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-2 text-sm">
                <button
                    onClick={() => setActiveTag("Все")}
                    className={cn(
                        "px-4 py-1.5 rounded-full transition-colors",
                        activeTag === "Все" ? "bg-[#E60000] text-white" : "bg-[#F5F5F5] text-gray-600 hover:bg-gray-200 hover:text-black"
                    )}
                >
                    Все
                </button>
                {tags.map(tag => (
                    <button
                        key={tag}
                        onClick={() => setActiveTag(tag)}
                        className={cn(
                            "px-4 py-1.5 rounded-full transition-colors",
                            activeTag === tag ? "bg-[#E60000] text-white" : "bg-[#F5F5F5] text-gray-600 hover:bg-gray-200 hover:text-black"
                        )}
                    >
                        {tag}
                    </button>
                ))}
                <button className="px-4 py-1.5 rounded-full bg-[#F5F5F5] text-gray-600 hover:bg-gray-200 hover:text-black transition-colors">Еще...</button>
            </div>
        </section>
    );
}
