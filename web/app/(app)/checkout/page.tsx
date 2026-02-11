'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Ticket, AlertCircle, Loader2, MessageCircle, Wallet } from 'lucide-react';

interface SelectedSeat {
    id: number;
    row_number: number;
    seat_number: number;
    price: number;
    zone_name?: string;
}

interface EventInfo {
    id: number;
    title: string;
    formatted_date: string;
    formatted_time: string;
    venue: string;
}

type CheckoutState = 'preview' | 'processing' | 'error';

export default function CheckoutPage() {
    const router = useRouter();
    const searchParams = useSearchParams();

    const [state, setState] = useState<CheckoutState>('preview');
    const [seats, setSeats] = useState<SelectedSeat[]>([]);
    const [eventInfo, setEventInfo] = useState<EventInfo | null>(null);
    const [userBalance, setUserBalance] = useState<number>(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadCheckoutData();
    }, []);

    const loadCheckoutData = async () => {
        try {
            // Get seats from URL params
            const seatsParam = searchParams.get('seats');
            const eventId = searchParams.get('event_id');

            if (!seatsParam || !eventId) {
                router.push('/');
                return;
            }

            const parsedSeats = JSON.parse(decodeURIComponent(seatsParam));
            setSeats(parsedSeats);

            // Fetch event info
            const eventResponse = await fetch(`/api/events/${eventId}`, { credentials: 'include' });
            if (eventResponse.ok) {
                const eventData = await eventResponse.json();
                setEventInfo(eventData);
            }

            // Fetch user balance
            const meResponse = await fetch('/api/me', { credentials: 'include' });
            if (meResponse.ok) {
                const userData = await meResponse.json();
                setUserBalance(userData.balance || 0);
            } else {
                router.push('/auth');
                return;
            }
        } catch (error) {
            console.error('Error loading checkout data:', error);
            router.push('/');
        } finally {
            setLoading(false);
        }
    };

    const getTotalPrice = () => {
        return seats.reduce((total, seat) => total + seat.price, 0);
    };

    const handleCancel = () => {
        router.push('/');
    };

    const handlePurchase = () => {
        // Check balance
        if (userBalance < getTotalPrice()) {
            router.push('/topup');
            return;
        }

        setState('processing');

        // After 12 seconds, show error
        setTimeout(() => {
            setState('error');
        }, 12000);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Загрузка...</p>
                </div>
            </div>
        );
    }

    // Processing state - spinner
    if (state === 'processing') {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center max-w-md mx-auto px-4">
                    <div className="bg-white rounded-2xl shadow-lg p-8">
                        <Loader2 className="w-16 h-16 text-orange-500 animate-spin mx-auto mb-6" />
                        <h2 className="text-2xl font-bold text-gray-900 mb-3">
                            Генерируем билет...
                        </h2>
                        <p className="text-gray-600 mb-4">
                            Пожалуйста, не закрывайте страницу. Это может занять несколько секунд.
                        </p>
                        <div className="flex justify-center space-x-1">
                            <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Error state
    if (state === 'error') {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center max-w-md mx-auto px-4">
                    <div className="bg-white rounded-2xl shadow-lg p-8">
                        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <AlertCircle className="w-10 h-10 text-red-500" />
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-3">
                            Ошибка при генерации билета
                        </h2>
                        <p className="text-gray-600 mb-6">
                            К сожалению, произошла ошибка при обработке вашего заказа.
                            Пожалуйста, обратитесь в службу поддержки для решения проблемы.
                        </p>
                        <div className="space-y-3">
                            <Link
                                href="/"
                                className="w-full inline-flex items-center justify-center px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors font-medium"
                            >
                                Вернуться на главную
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Preview state
    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow-sm">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="flex items-center">
                        <button
                            onClick={handleCancel}
                            className="mr-4 p-2 hover:bg-gray-100 rounded-full transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5 text-gray-600" />
                        </button>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Оформление заказа</h1>
                            <p className="text-sm text-gray-600 mt-1">Проверьте детали перед покупкой</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Event Info */}
                {eventInfo && (
                    <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-2">{eventInfo.title}</h2>
                        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                            <span>{eventInfo.formatted_date}</span>
                            <span>•</span>
                            <span>{eventInfo.formatted_time}</span>
                            <span>•</span>
                            <span>{eventInfo.venue}</span>
                        </div>
                    </div>
                )}

                {/* Selected Tickets */}
                <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
                    <div className="flex items-center mb-4">
                        <Ticket className="w-5 h-5 text-orange-500 mr-2" />
                        <h3 className="text-lg font-semibold text-gray-900">
                            Выбранные билеты ({seats.length})
                        </h3>
                    </div>

                    <div className="space-y-3">
                        {seats.map((seat) => (
                            <div
                                key={seat.id}
                                className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0"
                            >
                                <div>
                                    <p className="font-medium text-gray-900">
                                        Ряд {seat.row_number}, Место {seat.seat_number}
                                    </p>
                                    {seat.zone_name && (
                                        <p className="text-sm text-gray-500">{seat.zone_name}</p>
                                    )}
                                </div>
                                <p className="font-semibold text-gray-900">
                                    {seat.price.toLocaleString()} ₽
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Balance & Total */}
                <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
                    <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-100">
                        <div className="flex items-center">
                            <Wallet className="w-5 h-5 text-green-500 mr-2" />
                            <span className="text-gray-600">Ваш баланс</span>
                        </div>
                        <span className="font-semibold text-gray-900">{userBalance.toLocaleString()} ₽</span>
                    </div>

                    <div className="flex items-center justify-between">
                        <span className="text-lg font-semibold text-gray-900">Итого к оплате</span>
                        <span className="text-2xl font-bold text-orange-600">
                            {getTotalPrice().toLocaleString()} ₽
                        </span>
                    </div>

                    {userBalance < getTotalPrice() && (
                        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <p className="text-sm text-yellow-800">
                                Недостаточно средств на балансе.
                                <Link href="/topup" className="ml-1 font-medium underline">
                                    Пополнить баланс
                                </Link>
                            </p>
                        </div>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-4">
                    <button
                        onClick={handleCancel}
                        className="flex-1 px-6 py-4 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors font-medium text-lg"
                    >
                        Отмена
                    </button>
                    <button
                        onClick={handlePurchase}
                        className="flex-1 px-6 py-4 bg-orange-600 text-white rounded-xl hover:bg-orange-700 transition-colors font-medium text-lg shadow-lg shadow-orange-500/30"
                    >
                        Купить
                    </button>
                </div>
            </div>
        </div>
    );
}
