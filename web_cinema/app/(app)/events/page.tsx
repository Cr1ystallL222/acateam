'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

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
  created_by?: number;
  creator_name?: string;
  formatted_date: string;
  formatted_time: string;
  weekday: string;
}

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);

  useEffect(() => {
    fetchEvents();
    fetchCurrentUser();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch('/api/me', { credentials: 'include' });
      if (response.ok) {
        const user = await response.json();
        setCurrentUserId(user.telegram_user_id);
      }
    } catch (error) {
      console.error('Error fetching current user:', error);
    }
  };

  const fetchEvents = async () => {
    try {
      const response = await fetch('/api/events?type=cinema');
      if (response.ok) {
        const data = await response.json();
        setEvents(data);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка событий...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Афиша кино</h1>
          <p className="mt-2 text-gray-600">Выберите фильм для бронирования билетов</p>
        </div>
      </div>

      {/* Events Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {events.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎭</div>
            <h3 className="text-xl font-medium text-gray-900 mb-2">Пока нет событий</h3>
            <p className="text-gray-600">События появятся здесь, когда они будут созданы</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((event) => (
              <EventCard key={event.id} event={event} currentUserId={currentUserId} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function EventCard({ event, currentUserId }: { event: Event; currentUserId: number | null }) {
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

  return (
    <Link href={`/events/${event.id}`}>
      <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 overflow-hidden cursor-pointer">
        {/* Event Image */}
        <div className="h-48 bg-gradient-to-br from-orange-400 to-red-500 relative">
          {event.photo_path ? (
            <img
              src={`/api/events/${event.id}/photo`}
              alt={event.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <div className="text-white text-6xl">🎭</div>
            </div>
          )}

          {/* Event Type Badge */}
          <div className="absolute top-3 right-3">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${event.is_system
              ? 'bg-blue-100 text-blue-800'
              : event.created_by === currentUserId
                ? 'bg-green-100 text-green-800'
                : 'bg-purple-100 text-purple-800'
              }`}>
              {event.is_system ? 'Системное' : event.created_by === currentUserId ? 'Мое' : 'Реферское'}
            </span>
          </div>
        </div>

        {/* Event Info */}
        <div className="p-6">
          {/* Date and Time */}
          <div className="flex items-center text-sm text-gray-600 mb-2">
            <div className="flex items-center">
              <span className="font-medium">{event.formatted_date}</span>
              <span className="mx-1">•</span>
              <span>{event.formatted_time}</span>
              <span className="mx-1">•</span>
              <span className="font-medium">{getWeekdayRu(event.weekday)}</span>
            </div>
          </div>

          {/* Title */}
          <h3 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
            {event.title}
          </h3>

          {/* Venue */}
          <p className="text-sm text-gray-600 mb-3 line-clamp-1">
            📍 {event.venue}
          </p>

          {/* Description */}
          <p className="text-gray-700 text-sm mb-4 line-clamp-3">
            {event.description}
          </p>

          {/* Price Range */}
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-lg font-bold text-orange-600">
                {event.min_price.toLocaleString()} - {event.max_price.toLocaleString()} ₽
              </span>
            </div>

            <div className="flex items-center text-orange-600">
              <span className="text-sm font-medium">Выбрать места</span>
              <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>

          {/* Creator Info */}
          {!event.is_system && event.creator_name && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <p className="text-xs text-gray-500">
                Создано: {event.creator_name}
              </p>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}