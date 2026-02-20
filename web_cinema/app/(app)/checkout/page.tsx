'use client';

import { useState, useEffect, Suspense, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Ticket, AlertCircle, Loader2, Wallet, CheckCircle } from 'lucide-react';

interface SelectedSeat {
    id: number;
    row_number: number;
    seat_number: number;
    price: number;
    zone_name?: string;
}

interface EventInfo {
    id: number | string;
    title: string;
    formatted_date: string;
    formatted_time: string;
    venue: string;
}

const staticEvents = [
    { id: "grozovoy-pereval", title: "Грозовой перевал", time: "19:00", place: "Зал 1" },
    { id: "rubinshtein", title: "Рубинштейн", time: "20:00", place: "Главный зал" },
    { id: "zloy-gorod", title: "Злой город", time: "21:15", place: "Зал 2" },
    { id: "volkov", title: "Леонид Волков", time: "18:00", place: "VIP Зал" },
    { id: "van-gogh", title: "Ван Гог", time: "17:30", place: "Арт Зал" },
    { id: "zhdanov", title: "Иван Жданов", time: "19:30", place: "Сцена 1" },
    { id: "kats", title: "Максим Кац", time: "20:45", place: "Лекторий" },
    { id: "titanic", title: "Титаник", time: "18:45", place: "Зал IMAX" },
    { id: "lotr-fellowship", title: "Властелин колец: Братство Кольца", time: "18:00", place: "Зал IMAX" },
    { id: "lotr-two-towers", title: "Властелин колец: Две крепости", time: "16:25", place: "Зал 1" },
    { id: "omanko-event", title: "Специальный показ: OMANKO", time: "20:00", place: "Спецзал" }
];

type CheckoutState = 'preview' | 'processing' | 'error' | 'success';

