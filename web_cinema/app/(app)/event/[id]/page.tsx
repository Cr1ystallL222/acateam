'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Clock, Calendar, Info, Tag, MonitorPlay, ZoomIn, ZoomOut, Maximize, X } from 'lucide-react';

interface MovieEvent {
  id: string;
  title: string;
  image: string;
  place: string;
  time: string;
  age: string;
  format: string;
  price: number;
  labels?: { text: string; icon?: string }[];
  isStatic: boolean;
}

const staticEvents: MovieEvent[] = [
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

interface Seat {
  id: number;
  row_number: number;
  seat_number: number;
  price: number;
  is_available: boolean;
  zone_name: string;
}

const generateSeats = (eventId: string, minPrice: number) => {
  let hash = 0;
  for (let i = 0; i < eventId.length; i++) {
    hash = eventId.charCodeAt(i) + ((hash << 5) - hash);
  }

  const pseudoRandom = (seed: number) => {
    let t = seed += 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };

  const numRows = 10 + Math.floor(pseudoRandom(hash) * 5); // 10 to 14

  const rows: { row_number: number; seats: Seat[] }[] = [];
  let seatIdCounter = 1;
  const rowStartCount = 6 + Math.floor(pseudoRandom(hash + 1) * 4); // 6 to 9
  const rowEndCount = 18 + Math.floor(pseudoRandom(hash + 2) * 3); // 18 to 20

  const increaseStep = (rowEndCount - rowStartCount) / (numRows - 1);
  let availableCount = 0;
  let totalCount = 0;

  for (let row = 1; row <= numRows; row++) {
    let seatsInThisRow = Math.round(rowStartCount + increaseStep * (row - 1));
    if (seatsInThisRow > 20) seatsInThisRow = 20;

    let zoneName = "Партер";
    let rowPrice = minPrice;
    if (row > numRows * 0.5) {
      zoneName = "Амфитеатр";
      rowPrice = minPrice * 0.85;
    }
    rowPrice = Math.round(rowPrice / 10) * 10;

    const rowSeats: Seat[] = [];
    for (let seatNum = 1; seatNum <= seatsInThisRow; seatNum++) {
      const isBooked = pseudoRandom(hash + row * 100 + seatNum) < 0.3;
      rowSeats.push({
        id: seatIdCounter++,
        row_number: row,
        seat_number: seatNum,
        price: rowPrice,
        is_available: !isBooked,
        zone_name: zoneName
      });
      totalCount++;
      if (!isBooked) availableCount++;
    }

    rows.push({ row_number: row, seats: rowSeats });
  }

  return { rows, availableCount, totalCount };
};

export default function EventPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = params.id as string;

  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [showSeatMap, setShowSeatMap] = useState(false);
  const [selectedSeats, setSelectedSeats] = useState<Seat[]>([]);
  const [seatData, setSeatData] = useState<{ rows: { row_number: number, seats: Seat[] }[], availableCount: number, totalCount: number } | null>(null);
  const [userBalance, setUserBalance] = useState<number>(0);

  const seatMapRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1.0);

  const event = staticEvents.find(e => e.id === eventId);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/me', { credentials: 'include' });
      if (response.ok) {
        const userData = await response.json();
        setUserBalance(userData.balance || 0);
        setIsAuthenticated(true);
      } else {
        router.push('/register');
      }
    } catch (error) {
      router.push('/register');
    }
  };

  useEffect(() => {
    if (isAuthenticated && event) {
      const data = generateSeats(eventId, event.price || 500);
      setSeatData(data);
    }
  }, [isAuthenticated, event, eventId]);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 2.0));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.4));
  const handleResetZoom = () => setZoom(1.0);

  const focusZone = (zoneName: string) => {
    setZoom(1.1);
    setTimeout(() => {
      const el = document.getElementById(`zone-${zoneName}`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
  };

  const handleSeatClick = (seat: Seat) => {
    if (!seat.is_available) return;

    const isSelected = selectedSeats.some(s => s.id === seat.id);
    if (isSelected) {
      setSelectedSeats(selectedSeats.filter(s => s.id !== seat.id));
    } else {
      setSelectedSeats([...selectedSeats, seat]);
    }
  };

  const getTotalPrice = () => {
    return selectedSeats.reduce((total, seat) => total + seat.price, 0);
  };

  const handlePurchase = () => {
    if (selectedSeats.length === 0) return;

    // Check balance
    if (userBalance < getTotalPrice()) {
      router.push('/topup');
      return;
    }

    const seatsData = selectedSeats.map(s => ({
      id: s.id,
      row_number: s.row_number,
      seat_number: s.seat_number,
      price: s.price,
      zone_name: s.zone_name
    }));

    const paramsStr = new URLSearchParams({
      event_id: eventId,
      seats: encodeURIComponent(JSON.stringify(seatsData))
    });

    router.push(`/checkout?${paramsStr.toString()}`);
  };

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-[#111] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#E60000] mx-auto"></div>
          <p className="mt-4 text-gray-400">Проверка доступа...</p>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="min-h-screen bg-[#111] flex items-center justify-center text-white text-center px-4">
        <div>
          <h1 className="text-4xl font-bold mb-4">Фильм не найден</h1>
          <p className="text-gray-400 mb-8">Возможно, он был удален или вы перешли по неверной ссылке.</p>
          <Link href="/" className="inline-flex items-center text-[#E60000] hover:text-red-500 transition-colors">
            <ArrowLeft className="w-5 h-5 mr-2" /> На главную
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#111] text-white">
      {/* Hero Header with Movie Background */}
      <div className="relative w-full h-[50vh] min-h-[400px] flex items-end pb-12">
        {/* Background Image & Overlay */}
        <div className="absolute inset-0 z-0">
          <img
            src={event.image}
            alt={event.title}
            className="w-full h-full object-cover opacity-30"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#111] via-[#111]/80 to-transparent" />
        </div>

        {/* Content Container */}
        <div className="container mx-auto px-4 relative z-10">
          <Link href="/" className="inline-flex items-center text-gray-300 hover:text-white transition-colors mb-8 bg-black/40 px-4 py-2 rounded-full backdrop-blur-md border border-white/10 w-fit">
            <ArrowLeft className="w-4 h-4 mr-2" /> Все события
          </Link>

          <div className="flex flex-col md:flex-row gap-8 items-end">
            <div className="w-[180px] shrink-0 rounded-xl overflow-hidden shadow-2xl shadow-black/50 border border-white/10 hidden md:block">
              <img src={event.image} alt={event.title} className="w-full h-auto object-cover" />
            </div>

            <div className="flex-1">
              {event.labels && event.labels.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {event.labels.map((label, i) => (
                    <span key={i} className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider bg-[#E60000] text-white px-3 py-1 rounded-sm">
                      {label.icon && <img src={label.icon} alt="" className="w-3.5 h-3.5 brightness-0 invert" />}
                      {label.text}
                    </span>
                  ))}
                </div>
              )}
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 leading-tight">{event.title}</h1>

              <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-gray-300">
                <div className="flex items-center gap-2">
                  <Tag className="w-4 h-4 text-[#E60000]" />
                  <span className="capitalize">{event.place}</span>
                </div>
                <div className="flex items-center gap-2">
                  <MonitorPlay className="w-4 h-4 text-[#E60000]" />
                  <span>{event.format}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="border border-gray-500 rounded-sm px-1.5 py-0.5 text-xs font-bold text-gray-400">
                    {event.age}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Details Section */}
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">

          {/* Main Info */}
          <div className="md:col-span-2 space-y-8">
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <Info className="w-6 h-6 text-[#E60000]" /> Описание
              </h2>
              <p className="text-gray-300 leading-relaxed text-lg">
                Погрузитесь в атмосферу этого удивительного фильма на большом экране кинотеатра.
                Вас ждет непревзойденное качество изображения и звука.
                Встречайте главных героев и переживайте вместе с ними каждую минуту захватывающего сюжета.
              </p>
            </section>

            <section className="bg-[#1A1A1A] rounded-2xl p-6 border border-white/5">
              <h3 className="text-xl font-bold mb-6">Сеанс</h3>
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-[#222] rounded-xl p-4 border border-[#333]">
                  <div className="text-sm text-gray-400 mb-1 flex items-center gap-1.5">
                    <Calendar className="w-4 h-4" /> Дата
                  </div>
                  <div className="text-lg font-medium">Сегодня</div>
                </div>
                <div className="bg-[#222] rounded-xl p-4 border border-[#333]">
                  <div className="text-sm text-gray-400 mb-1 flex items-center gap-1.5">
                    <Clock className="w-4 h-4" /> Время
                  </div>
                  <div className="text-lg font-medium">{event.time}</div>
                </div>
              </div>
            </section>

            {/* Seat Map Area */}
            {showSeatMap && seatData && (
              <section className="bg-[#1A1A1A] rounded-2xl p-6 border border-white/5" id="seat-map-section">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold">Выбор мест</h3>
                  <div className="flex items-center gap-2">
                    <button onClick={handleZoomOut} className="p-1.5 bg-[#222] hover:bg-[#333] rounded text-gray-400"><ZoomOut className="w-4 h-4" /></button>
                    <button onClick={handleResetZoom} className="p-1.5 bg-[#222] hover:bg-[#333] rounded text-gray-400"><Maximize className="w-4 h-4" /></button>
                    <button onClick={handleZoomIn} className="p-1.5 bg-[#222] hover:bg-[#333] rounded text-gray-400"><ZoomIn className="w-4 h-4" /></button>
                  </div>
                </div>

                <div className="mb-4 flex flex-wrap gap-2 text-xs">
                  {["Партер", "Амфитеатр"].map(z => (
                    <button key={z} onClick={() => focusZone(z)} className="px-3 py-1.5 bg-[#222] hover:bg-[#333] border border-white/5 rounded-full transition-colors">
                      {z}
                    </button>
                  ))}
                </div>

                <div className="w-full overflow-auto pt-6 pb-12 px-2 text-center bg-[#111] rounded-xl border border-white/5" style={{ maxHeight: '600px' }} ref={seatMapRef}>
                  <div style={{ transform: `scale(${zoom})`, transformOrigin: 'top center', transition: 'transform 0.3s ease-out' }}>

                    <div className="mb-12">
                      <div className="w-3/4 max-w-md h-8 bg-gradient-to-t from-white/10 to-transparent mx-auto rounded-t-[100%] flex items-end justify-center pb-2 shadow-[0_-4px_10px_rgba(255,255,255,0.02)]">
                        <span className="text-[10px] font-bold text-gray-400 tracking-[0.4em] uppercase">Экран</span>
                      </div>
                    </div>

                    {["Партер", "Амфитеатр"].map((zoneName) => {
                      const zoneRows = seatData.rows.filter(r => r.seats[0]?.zone_name === zoneName);
                      if (zoneRows.length === 0) return null;

                      return (
                        <div id={`zone-${zoneName}`} key={zoneName} className="mb-10 last:mb-0 relative" style={{ scrollMarginTop: '100px' }}>
                          <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-4 border-b border-gray-800 pb-2 inline-block px-12">{zoneName}</h4>
                          <div className="space-y-2">
                            {zoneRows.map(row => {
                              const curveFactor = 0.05;
                              return (
                                <div key={row.row_number} className="relative h-6 md:h-7 flex items-center justify-center">
                                  <div className="flex items-center justify-center relative w-full">
                                    <span className="absolute left-0 md:left-4 lg:left-12 text-[9px] text-gray-500 w-6 text-right font-medium">{row.row_number}</span>

                                    <div className="flex items-center justify-center mx-auto" style={{ minWidth: 'max-content' }}>
                                      {row.seats.map((seat, seatIdx) => {
                                        const center = (row.seats.length - 1) / 2;
                                        const dist = seatIdx - center;
                                        const absDist = Math.abs(dist);
                                        const yOffset = Math.pow(absDist, 2) * -curveFactor;
                                        const rot = -dist * 1.5;

                                        const isSelected = selectedSeats.some(s => s.id === seat.id);

                                        let bgColor = '#333';
                                        let textColor = '#888';

                                        if (seat.is_available) {
                                          textColor = 'white';
                                          if (isSelected) {
                                            bgColor = '#E60000';
                                          } else {
                                            if (zoneName === 'Партер') bgColor = '#4f46e5';
                                            else bgColor = '#059669';
                                          }
                                        } else {
                                          bgColor = '#222';
                                          textColor = '#444';
                                        }

                                        return (
                                          <button
                                            key={seat.id}
                                            onClick={() => handleSeatClick(seat)}
                                            disabled={!seat.is_available}
                                            className={`w-5 h-5 md:w-6 md:h-6 mx-[2px] rounded-t-lg rounded-b-sm text-[9px] flex items-center justify-center transition-all border-b-2 border-black/30
                                                            ${isSelected ? 'z-20 scale-125 ring-2 ring-white shadow-[0_0_10px_rgba(230,0,0,0.5)]' : 'z-10 hover:scale-125 hover:z-30'}
                                                            ${!seat.is_available ? 'cursor-not-allowed opacity-50' : ''}
                                                        `}
                                            style={{
                                              backgroundColor: bgColor,
                                              color: textColor,
                                              transform: `translateY(${yOffset}px) rotate(${rot}deg)`,
                                              marginTop: `${Math.abs(yOffset)}px`
                                            }}
                                            title={`${zoneName}, Ряд ${row.row_number}, Место ${seat.seat_number} (${seat.price}₽)`}
                                          >
                                            {seat.seat_number}
                                          </button>
                                        )
                                      })}
                                    </div>
                                    <span className="absolute right-0 md:right-4 lg:right-12 text-[9px] text-gray-500 w-6 text-left font-medium">{row.row_number}</span>
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                <div className="flex flex-wrap justify-center gap-4 text-xs text-gray-400 mt-6 pt-6 border-t border-white/5">
                  <div className="flex items-center"><div className="w-3 h-3 bg-[#4f46e5] rounded-sm mr-2"></div>Партер</div>
                  <div className="flex items-center"><div className="w-3 h-3 bg-[#059669] rounded-sm mr-2"></div>Амфитеатр</div>
                  <div className="flex items-center"><div className="w-3 h-3 bg-[#222] border border-[#333] rounded-sm mr-2"></div>Занято</div>
                  <div className="flex items-center"><div className="w-3 h-3 bg-[#E60000] rounded-sm mr-2 shadow-[0_0_5px_rgba(230,0,0,0.5)]"></div>Ваш выбор</div>
                </div>
              </section>
            )}

          </div>

          {/* Action Card */}
          <div className="md:col-span-1">
            <div className="sticky top-24 bg-[#1A1A1A] rounded-2xl p-6 border border-white/5 shadow-xl">
              <div className="text-center mb-6">
                <p className="text-gray-400 text-sm mb-1">Стоимость билетов от</p>
                <div className="text-4xl font-bold text-white">
                  {event.price === 0 ? "Бесплатно" : `${event.price} ₽`}
                </div>
              </div>

              {!showSeatMap ? (
                <button
                  onClick={() => {
                    setShowSeatMap(true);
                    setTimeout(() => {
                      document.getElementById('seat-map-section')?.scrollIntoView({ behavior: 'smooth' });
                    }, 100);
                  }}
                  className="w-full bg-[#E60000] hover:bg-red-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-red-500/30 hover:shadow-red-500/50 hover:-translate-y-1"
                >
                  Купить билет
                </button>
              ) : selectedSeats.length === 0 ? (
                <div className="text-center p-4 bg-white/5 rounded-xl border border-white/10">
                  <p className="text-gray-300">Выберите места на схеме зала</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="max-h-[200px] overflow-y-auto pr-2 custom-scrollbar space-y-2">
                    {selectedSeats.map(seat => (
                      <div key={seat.id} className="flex items-center justify-between text-sm bg-white/5 p-2 rounded">
                        <div>
                          <span className="text-gray-400 text-xs block">{seat.zone_name}</span>
                          Ряд {seat.row_number}, Место {seat.seat_number}
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-bold">{seat.price} ₽</span>
                          <button onClick={() => handleSeatClick(seat)} className="text-red-500 hover:text-red-400">
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="border-t border-white/10 pt-4 text-center">
                    <p className="text-gray-400 mb-1">К оплате:</p>
                    <p className="text-3xl font-bold mb-4">{getTotalPrice().toLocaleString()} ₽</p>

                    <button
                      onClick={handlePurchase}
                      className="w-full bg-[#E60000] hover:bg-red-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-red-500/30 hover:shadow-red-500/50 hover:-translate-y-1 flex items-center justify-center gap-2"
                    >
                      Купить билеты
                    </button>
                    {userBalance < getTotalPrice() && (
                      <p className="text-yellow-500 text-xs mt-3">
                        На вашем балансе недостаточно средств ({userBalance} ₽).
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}