'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { MapPin, Calendar, Clock, Drama, XCircle, X, ChevronDown, ChevronUp, ArrowLeft, ZoomIn, ZoomOut, Maximize } from 'lucide-react';

// ... (inside component)

// Loading spinner is fine as CSS div but maybe could use Loader2 icon
// Static event icon
// <Drama className="w-16 h-16 text-gray-400 mb-4" />

// Event not found
// <XCircle className="w-16 h-16 text-red-400 mb-4" />

// Back link
// <Link href="/" ...> <ArrowLeft className="w-4 h-4 mr-2"/> Вернуться ... </Link>

// Event details
// <MapPin className="w-4 h-4 mr-1" /> {event.venue}

// Close/Remove seat
// <button ...> <X className="w-4 h-4" /> </button>

interface Seat {
  id: number;
  event_id: number;
  row_number: number;
  seat_number: number;
  price: number;
  is_available: boolean;
  reserved_by?: number;
  zone_name?: string;
}

interface Event {
  id: number;
  title: string;
  description: string;
  photo_path?: string;
  min_price: number;
  max_price: number;
  date_time: string;
  venue: string;
  is_system: boolean;
  creator_name?: string;
  formatted_date: string;
  formatted_time: string;
  weekday: string;
  total_seats: number;
  available_seats: number;
  rows: { [key: number]: Seat[] };
}

interface PriceGroup {
  price: number;
  color: string;
  seats: Seat[];
}

interface SeatMapData {
  event: Event;
  rows: Array<{
    row_number: number;
    seats: Seat[];
    available_count: number;
    total_count: number;
  }>;
  price_groups: PriceGroup[];
  total_seats: number;
  available_seats: number;
}

