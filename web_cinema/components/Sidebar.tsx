import Link from 'next/link';

export default function Sidebar() {
    return (
        <div className="hidden lg:block w-64 shrink-0 py-8 pr-4">
            {/* Section 1 */}
            <ul className="space-y-4 mb-8">
                <li>
                    <Link href="/movies" className="block relative group overflow-hidden rounded-lg bg-[#222] border border-[#333] hover:border-[#555] transition-all duration-300">
                        <div className="absolute inset-0 bg-gradient-to-r from-purple-900/20 to-blue-900/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        <div className="relative p-4 flex items-center justify-between">
                            <span className="text-lg font-bold text-white group-hover:text-[#E60000] transition-colors">Фильмы</span>
                            <svg className="w-5 h-5 text-gray-500 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                            </svg>
                        </div>
                    </Link>
                </li>
                <li>
                    <Link href="/" className="block relative group overflow-hidden rounded-lg bg-[#222] border border-[#333] hover:border-[#555] transition-all duration-300">
                        <div className="absolute inset-0 bg-gradient-to-r from-red-900/20 to-orange-900/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        <div className="relative p-4 flex items-center justify-between">
                            <span className="text-lg font-bold text-white group-hover:text-[#E60000] transition-colors">Расписание</span>
                            <svg className="w-5 h-5 text-gray-500 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </div>
                    </Link>
                </li>
            </ul>

            {/* Section 2 */}
            {/* Section 2 removed as range requested */}
        </div>
    );
}
