"use client";

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Hero from "@/components/Hero";
import FilterBar from "@/components/FilterBar";
import EventCard from "@/components/EventCard";
import { X } from 'lucide-react';

// Static events data (existing events from the site)
// Static events data (imported from web_cinema2/data/movies.ts structure)
const staticEvents = [
  {
    id: "grozovoy-pereval",
    title: "Грозовой перевал",
    image: "/movies_files/s7185.jpg",
    place: "мелодрама, драма",
    time: "19:00",
    age: "18+",
    format: "2D",
    price: 450,
    labels: [{ text: "Премьера" }],
    isStatic: true
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
    labels: [{ text: "Меморандум", icon: "/main_files/memo.svg" }],
    isStatic: true
  },
  {
    id: "ubezhishche",
    title: "Убежище",
    image: "/main_files/p7217.jpg",
    place: "триллер, экшн",
    time: "16:30",
    age: "18+",
    format: "2D",
    price: 650,
    isStatic: true
  },
  {
    id: "zdes-byl-yura",
    title: "Здесь был Юра",
    image: "/main_files/p7210.jpg",
    place: "комедия, драма, музыка",
    time: "16:45",
    age: "18+",
    format: "2D",
    price: 350,
    isStatic: true
  },
  {
    id: "gornichnaya",
    title: "Горничная",
    image: "/main_files/p7167.jpg",
    place: "триллер",
    time: "17:10",
    age: "18+",
    format: "2D",
    price: 430,
    isStatic: true
  },
  {
    id: "schastliv-kogda-ty-net",
    title: "Счастлив, когда ты нет",
    image: "/main_files/p7231.jpg",
    place: "романтическая комедия",
    time: "21:45",
    age: "18+",
    format: "2D",
    price: 750,
    isStatic: true
  },
  {
    id: "greenland-2",
    title: "Гренландия 2: Миграция",
    image: "/main_files/p7200.jpg",
    place: "триллер, экшн",
    time: "21:50",
    age: "18+",
    format: "2D",
    price: 430,
    isStatic: true
  },
  {
    id: "marti-velikolepniy",
    title: "Марти Великолепный",
    image: "/main_files/p7180.jpg",
    place: "комедия, спорт",
    time: "Скоро",
    age: "18+",
    format: "2D",
    price: 0,
    isStatic: true
  },
  {
    id: "skazka-o-tsare-saltane",
    title: "Сказка о царе Салтане",
    image: "/main_files/p7230.jpg",
    place: "фэнтези",
    time: "14:15",
    age: "6+",
    format: "2D",
    price: 650,
    labels: [{ text: "Пушкинская карта" }],
    isStatic: true
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
    labels: [{ text: "То Кино!", icon: "/main_files/tokino.svg" }],
    isStatic: true
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
    labels: [{ text: "То Кино!", icon: "/main_files/tokino.svg" }],
    isStatic: true
  },
  {
    id: "pervaya",
    title: "Первая",
    image: "/main_files/p7229.jpg",
    place: "романтическая драма",
    time: "14:25",
    age: "16+",
    format: "2D",
    price: 650,
    isStatic: true
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
    labels: [{ text: "Фильм недели", icon: "/main_files/fn.svg" }],
    isStatic: true
  },
  {
    id: "titanic",
    title: "Титаник",
    image: "/main_files/p6620.jpg",
    place: "триллер, мелодрама, драма",
    time: "18:45",
    age: "12+",
    format: "2D",
    price: 430,
    labels: [{ text: "То Кино!", icon: "/main_files/tokino.svg" }],
    isStatic: true
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
    labels: [{ text: "Классика" }],
    isStatic: true
  },
  {
    id: "lotr-two-towers",
    title: "Властелин колец: Две крепости",
    image: "/main_files/p7225.jpg",
    place: "фэнтези, приключения",
    time: "16:25",
    age: "16+",
    format: "2D",
    price: 650,
    labels: [{ text: "То Кино!", icon: "/main_files/tokino.svg" }],
    isStatic: true
  },
  {
    id: "omanko-event",
    title: "Специальный показ: OMANKO",
    image: "/main_files/p7232.jpg",
    place: "документальный, мода",
    time: "20:00",
    age: "18+",
    format: "2D",
    price: 1000,
    labels: [{ text: "Спецпоказ" }],
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

function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [databaseEvents, setDatabaseEvents] = useState<DatabaseEvent[]>([]);
  const [loading, setLoading] = useState(false); // Disable loading state
  const [user, setUser] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [showExpiredNotice, setShowExpiredNotice] = useState(false);
  const eventsPerPage = 12;

  useEffect(() => {
    fetchUser();
    // fetchDatabaseEvents(); // Disable theater events fetch

    // Check for expired deposit redirect
    if (searchParams.get('expired') === '1') {
      setShowExpiredNotice(true);
      // Clean URL
      window.history.replaceState({}, '', '/');
      // Auto-hide after 6 seconds
      const timer = setTimeout(() => setShowExpiredNotice(false), 6000);
      return () => clearTimeout(timer);
    }
  }, [searchParams]);

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
    const formatTime = (dateTime: string) => {
      try {
        const date = new Date(dateTime);
        const time = date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        return time;
      } catch {
        return event.formatted_time || '';
      }
    };

    return {
      id: event.id.toString(),
      title: event.title,
      image: event.photo_path ? `/api/events/${event.id}/photo` : '/images/banner.jpeg',
      place: event.venue, // Map venue to place
      time: formatTime(event.date_time),
      age: "16+", // Default or from DB if available
      format: "2D", // Default
      price: event.min_price, // Pass number directly
      isStatic: false,
      isSystem: event.is_system,
      creatorName: event.creator_name
    };
  };

  // Filter events based on search query
  const searchQuery = searchParams.get('q')?.toLowerCase() || '';

  const filteredEvents = staticEvents.filter(event => {
    if (!searchQuery) return true;
    return (
      event.title.toLowerCase().includes(searchQuery) ||
      (event.place && event.place.toLowerCase().includes(searchQuery))
    );
  });

  // Only show database events (no static events)
  const allEvents = filteredEvents; // Use static movie data only

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
    <main className="min-h-screen bg-[#111]">
      {/* Expired deposit notification */}
      {showExpiredNotice && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-red-600 text-white px-6 py-3 rounded-xl shadow-lg flex items-center gap-3 animate-slide-down">
          <span className="text-sm font-medium">Заявка на пополнение истекла. Попробуйте позже.</span>
          <button onClick={() => setShowExpiredNotice(false)} className="hover:bg-white/20 rounded-full p-1 transition-colors">
            <X size={16} />
          </button>
        </div>
      )}

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

export default function Home() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}
