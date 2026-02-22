"use client";

import { useState, useRef, useEffect, useCallback } from 'react';
import { Search, ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useRouter, useSearchParams } from 'next/navigation';

const months = ["ЯНВ", "ФЕВР", "МАРТ", "АПР", "МАЙ", "ИЮН", "ИЮЛ", "АВГ", "СЕНТ", "ОКТ", "НОЯБ", "ДЕК"];
const weekDays = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];

interface DayItem {
    date: Date;
    num: number;
    name: string;
    month: string | null;
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
    const [days, setDays] = useState<DayItem[]>([]);
    const [city, setCity] = useState("");

    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const router = useRouter();
    const searchParams = useSearchParams();
    const [searchTerm, setSearchTerm] = useState(searchParams.get('q') || '');

    // Debounce search update
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            const params = new URLSearchParams(searchParams.toString());
            if (searchTerm) {
                params.set('q', searchTerm);
            } else {
                params.delete('q');
            }
            router.push(`/?${params.toString()}`, { scroll: false });
        }, 500);
        return () => clearTimeout(timeoutId);
    }, [searchTerm, router, searchParams]);

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

        const currentIterDate = new Date(today);

        while (currentIterDate <= endDate) {
            const dayNum = currentIterDate.getDate();
            const weekDayIndex = currentIterDate.getDay();
            const isWeekend = weekDayIndex === 0 || weekDayIndex === 6;

            let monthLabel: string | null = null;

            if (dayNum === 1 || tempDays.length === 0) {
                monthLabel = months[currentIterDate.getMonth()];
            }

            tempDays.push({
                date: new Date(currentIterDate),
                num: dayNum,
                name: weekDays[weekDayIndex],
                month: monthLabel,
                weekend: isWeekend,
                active: tempDays.length === 0
            });

            currentIterDate.setDate(currentIterDate.getDate() + 1);
        }
        setDays(tempDays);
    }, []);

    const [activeIndex, setActiveIndex] = useState(0);

    const handleDateClick = (index: number) => {
        setActiveIndex(index);
    };

    return (
        <section className="container mx-auto px-4 py-8 space-y-6">
            {/* Title + Search */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <h1 className="text-3xl font-bold text-[#171717]">Афиша{city ? ` ${getCityGenitive(city)}` : ""}</h1>

                <div className="w-full md:w-auto relative group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-hover:text-black transition-colors" size={16} />
                    <input
                        type="text"
                        placeholder="Поиск по событиям"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full md:w-[280px] bg-[#F5F5F5] text-black text-sm py-2.5 pl-9 pr-4 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#E60000]"
                    />
                </div>
            </div>

            {/* Date Picker */}
            <div className="flex items-center gap-4 bg-white border border-gray-100 p-2 rounded-xl overflow-x-auto shadow-sm">
                <button className="p-2 text-gray-500 hover:text-black hover:bg-gray-100 rounded-full shrink-0"><ChevronLeft size={20} /></button>
                <button className="p-2 text-gray-500 hover:text-black hover:bg-gray-100 rounded-lg shrink-0"><Calendar size={20} /></button>

                <div className="flex flex-1 items-center gap-1 overflow-x-auto scrollbar-hide px-2 relative" ref={scrollContainerRef}>
                    {days.map((day, i) => (
                        <div key={i} className="flex items-center">
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
        </section>
    );
}

