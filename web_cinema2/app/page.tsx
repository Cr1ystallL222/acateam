'use client';

import Link from 'next/link';
import MovieCard from '@/components/MovieCard';
import { movies } from '@/data/movies';
import { useRef } from 'react';

export default function Home() {
  const dates = [
    { day: "Ср", date: "18", active: true },
    { day: "Чт", date: "19" },
    { day: "Пт", date: "20" },
    { day: "Сб", date: "21" },
    { day: "Вс", date: "22" },
  ];

  const scrollContainerRefNow = useRef<HTMLDivElement>(null);
  const scrollContainerRefSoon = useRef<HTMLDivElement>(null);

  const scroll = (ref: React.RefObject<HTMLDivElement | null>, direction: 'left' | 'right') => {
    if (ref.current) {
      // Card width (300px mobile / 385px desktop) + gap (16px)
      // We can approximate or detect. For simplicity and robustness with the current fixed widths:
      // Mobile: 300 + 16 = 316
      // Desktop: 385 + 16 = 401
      const isMobile = window.innerWidth < 768;
      const scrollAmount = isMobile ? 316 : 401;

      ref.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl md:text-4xl font-bold mb-6">Расписание в Москве</h1>

      {/* Date Filter & Tools */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="flex flex-wrap gap-2">
          {dates.map((d, i) => (
            <Link
              key={i}
              href="#"
              className={`flex flex-col items-center justify-center w-12 h-12 md:w-14 md:h-14 rounded-full border transition-colors ${d.active ? 'bg-[#333] border-[#555] text-white' : 'bg-transparent border-[#333] text-gray-400 hover:border-gray-500'}`}
            >
              <span className="text-[10px] uppercase font-bold">{d.day}</span>
              <span className="text-lg font-bold leading-none">{d.date}</span>
            </Link>
          ))}

          <button className="flex items-center justify-center w-12 h-12 md:w-14 md:h-14 rounded-full border border-[#333] hover:border-gray-500 text-gray-400">
            <svg className="w-5 h-5"><use href="#icon-calendar_reg" /></svg>
          </button>

          <button className="hidden md:flex items-center gap-2 px-6 h-14 rounded-full border border-[#333] hover:border-gray-500 text-gray-400 ml-4">
            <svg className="w-5 h-5"><use href="#icon-filter" /></svg>
            <span>Фильтровать</span>
          </button>
        </div>
      </div>

      {/* Cinema Block - Уже в кино (Now) */}
      <div className="relative group">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-[#2d9cdb]">Уже в кино</h2>
          <div className="flex gap-2">
            <button onClick={() => scroll(scrollContainerRefNow, 'left')} className="p-2 rounded-full bg-[#333] hover:bg-[#555] disabled:opacity-50 transition-colors cursor-pointer z-10">
              <svg className="w-6 h-6 rotate-180 fill-white"><use href="#icon-arrow-right" /></svg>
            </button>
            <button onClick={() => scroll(scrollContainerRefNow, 'right')} className="p-2 rounded-full bg-[#333] hover:bg-[#555] disabled:opacity-50 transition-colors cursor-pointer z-10">
              <svg className="w-6 h-6 fill-white"><use href="#icon-arrow-right" /></svg>
            </button>
          </div>
        </div>

        {/* Horizontal Scroll */}

        <div ref={scrollContainerRefNow} className="flex gap-4 overflow-x-auto pb-6 scrollbar-hide snap-x scroll-smooth">
          {movies.filter(m => m.category === 'now' || m.category === 'love_story' || m.category === 'lotr' || m.category === 'omanko').map((movie) => (
            <div key={movie.id} className="snap-start w-[300px] md:w-[385px] shrink-0">
              <Link href={`/movie/${movie.id}`}>
                <MovieCard {...movie} />
              </Link>
            </div>
          ))}
        </div>

        {/* Fade effect on right */}
        <div className="absolute top-12 right-0 h-[calc(100%-3rem)] w-20 bg-gradient-to-l from-black to-transparent pointer-events-none md:hidden"></div>
      </div>

      {/* Cinema Block - Скоро (Soon) */}
      <div className="relative group">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-[#E60000]">Скоро</h2>
          <div className="flex gap-2">
            <button onClick={() => scroll(scrollContainerRefSoon, 'left')} className="p-2 rounded-full bg-[#333] hover:bg-[#555] disabled:opacity-50 transition-colors cursor-pointer z-10">
              <svg className="w-6 h-6 rotate-180 fill-white"><use href="#icon-arrow-right" /></svg>
            </button>
            <button onClick={() => scroll(scrollContainerRefSoon, 'right')} className="p-2 rounded-full bg-[#333] hover:bg-[#555] disabled:opacity-50 transition-colors cursor-pointer z-10">
              <svg className="w-6 h-6 fill-white"><use href="#icon-arrow-right" /></svg>
            </button>
          </div>
        </div>

        {/* Horizontal Scroll */}

        <div ref={scrollContainerRefSoon} className="flex gap-4 overflow-x-auto pb-6 scrollbar-hide snap-x scroll-smooth">
          {movies.filter(m => m.category === 'soon' || m.category === 'tokino' || m.category === 'pushkin').map((movie) => (
            <div key={movie.id} className="snap-start w-[300px] md:w-[385px] shrink-0">
              <Link href={`/movie/${movie.id}`}>
                <MovieCard {...movie} />
              </Link>
            </div>
          ))}
        </div>

        {/* Fade effect on right */}
        <div className="absolute top-12 right-0 h-[calc(100%-3rem)] w-20 bg-gradient-to-l from-black to-transparent pointer-events-none md:hidden"></div>
      </div>


    </div>
  );
}
