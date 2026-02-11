"use client";

import { useState, useEffect } from 'react';
import Hero from "@/components/Hero";
import FilterBar from "@/components/FilterBar";
import EventCard from "@/components/EventCard";
import { X } from 'lucide-react';

// Static events data (existing events from the site)
const staticEvents = [
  {
    id: "100001",
    title: "Фестиваль науки в КГИК",
    venue: "Краснодарский государственный институт культуры",
    date: "06 Февр",
    time: "пт 11:00",
    price: "от 0 руб.",
    image: "/images/026ce21a706b9829d72e7db9f1df3012-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100002",
    title: "«Миры М.А. Булгакова». К 135-летию со дня рождения...",
    venue: "Школа-лицей при музее Сталинградская битва",
    date: "С 13 Мар.",
    time: "",
    price: "от 350 руб.",
    image: "/images/0e8052455655d9aaca6315f378362cdf-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100003",
    title: "Квиз «Знатоки родного края»",
    venue: "Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы",
    date: "04 Февр",
    time: "ср 14:00",
    price: "от 250 руб.",
    image: "/images/1-jpeg.jpeg",
    isStatic: true
  },
  {
    id: "100004",
    title: "Спектакль «На всякого мудреца...»",
    venue: "Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова",
    date: "04 Февр",
    time: "ср 18:30",
    price: "",
    image: "/images/1572446586138e701da3254e277dd9f0-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100005",
    title: "Диво дивное — слово русское!",
    venue: "Краснодарская краевая детская библиотека им.братьев Игнатовых",
    date: "05 Февр",
    time: "чт 11:00",
    price: "от 0 руб.",
    image: "/images/1f189852c5966a3eb983a78acd54b701-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100006",
    title: "День кубанского кобзаря",
    venue: "Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы",
    date: "05 Февр",
    time: "чт 14:00",
    price: "от 0 руб.",
    image: "/images/26c35e1eecc195b202a606f9728060bb-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100007",
    title: "Спектакль «Доктор Айболит»",
    venue: "Пашковский городской дом культуры г. Краснодара",
    date: "07 Февр",
    time: "сб 14:00",
    price: "от 600 руб.",
    image: "/images/30807229e5a58543550454e83002cc48-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100008",
    title: "Спектакль «Сквозь огонь войны»",
    venue: "Театр защитников Отечества",
    date: "08 Февр",
    time: "вс 17:00",
    price: "",
    image: "/images/3609ed8fe59c2b5c3508e1cd7b4b9874-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100009",
    title: "Опера «Царская невеста»",
    venue: "Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова",
    date: "10 Февр",
    time: "сб 17:00",
    price: "от 400 руб.",
    image: "/images/377fe330d6a08a6b09438ffdcacde5a6-jpeg.jpeg",
    isStatic: true
  },
  {
    id: "100010",
    title: "Спектакль «В стране дорожных знаков»",
    venue: "Краснодарский краевой театр кукол",
    date: "12 Февр",
    time: "чт 11:00",
    price: "от 350 руб.",
    image: "/images/7a79eb8caca34affc0db16180a1cabbe-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100011",
    title: "Концерт «Овеяна славой родная Кубань»",
    venue: "Центральный концертный зал",
    date: "12 Февр",
    time: "чт 14:00",
    price: "",
    image: "/images/7b558d68b9e52db8b7fda34f1c9e13cd-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100012",
    title: "Спектакль «Довойник»",
    venue: "Краснодарский академический театр драмы им. М.Горького",
    date: "15 Февр",
    time: "пт 18:30",
    price: "",
    image: "/images/7c70a2ae3e90ccde8884e252621f4664-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100013",
    title: "Концерт «Песни Победы вместе поем»",
    venue: "Центральный концертный зал",
    date: "14 Февр",
    time: "сб 15:00",
    price: "",
    image: "/images/8fb891bcdc9fa96dad8b2eb96b59c0b6-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100014",
    title: "Концерт «Маленький принц»",
    venue: "Краснодарская филармония им. Г.Ф. Пономаренко",
    date: "14 Февр",
    time: "сб 17:00",
    price: "",
    image: "/images/ba61bc932f041a3a8f03979c52b20272-jpg.jpeg",
    isStatic: true
  },
  {
    id: "100015",
    title: "Спектакль «Ромео и Джульетта»",
    venue: "Краснодарский академический театр драмы им. М.Горького",
    date: "17 Февр",
    time: "пн 19:00",
    price: "",
    image: "/images/c02ad07ab42247ef32be54b05d5599b9-jpg.jpeg",
    isStatic: true
  }
];