function CheckoutContent() {
    const router = useRouter();
    const searchParams = useSearchParams();

    const [state, setState] = useState<CheckoutState>('preview');
    const [seats, setSeats] = useState<SelectedSeat[]>([]);
    const [eventInfo, setEventInfo] = useState<EventInfo | null>(null);
    const [userBalance, setUserBalance] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [ticketDataUrl, setTicketDataUrl] = useState<string | null>(null);

    useEffect(() => {
        loadCheckoutData();
    }, []);

    const loadCheckoutData = async () => {
        try {
            const seatsParam = searchParams.get('seats');
            const eventId = searchParams.get('event_id');

            if (!seatsParam || !eventId) {
                router.push('/');
                return;
            }

            const parsedSeats = JSON.parse(decodeURIComponent(seatsParam));
            setSeats(parsedSeats);

            const eventResponse = await fetch(`/api/events/${eventId}`, { credentials: 'include' });
            if (eventResponse.ok) {
                const eventData = await eventResponse.json();
                setEventInfo(eventData);
            } else {
                const staticEvent = staticEvents.find(e => e.id === eventId);
                if (staticEvent) {
                    setEventInfo({
                        id: staticEvent.id,
                        title: staticEvent.title,
                        formatted_date: 'Сегодня',
                        formatted_time: staticEvent.time,
                        venue: staticEvent.place
                    });
                }
            }

            const meResponse = await fetch('/api/me', { credentials: 'include' });
            if (meResponse.ok) {
                const userData = await meResponse.json();
                setUserBalance(userData.balance || 0);
            } else {
                router.push('/register');
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

    const handlePurchase = async () => {
        if (userBalance < getTotalPrice()) {
            router.push('/topup');
            return;
        }

        setState('processing');

        try {
            const payload = {
                movie: eventInfo?.title || "Неизвестно",
                session_time: eventInfo?.formatted_time || "12:00",
                qty: seats.length,
                total_price: getTotalPrice()
            };
            const res = await fetch('/api/orders/pay', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                setState('error');
                return;
            }

            // Вычитаем баланс визуально (не обязательно, но можно)
            setUserBalance(prev => prev - getTotalPrice());
        } catch (error) {
            console.error('Purchase error:', error);
            setState('error');
            return;
        }

        // Генерируем билет на фоне
        await generateTicket();

        // Небольшая задержка для красоты
        setTimeout(() => {
            if (ticketDataUrl || true) {
                setState('success');
            } else {
                setState('error');
            }
        }, 1500);
    };

    const generateTicket = async () => {
        return new Promise<void>((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            if (!ctx) return resolve();

            const img = new Image();
            img.src = '/Ticket_shablon.png';
            img.onload = () => {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);

                ctx.fillStyle = '#000000';
                ctx.font = 'bold 8px Arial';

                const ticketNumber = Math.floor(100000 + Math.random() * 900000).toString();
                ctx.fillText(ticketNumber, 31, 46);

                if (eventInfo) {
                    ctx.fillText(eventInfo.formatted_date, 30, 75);
                    ctx.fillText(eventInfo.formatted_time, 30, 90);
                    ctx.fillText(eventInfo.title, 25, 130);
                    ctx.fillText(eventInfo.venue, 25, 180);
                }

                const hallNumber = Math.floor(1 + Math.random() * 8).toString();
                ctx.fillText(hallNumber, 30, 225);

                if (seats.length > 0) {
                    const rows = [...new Set(seats.map(s => s.row_number))].join(', ');
                    ctx.fillText(rows, 100, 223);

                    const seatNums = seats.map(s => s.seat_number).join(', ');
                    ctx.fillText(seatNums, 170, 225);
                }

                setTicketDataUrl(canvas.toDataURL('image/png'));
                resolve();
            }
            img.onerror = () => { resolve(); }
        });
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-[#111] flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#E60000] mx-auto"></div>
                    <p className="mt-4 text-gray-400">Загрузка...</p>
                </div>
            </div>
        );
    }

    if (state === 'processing') {
        return (
            <div className="min-h-screen bg-[#111] flex items-center justify-center">
                <div className="text-center max-w-md mx-auto px-4">
                    <div className="bg-[#1a1a1a] border border-white/5 rounded-2xl shadow-xl p-8">
                        <Loader2 className="w-16 h-16 text-[#E60000] animate-spin mx-auto mb-6" />
                        <h2 className="text-2xl font-bold text-white mb-3">
                            Генерируем билет...
                        </h2>
                        <p className="text-gray-400 mb-4">
                            Пожалуйста, не закрывайте страницу. Это может занять несколько секунд.
                        </p>
                        <div className="flex justify-center space-x-1">
                            <div className="w-2 h-2 bg-[#E60000] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-[#E60000] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-[#E60000] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (state === 'error') {
        return (
            <div className="min-h-screen bg-[#111] flex items-center justify-center">
                <div className="text-center max-w-md mx-auto px-4">
                    <div className="bg-[#1a1a1a] border border-white/5 rounded-2xl shadow-xl p-8">
                        <div className="w-16 h-16 bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
                            <AlertCircle className="w-10 h-10 text-[#E60000]" />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-3">
                            Ошибка при генерации билета
                        </h2>
                        <p className="text-gray-400 mb-6">
                            К сожалению, произошла ошибка при обработке вашего заказа.
                            Пожалуйста, обратитесь в службу поддержки для решения проблемы.
                        </p>
                        <div className="space-y-3">
                            <Link
                                href="/"
                                className="w-full inline-flex items-center justify-center px-6 py-3 bg-[#E60000] text-white rounded-xl hover:bg-red-700 transition-colors font-medium"
                            >
                                Вернуться на главную
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (state === 'success' && ticketDataUrl) {
        return (
            <div className="min-h-screen bg-[#111] flex flex-col items-center justify-center py-12 px-4">
                <div className="text-center max-w-md w-full mx-auto">
                    <div className="bg-[#1a1a1a] border border-white/5 rounded-2xl shadow-xl p-8 mb-6">
                        <div className="w-16 h-16 bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
                            <CheckCircle className="w-10 h-10 text-green-500" />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Билет успешно оформлен!</h2>
                        <p className="text-gray-400 mb-8">
                            Транзакция прошла успешно. Вы можете скачать свой билет ниже.
                        </p>

                        <div className="mb-8 rounded-xl overflow-hidden border border-white/10 relative group">
                            <img src={ticketDataUrl} alt="Ваш Билет" className="w-full h-auto" />
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                {/* Иконка лупы или подсказка */}
                            </div>
                        </div>

                        <a
                            href={ticketDataUrl}
                            download={`ticket_${eventInfo?.id || 'event'}.png`}
                            className="w-full inline-flex items-center justify-center px-6 py-4 bg-[#E60000] text-white rounded-xl hover:bg-red-700 transition-colors font-medium shadow-lg shadow-red-500/20 mb-4"
                        >
                            Скачать билет
                        </a>

                        <Link href="/" className="inline-block text-gray-400 hover:text-white transition-colors">
                            Вернуться на главную
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#111]">
            <div className="bg-[#1a1a1a] shadow-sm border-b border-white/10">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="flex items-center">
                        <button
                            onClick={handleCancel}
                            className="mr-4 p-2 hover:bg-white/10 rounded-full transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5 text-gray-300" />
                        </button>
                        <div>
                            <h1 className="text-2xl font-bold text-white">Оформление заказа</h1>
                            <p className="text-sm text-gray-400 mt-1">Проверьте детали перед покупкой</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {eventInfo && (
                    <div className="bg-[#1a1a1a] rounded-xl shadow-sm p-6 mb-6 border border-white/5">
                        <h2 className="text-lg font-semibold text-white mb-2">{eventInfo.title}</h2>
                        <div className="flex flex-wrap gap-4 text-sm text-gray-400">
                            <span>{eventInfo.formatted_date}</span>
                            <span>•</span>
                            <span>{eventInfo.formatted_time}</span>
                            <span>•</span>
                            <span>{eventInfo.venue}</span>
                        </div>
                    </div>
                )}

                <div className="bg-[#1a1a1a] rounded-xl shadow-sm p-6 mb-6 border border-white/5">
                    <div className="flex items-center mb-4">
                        <Ticket className="w-5 h-5 text-[#E60000] mr-2" />
                        <h3 className="text-lg font-semibold text-white">
                            Выбранные билеты ({seats.length})
                        </h3>
                    </div>

                    <div className="space-y-3">
                        {seats.map((seat) => (
                            <div
                                key={seat.id}
                                className="flex items-center justify-between py-3 border-b border-white/10 last:border-0"
                            >
                                <div>
                                    <p className="font-medium text-white">
                                        Ряд {seat.row_number}, Место {seat.seat_number}
                                    </p>
                                    {seat.zone_name && (
                                        <p className="text-sm text-gray-500">{seat.zone_name}</p>
                                    )}
                                </div>
                                <p className="font-semibold text-white">
                                    {seat.price.toLocaleString()} ₽
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-[#1a1a1a] rounded-xl shadow-sm p-6 mb-6 border border-white/5">
                    <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/10">
                        <div className="flex items-center">
                            <Wallet className="w-5 h-5 text-green-500 mr-2" />
                            <span className="text-gray-400">Ваш баланс</span>
                        </div>
                        <span className="font-semibold text-white">{userBalance.toLocaleString()} ₽</span>
                    </div>

                    <div className="flex items-center justify-between">
                        <span className="text-lg font-semibold text-white">Итого к оплате</span>
                        <span className="text-2xl font-bold text-[#E60000]">
                            {getTotalPrice().toLocaleString()} ₽
                        </span>
                    </div>

                    {userBalance < getTotalPrice() && (
                        <div className="mt-4 p-3 bg-red-900/20 border border-red-900/50 rounded-lg">
                            <p className="text-sm text-red-400">
                                Недостаточно средств на балансе.
                                <Link href="/topup" className="ml-1 font-medium underline text-white">
                                    Пополнить баланс
                                </Link>
                            </p>
                        </div>
                    )}
                </div>

                <div className="flex flex-col sm:flex-row gap-4">
                    <button
                        onClick={handleCancel}
                        className="flex-1 px-6 py-4 bg-[#222] text-white rounded-xl hover:bg-[#333] transition-colors font-medium text-lg border border-white/10"
                    >
                        Отмена
                    </button>
                    <button
                        onClick={handlePurchase}
                        className="flex-1 px-6 py-4 bg-[#E60000] text-white rounded-xl hover:bg-red-700 transition-colors font-medium text-lg shadow-lg shadow-red-500/30"
                    >
                        Купить
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function CheckoutPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#111] flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#E60000] mx-auto"></div>
            </div>
        }>
            <CheckoutContent />
        </Suspense>
    );
}
