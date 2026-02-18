import Link from 'next/link';

export default function MobileNav() {
    return (
        <nav className="fixed bottom-0 left-0 w-full bg-[#1A1A1A] border-t border-[#333] z-50 lg:hidden">
            <ul className="flex items-center justify-around h-16">
                <li>
                    <Link href="/" className="flex flex-col items-center gap-1 text-gray-400 hover:text-white">
                        <svg className="w-5 h-5 fill-current"><use href="#icon-home" /></svg>
                        <span className="text-xs">Главная</span>
                    </Link>
                </li>
                <li>
                    <Link href="/movies" className="flex flex-col items-center gap-1 text-gray-400 hover:text-white">
                        <svg className="w-5 h-5 fill-current"><use href="#icon-film" /></svg>
                        <span className="text-xs">Фильмы</span>
                    </Link>
                </li>
                <li>
                    <Link href="/" className="flex flex-col items-center gap-1 text-gray-400 hover:text-white">
                        <svg className="w-5 h-5 fill-current"><use href="#icon-calendar" /></svg>
                        <span className="text-xs">Расписание</span>
                    </Link>
                </li>
                <li>
                    <Link href="#" className="flex flex-col items-center gap-1 text-gray-400 hover:text-white">
                        <div className="w-5 h-5 flex flex-col justify-center gap-1 items-center">
                            <span className="w-4 h-0.5 bg-current"></span>
                            <span className="w-4 h-0.5 bg-current"></span>
                            <span className="w-4 h-0.5 bg-current"></span>
                        </div>
                        <span className="text-xs">Меню</span>
                    </Link>
                </li>
            </ul>
        </nav>
    );
}