export default function EventPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = params.id as string;

  const [seatMapData, setSeatMapData] = useState<SeatMapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSeats, setSelectedSeats] = useState<Seat[]>([]);
  const [showSeatMap, setShowSeatMap] = useState(false);
  const [isStaticEvent, setIsStaticEvent] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  // Seat Map Zoom & Focus State
  const [zoom, setZoom] = useState(0.6);
  const seatMapRef = useRef<HTMLDivElement>(null);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 2.0));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.4));
  const handleResetZoom = () => setZoom(0.6);

  const focusZone = (zoneName: string) => {
    setZoom(1.0);
    setTimeout(() => {
      const el = document.getElementById(`zone-${zoneName}`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
  };

  // Check authentication first
  useEffect(() => {
    checkAuth();
  }, []);

  // Fetch event data only after auth check passes
  useEffect(() => {
    if (isAuthenticated === true && eventId) {
      fetchEventData();
    }
  }, [isAuthenticated, eventId]);

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/me', { credentials: 'include' });
      if (response.ok) {
        setIsAuthenticated(true);
      } else {
        // Not authenticated - redirect to auth page
        setIsAuthenticated(false);
        router.push('/auth');
      }
    } catch (error) {
      console.error('Error checking auth:', error);
      setIsAuthenticated(false);
      router.push('/auth');
    }
  };

  const fetchEventData = async () => {
    try {
      // Check if it's a static event (ID < 200000)
      // REMOVED: User events have small IDs too. Always try to fetch from API first.
      // const numericId = parseInt(eventId);
      // if (numericId < 100000) { ... }

      // Try to fetch from database events API
      const response = await fetch(`/api/events/${eventId}/seat-map`, { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        setSeatMapData(data);
      } else if (response.status === 401) {
        // Auth expired - redirect to login
        router.push('/auth');
        return;
      } else {
        // If not found in database, it's just not found
        console.warn('Event not found in DB');
      }
    } catch (error) {
      console.error('Error fetching event data:', error);
    } finally {
      setLoading(false);
    }
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

    const seatsData = selectedSeats.map(s => ({
      id: s.id,
      row_number: s.row_number,
      seat_number: s.seat_number,
      price: s.price,
      zone_name: s.zone_name
    }));

    const params = new URLSearchParams({
      event_id: eventId,
      seats: encodeURIComponent(JSON.stringify(seatsData))
    });

    router.push(`/checkout?${params.toString()}`);
  };

  const getWeekdayRu = (weekday: string) => {
    const weekdays: { [key: string]: string } = {
      'Monday': 'ПН',
      'Tuesday': 'ВТ',
      'Wednesday': 'СР',
      'Thursday': 'ЧТ',
      'Friday': 'ПТ',
      'Saturday': 'СБ',
      'Sunday': 'ВС'
    };
    return weekdays[weekday] || weekday;
  };

  // Still checking authentication
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Проверка авторизации...</p>
        </div>
      </div>
    );
  }

  // Not authenticated - will redirect
  if (isAuthenticated === false) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Перенаправление на страницу авторизации...</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка события...</p>
        </div>
      </div>
    );
  }

  // Static event - show placeholder
  if (isStaticEvent) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center text-sm text-gray-600 mb-2">
                  <Link href="/" className="hover:text-orange-600">Главная</Link>
                  <span className="mx-2">→</span>
                  <span>Событие</span>
                </div>
                <h1 className="text-3xl font-bold text-gray-900">Событие #{eventId}</h1>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="flex justify-center mb-4">
              <Drama className="w-16 h-16 text-gray-400" />
            </div>
            <h3 className="text-xl font-medium text-gray-900 mb-4">Статическое событие</h3>
            <p className="text-gray-600 mb-6">
              Это событие из оригинального каталога сайта.
              Бронирование мест пока недоступно.
            </p>
            <Link
              href="/"
              className="inline-flex items-center px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" /> Вернуться к событиям
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!seatMapData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <XCircle className="w-16 h-16 text-red-400" />
          </div>
          <h3 className="text-xl font-medium text-gray-900 mb-2">Событие не найдено</h3>
          <Link href="/" className="text-orange-600 hover:text-orange-700 inline-flex items-center">
            <ArrowLeft className="w-4 h-4 mr-2" /> Вернуться к списку событий
          </Link>
        </div>
      </div>
    );
  }

  const { event, rows, price_groups } = seatMapData;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center text-sm text-gray-600 mb-2">
                <Link href="/" className="hover:text-orange-600">Главная</Link>
                <span className="mx-2">→</span>
                <span>{event.title}</span>
              </div>
              <h1 className="text-3xl font-bold text-gray-900">{event.title}</h1>
              <div className="flex items-center mt-2 text-gray-600">
                <span className="font-medium">{event.formatted_date}</span>
                <span className="mx-2">•</span>
                <span>{event.formatted_time}</span>
                <span className="mx-2">•</span>
                <span className="font-medium">{getWeekdayRu(event.weekday)}</span>
              </div>
              <p className="text-gray-600 mt-1 flex items-center">
                <MapPin className="w-4 h-4 mr-1 text-gray-500" /> {event.venue}
              </p>
            </div>

            <div className="text-right">
              <div className="text-sm text-gray-600">Доступно билетов</div>
              <div className="text-2xl font-bold text-green-600">
                {seatMapData.available_seats}
              </div>
              <div className="text-sm text-gray-500">из {seatMapData.total_seats}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Event Info */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">О событии</h3>
              <p className="text-gray-700 mb-4">{event.description}</p>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Цены:</span>
                  <span className="font-medium">{event.min_price.toLocaleString()} - {event.max_price.toLocaleString()} ₽</span>
                </div>

              </div>
            </div>

            {/* Price Legend */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4">Цены по зонам</h3>
              <div className="space-y-2">
                {price_groups.map((group) => (
                  <div key={group.price} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div
                        className="w-4 h-4 rounded-full mr-3"
                        style={{ backgroundColor: group.color }}
                      ></div>
                      <span className="text-sm">{group.price.toLocaleString()} ₽</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {group.seats.filter(s => s.is_available).length} мест
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Seat Map */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold">Схема зала</h3>
                <button
                  onClick={() => setShowSeatMap(!showSeatMap)}
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                >
                  {showSeatMap ? 'Скрыть схему' : 'Показать схему'}
                </button>
              </div>

              {showSeatMap && (
                <div className="mb-6 bg-white overflow-hidden rounded-lg border border-gray-100 relative">

                  {/* Zoom & Focus Controls */}
                  <div className="absolute right-4 top-4 z-10 flex flex-col gap-2">
                    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-1 flex flex-col">
                      <button onClick={handleZoomIn} className="p-2 hover:bg-gray-100 rounded text-gray-700" title="Увеличить"><ZoomIn className="w-5 h-5" /></button>
                      <button onClick={handleResetZoom} className="p-2 hover:bg-gray-100 rounded text-gray-700" title="Сбросить"><Maximize className="w-5 h-5" /></button>
                      <button onClick={handleZoomOut} className="p-2 hover:bg-gray-100 rounded text-gray-700" title="Уменьшить"><ZoomOut className="w-5 h-5" /></button>
                    </div>

                    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-2 flex flex-col gap-1 mt-2">
                      <span className="text-[10px] uppercase font-bold text-center text-gray-400 mb-1">Зоны</span>
                      {["Партер", "Балкон 1-й ярус", "Балкон 2-й ярус"].map(z => (
                        <button key={z} onClick={() => focusZone(z)} className="text-xs px-2 py-1.5 bg-gray-50 hover:bg-orange-50 hover:text-orange-600 rounded text-left transition-colors border border-transparent hover:border-orange-100">
                          {z.replace('Балкон ', 'Б. ').replace('ярус', 'яр.')}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="w-full overflow-auto pt-10 pb-12 px-2 text-center custom-scrollbar bg-white" style={{ maxHeight: '80vh' }} ref={seatMapRef}>
                    <div style={{ transform: `scale(${zoom})`, transformOrigin: 'top center', transition: 'transform 0.3s ease-out' }}>

                      {["Балкон 2-й ярус", "Балкон 1-й ярус", "Партер"].map((zoneName) => {
                        const zoneRows = rows.filter(r => {
                          const z = r.seats[0]?.zone_name;
                          return z === zoneName || (!z && zoneName === "Партер");
                        });

                        if (zoneRows.length === 0) return null;

                        const sortedRows = [...zoneRows].sort((a, b) => b.row_number - a.row_number);

                        return (
                          <div id={`zone-${zoneName}`} key={zoneName} className="mb-14 last:mb-0 relative" style={{ scrollMarginTop: '100px' }}>
                            <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-8 border-b border-gray-100 pb-2 inline-block px-12">{zoneName}</h4>
                            <div className="space-y-3">
                              {sortedRows.map(row => {
                                const isParterre = zoneName === "Партер";
                                const curveFactor = isParterre ? 0.03 : 0.10;

                                return (
                                  <div key={row.row_number} className="relative h-6 md:h-7 flex items-center justify-center">
                                    <div className="flex items-center justify-center relative w-full">
                                      <span className="absolute left-2 md:left-10 lg:left-1/4 text-[9px] text-gray-300 w-6 text-right font-medium">{row.row_number}</span>

                                      <div className="flex items-center justify-center mx-auto" style={{ minWidth: 'max-content' }}>
                                        {row.seats.map((seat, seatIdx) => {
                                          const center = (row.seats.length - 1) / 2;
                                          const dist = seatIdx - center;
                                          const absDist = Math.abs(dist);
                                          const yOffset = Math.pow(absDist, 2) * -curveFactor;
                                          const rot = -dist * (isParterre ? 1.2 : 2.0);

                                          const isSelected = selectedSeats.some(s => s.id === seat.id);

                                          let bgColor = '#f3f4f6';
                                          let textColor = '#d1d5db';

                                          if (seat.is_available) {
                                            textColor = 'white';
                                            if (isSelected) {
                                              bgColor = '#ea580c';
                                            } else {
                                              if (zoneName.includes('Партер')) bgColor = '#be123c';
                                              else if (zoneName.includes('Балкон 1')) bgColor = '#6b7280';
                                              else bgColor = '#374151';
                                            }
                                          } else {
                                            bgColor = '#e5e7eb';
                                          }

                                          return (
                                            <button
                                              key={seat.id}
                                              onClick={() => handleSeatClick(seat)}
                                              disabled={!seat.is_available}
                                              className={`w-4 md:w-5 h-5 md:h-6 mx-[1px] md:mx-[2px] rounded-[3px] text-[8px] md:text-[9px] flex items-end justify-center pb-1 transition-all shadow-sm font-medium border-b border-black/10
                                                            ${isSelected ? 'z-20 scale-125 ring-2 ring-white shadow-md' : 'z-10 hover:scale-150 hover:z-30 hover:shadow-lg'}
                                                            ${!seat.is_available ? 'cursor-not-allowed text-gray-300' : ''}
                                                        `}
                                              style={{
                                                backgroundColor: bgColor,
                                                color: textColor,
                                                transform: `translateY(${yOffset}px) rotate(${rot}deg)`,
                                                marginTop: `${Math.abs(yOffset)}px`
                                              }}
                                              title={`Ряд ${row.row_number}, Место ${seat.seat_number} (${seat.price}₽)`}
                                            >
                                              {seat.seat_number}
                                            </button>
                                          )
                                        })}
                                      </div>

                                      <span className="absolute right-2 md:right-10 lg:right-1/4 text-[9px] text-gray-300 w-6 text-left font-medium">{row.row_number}</span>
                                    </div>
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        )
                      })}

                      <div className="mt-24 mb-4">
                        <div className="w-1/2 max-w-sm h-16 bg-gray-50 mx-auto rounded-t-[50%] border-t border-gray-200 flex items-end justify-center pb-4 shadow-[inset_0_2px_4px_rgba(0,0,0,0.05)]">
                          <span className="text-[10px] font-bold text-gray-400 tracking-[0.4em] uppercase">Сцена</span>
                        </div>
                      </div>
                    </div>

                  </div>
                  <div className="flex flex-wrap justify-center gap-4 md:gap-8 text-[10px] md:text-xs text-gray-500 border-t border-gray-100 bg-gray-50/50 py-4">
                    <div className="flex items-center"><div className="w-3 h-3 bg-[#be123c] rounded-sm mr-2 shadow-sm"></div>Партер</div>
                    <div className="flex items-center"><div className="w-3 h-3 bg-[#6b7280] rounded-sm mr-2 shadow-sm"></div>Балкон 1</div>
                    <div className="flex items-center"><div className="w-3 h-3 bg-[#374151] rounded-sm mr-2 shadow-sm"></div>Балкон 2</div>
                    <div className="flex items-center"><div className="w-3 h-3 bg-[#e5e7eb] rounded-sm mr-2 shadow-sm"></div>Занято</div>
                    <div className="flex items-center"><div className="w-3 h-3 bg-[#ea580c] rounded-sm mr-2 shadow-sm"></div>Выбрано</div>
                  </div>
                </div>
              )}

              {/* Selected Seats Summary */}
              {selectedSeats.length > 0 && (
                <div className="border-t pt-6">
                  <h4 className="font-semibold mb-4">Выбранные места ({selectedSeats.length})</h4>
                  <div className="space-y-2 mb-4">
                    {selectedSeats.map((seat) => (
                      <div key={seat.id} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                        <span className="text-sm">
                          Ряд {seat.row_number}, Место {seat.seat_number}
                        </span>
                        <div className="flex items-center">
                          <span className="font-medium mr-3">{seat.price.toLocaleString()} ₽</span>
                          <button
                            onClick={() => handleSeatClick(seat)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="text-lg font-bold">
                      Итого: {getTotalPrice().toLocaleString()} ₽
                    </div>
                    <button
                      onClick={handlePurchase}
                      className="px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors font-medium"
                    >
                      Купить билеты
                    </button>
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