export interface Movie {
    id: number;
    title: string;
    image: string;
    genre: string;
    hall: string;
    time: string;
    age: string;
    format: string;
    price: number;
    description: string;
    category: "now" | "soon" | "pushkin" | "tokino" | "love_story" | "lotr" | "omanko";
    labels?: { text: string; icon?: string }[];
}

export const movies: Movie[] = [
    // Уже в кино
    {
        id: 1,
        title: "Грозовой перевал",
        image: "/movies_files/s7185.jpg",
        genre: "мелодрама, драма",
        hall: "Зал №1",
        time: "19:00",
        age: "18+",
        format: "2D",
        price: 450,
        description: "История роковой любви Хитклиффа и Кэти, которая не знает границ и времени. Экранизация классического романа Эмилии Бронте.",
        category: "now",
        labels: [{ text: "Премьера" }]
    },
    {
        id: 2,
        title: "Уволить Жору",
        image: "/main_files/p7232.jpg",
        genre: "комедия",
        hall: "Зал №2",
        time: "14:10",
        age: "16+",
        format: "2D",
        price: 350,
        description: "Комедийная история о том, как сложно найти хорошего сотрудника и еще сложнее - уволить плохого.",
        category: "now",
        labels: [{ text: "Меморандум", icon: "/main_files/memo.svg" }]
    },
    {
        id: 3,
        title: "Убежище",
        image: "/main_files/p7217.jpg",
        genre: "триллер, экшн",
        hall: "Зал №8",
        time: "16:30",
        age: "18+",
        format: "2D",
        price: 650,
        description: "Захватывающий триллер о выживании.",
        category: "now"
    },
    {
        id: 4,
        title: "Здесь был Юра",
        image: "/main_files/p7210.jpg",
        genre: "комедия, драма, музыка",
        hall: "Зал №2",
        time: "16:45",
        age: "18+",
        format: "2D",
        price: 350,
        description: "Музыкальная комедия о поиске себя.",
        category: "now"
    },
    {
        id: 5,
        title: "Горничная",
        image: "/main_files/p7167.jpg",
        genre: "триллер",
        hall: "Зал №4",
        time: "17:10",
        age: "18+",
        format: "2D",
        price: 430,
        description: "Напряженный триллер с неожиданными поворотами.",
        category: "now"
    },
    {
        id: 6,
        title: "Счастлив, когда ты нет",
        image: "/main_files/p7231.jpg",
        genre: "романтическая комедия",
        hall: "Зал №6",
        time: "21:45",
        age: "18+",
        format: "2D",
        price: 750,
        description: "Комедия об отношениях и расставаниях.",
        category: "now"
    },
    {
        id: 7,
        title: "Гренландия 2: Миграция",
        image: "/main_files/p7200.jpg",
        genre: "триллер, экшн",
        hall: "Зал №7",
        time: "21:50",
        age: "18+",
        format: "2D",
        price: 430,
        description: "Продолжение блокбастера о выживании в глобальной катастрофе.",
        category: "now"
    },

    // Скоро
    {
        id: 8,
        title: "Марти Великолепный",
        image: "/main_files/p7180.jpg",
        genre: "комедия, спорт",
        hall: "Зал №4",
        time: "Скоро",
        age: "18+",
        format: "2D",
        price: 0,
        description: "Захватывающая спортивная драма о преодолении себя и пути к вершине.",
        category: "soon"
    },

    // Пушкинская карта
    {
        id: 9,
        title: "Сказка о царе Салтане",
        image: "/main_files/p7230.jpg",
        genre: "фэнтези",
        hall: "Зал №8",
        time: "14:15",
        age: "6+",
        format: "2D",
        price: 650,
        description: "Классическая сказка Пушкина в новом прочтении. Волшебный мир, знакомый с детства.",
        category: "pushkin",
        labels: [{ text: "Пушкинская карта" }]
    },

    // То Кино
    {
        id: 10,
        title: "Аватар: Пламя и пепел",
        image: "/main_files/p7013.jpg",
        genre: "боевик, триллер, фантастика",
        hall: "Зал №7",
        time: "15:45",
        age: "16+",
        format: "2D",
        price: 1300,
        description: "Продолжение эпической саги на Пандоре. Новые племена, новые угрозы и невероятные визуальные эффекты.",
        category: "tokino",
        labels: [{ text: "То Кино!", icon: "/main_files/tokino.svg" }]
    },
    {
        id: 11,
        title: "Stray Kids: The dominATE Experience",
        image: "/main_files/p7252.jpg",
        genre: "музыка, концерт",
        hall: "Зал №1",
        time: "16:10",
        age: "12+",
        format: "2D",
        price: 350,
        description: "Специальный показ концерта популярной k-pop группы.",
        category: "tokino",
        labels: [{ text: "То Кино!", icon: "/main_files/tokino.svg" }]
    },

    // История любви
    {
        id: 12,
        title: "Первая",
        image: "/main_files/p7229.jpg",
        genre: "романтическая драма",
        hall: "Зал №6",
        time: "14:25",
        age: "16+",
        format: "2D",
        price: 650,
        description: "Трогательная история первой любви, которая оставляет след на всю жизнь.",
        category: "love_story"
    },
    {
        id: 13,
        title: "Равиоли Оли",
        image: "/main_files/p7213.jpg",
        genre: "романтическая комедия",
        hall: "Зал №2",
        time: "14:45",
        age: "16+",
        format: "2D",
        price: 200,
        description: "Легкая итальянская комедия о еде и любви.",
        category: "love_story",
        labels: [{ text: "Фильм недели", icon: "/main_files/fn.svg" }]
    },
    {
        id: 14,
        title: "Титаник",
        image: "/main_files/p6620.jpg",
        genre: "триллер, мелодрама, драма",
        hall: "Зал №2",
        time: "18:45",
        age: "12+",
        format: "2D",
        price: 430,
        description: "Легендарная история любви на фоне катастрофы.",
        category: "love_story",
        labels: [{ text: "То Кино!", icon: "/main_files/tokino.svg" }]
    },

    // Властелин Колец
    {
        id: 15,
        title: "Властелин колец: Братство Кольца",
        image: "/main_files/p7228.jpg",
        genre: "фэнтези, приключения",
        hall: "Зал №1",
        time: "18:00",
        age: "12+",
        format: "IMAX",
        price: 500,
        description: "Легендарное начало трилогии. Хоббит Фродо отправляется в опасное путешествие, чтобы уничтожить Кольцо Всевластия.",
        category: "lotr",
        labels: [{ text: "Классика" }]
    },
    {
        id: 16,
        title: "Властелин колец: Две крепости",
        image: "/main_files/p7225.jpg",
        genre: "фэнтези, приключения",
        hall: "Зал №6",
        time: "16:25",
        age: "16+",
        format: "2D",
        price: 650,
        description: "Вторая часть трилогии. Братство распалось, но надежда еще жива.",
        category: "lotr",
        labels: [{ text: "То Кино!", icon: "/main_files/tokino.svg" }]
    },

    // МИРАЖ х OMANKO х ЭТО ЗНАК
    {
        id: 17,
        title: "Специальный показ: OMANKO",
        image: "/main_files/p7232.jpg",
        genre: "документальный, мода",
        hall: "VIP Зал",
        time: "20:00",
        age: "18+",
        format: "2D",
        price: 1000,
        description: "Эксклюзивный показ коллаборации Мираж Синема и бренда OMANKO.",
        category: "omanko",
        labels: [{ text: "Спецпоказ" }]
    }
];

export const getMoviesByCategory = (category: string) => {
    return movies.filter(movie => movie.category === category);
};

export const getMovieById = (id: number) => {
    return movies.find(movie => movie.id === id);
};
