'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Clock, Calendar, Info, Tag, MonitorPlay } from 'lucide-react';

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

export default function EventPage() {
  const params = useParams();
  const eventId = params.id as string;

  const event = staticEvents.find(e => e.id === eventId);

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

              <button
                onClick={() => alert("Бронирование билетов доступно только в кассах кинотеатра")}
                className="w-full bg-[#E60000] hover:bg-red-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-red-500/30 hover:shadow-red-500/50 hover:-translate-y-1"
              >
                Забронировать
              </button>

              <p className="text-center text-xs text-gray-500 mt-4">
                По требованию организатора, бронирование данного события ограничено
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}