interface DatabaseEvent {
  id: number;
  title: string;
  description: string;
  photo_path?: string;
  min_price: number;
  max_price: number;
  date_time: string;
  venue: string;
  is_system: boolean;
  created_by?: number;
  creator_name?: string;
  formatted_date: string;
  formatted_time: string;
  weekday: string;
}

export default function Home() {
  const [databaseEvents, setDatabaseEvents] = useState<DatabaseEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const eventsPerPage = 12; // 3 ряда по 4 события

  useEffect(() => {
    fetchUser();
    fetchDatabaseEvents();
  }, []);

  const fetchUser = async () => {
    try {
      const response = await fetch('/api/me');
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const fetchDatabaseEvents = async () => {
    try {
      const response = await fetch('/api/events', { credentials: 'include' });
      if (response.ok) {
        const events = await response.json();
        setDatabaseEvents(events);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  // Convert database events to EventCard format
  const convertDatabaseEvent = (event: DatabaseEvent) => {
    const formatDate = (dateTime: string) => {
      try {
        const date = new Date(dateTime);
        const day = date.getDate().toString().padStart(2, '0');
        const months = ['Янв', 'Февр', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
        const month = months[date.getMonth()];
        return `${day} ${month}`;
      } catch {
        return event.formatted_date || 'Дата';
      }
    };

    const formatTime = (dateTime: string) => {
      try {
        const date = new Date(dateTime);
        const weekdays = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
        const weekday = weekdays[date.getDay()];
        const time = date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        return `${weekday} ${time}`;
      } catch {
        return event.formatted_time || '';
      }
    };

    return {
      id: event.id.toString(),
      title: event.title,
      venue: event.venue,
      date: formatDate(event.date_time),
      time: formatTime(event.date_time),
      price: `от ${event.min_price.toLocaleString()} руб.`,
      image: event.photo_path ? `/api/events/${event.id}/photo` : '/images/banner.jpeg',
      isStatic: false,
      isSystem: event.is_system,
      creatorName: event.creator_name
    };
  };

  // Only show database events (no static events)
  const allEvents = databaseEvents.map(convertDatabaseEvent);

  // Pagination logic
  const totalPages = Math.ceil(allEvents.length / eventsPerPage);
  const startIndex = (currentPage - 1) * eventsPerPage;
  const endIndex = startIndex + eventsPerPage;
  const currentEvents = allEvents.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <main className="min-h-screen bg-white">
      <Hero />

      <FilterBar />

      <section className="container mx-auto px-4 pb-24">
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
          </div>
        ) : (
          <>


            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-6 gap-y-10">
              {currentEvents.map((event) => (
                <EventCard
                  key={event.id}
                  {...event}
                />
              ))}
            </div>
          </>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-2 mt-16">
            {/* Previous button */}
            {currentPage > 1 && (
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                className="w-auto h-9 px-4 flex items-center justify-center text-gray-400 hover:text-black hover:bg-gray-100 rounded text-sm font-medium transition-colors mr-4"
              >
                Пред.
              </button>
            )}

            {/* Page numbers */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`w-9 h-9 flex items-center justify-center rounded font-bold text-sm transition-colors ${currentPage === pageNum
                    ? 'bg-[#E60000] text-white'
                    : 'text-gray-400 hover:text-black hover:bg-gray-100'
                    }`}
                >
                  {pageNum}
                </button>
              );
            })}

            {/* Show dots if there are more pages */}
            {totalPages > 5 && currentPage < totalPages - 2 && (
              <>
                <span className="text-gray-400 px-2 pb-2">...</span>
                <button
                  onClick={() => handlePageChange(totalPages)}
                  className="w-9 h-9 flex items-center justify-center text-gray-400 hover:text-black hover:bg-gray-100 rounded text-sm transition-colors"
                >
                  {totalPages}
                </button>
              </>
            )}

            {/* Next button */}
            {currentPage < totalPages && (
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                className="w-auto h-9 px-4 flex items-center justify-center text-gray-400 hover:text-black hover:bg-gray-100 rounded text-sm font-medium transition-colors ml-4"
              >
                След.
              </button>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
