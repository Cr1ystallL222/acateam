'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';

interface Seat {
  id: number;
  event_id: number;
  row_number: number;
  seat_number: number;
  price: number;
  is_available: boolean;
  reserved_by?: number;
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

  useEffect(() => {
    if (eventId) {
      fetchSeatMap();
    }
  }, [eventId]);

  const fetchSeatMap = async () => {
    try {
      const response = await fetch(`/api/events/${eventId}/seat-map`);
      if (response.ok) {
        const data = await response.json();
        setSeatMapData(data);
      }
    } catch (error) {
      console.error('Error fetching seat map:', error);
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

  if (!seatMapData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h3 className="text-xl font-medium text-gray-900 mb-2">Событие не найдено</h3>
          <Link href="/events" className="text-orange-600 hover:text-orange-700">
            ← Вернуться к списку событий
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
                <Link href="/events" className="hover:text-orange-600">События</Link>
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
              <p className="text-gray-600 mt-1">📍 {event.venue}</p>
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
                <div className="flex justify-between">
                  <span className="text-gray-600">Тип:</span>
                  <span className="font-medium">
                    {event.is_system ? 'Системное событие' : `Создано: ${event.creator_name}`}
                  </span>
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
                <div className="mb-6">
                  {/* Stage */}
                  <div className="text-center mb-8">
                    <div className="inline-block bg-gray-800 text-white px-8 py-2 rounded-full text-sm font-medium">
                      🎭 СЦЕНА
                    </div>
                  </div>

                  {/* Seat Map */}
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {rows.map((row) => (
                      <div key={row.row_number} className="flex items-center">
                        <div className="w-12 text-xs text-gray-600 text-right mr-4">
                          Ряд {row.row_number}
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {row.seats.map((seat) => {
                            const isSelected = selectedSeats.some(s => s.id === seat.id);
                            const priceGroup = price_groups.find(g => g.price === seat.price);
                            
                            return (
                              <button
                                key={seat.id}
                                onClick={() => handleSeatClick(seat)}
                                disabled={!seat.is_available}
                                className={`w-6 h-6 text-xs rounded transition-all ${
                                  !seat.is_available
                                    ? 'bg-gray-300 cursor-not-allowed'
                                    : isSelected
                                    ? 'bg-orange-600 text-white scale-110'
                                    : 'hover:scale-110 text-white'
                                }`}
                                style={{
                                  backgroundColor: !seat.is_available 
                                    ? '#d1d5db' 
                                    : isSelected 
                                    ? '#ea580c' 
                                    : priceGroup?.color || '#6b7280'
                                }}
                                title={`Ряд ${seat.row_number}, Место ${seat.seat_number} - ${seat.price} ₽`}
                              >
                                {seat.seat_number}
                              </button>
                            );
                          })}
                        </div>
                        <div className="ml-4 text-xs text-gray-500">
                          {row.available_count}/{row.total_count}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Legend */}
                  <div className="mt-6 flex items-center justify-center space-x-6 text-xs text-gray-600">
                    <div className="flex items-center">
                      <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
                      <span>Доступно</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-4 h-4 bg-orange-600 rounded mr-2"></div>
                      <span>Выбрано</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-4 h-4 bg-gray-300 rounded mr-2"></div>
                      <span>Занято</span>
                    </div>
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
                            ✕
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="text-lg font-bold">
                      Итого: {getTotalPrice().toLocaleString()} ₽
                    </div>
                    <button className="px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors font-medium">
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