import Link from 'next/link';
import Image from 'next/image';

interface EventProps {
    title: string;
    image: string;
    place: string;
    time: string;
    date: string;
    day: string;
    price: string;
}

export default function EventCard({ title, image, place, time, date, day, price }: EventProps) {
    return (
        <div className="w-full h-full bg-[#222] rounded-lg overflow-hidden relative group border border-[#333] hover:border-[#555] transition-colors cursor-pointer flex flex-col">
            <div className="p-4 flex-1 flex flex-col">
                <div className="text-xl font-bold mb-3 text-white group-hover:text-[#E60000] transition-colors line-clamp-2 min-h-[56px]">
                    {title}
                </div>

                <div className="flex gap-4 flex-1">
                    {/* Photo */}
                    <div className="w-[100px] h-[140px] shrink-0 relative rounded overflow-hidden">
                        <Image
                            src={image}
                            alt={title}
                            fill
                            className="object-cover"
                        />
                        {/* Date Overlay */}
                        <div className="absolute top-0 left-0 bg-black/70 text-white px-2 py-1 text-xs font-bold text-center w-full">
                            <div className="leading-none text-[10px] uppercase text-gray-300">{day}</div>
                            <div className="leading-none text-sm">{date.split(' ')[0]}</div>
                            <div className="leading-none text-[9px] text-gray-400">{date.split(' ')[1]}</div>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="flex flex-col flex-1 justify-between">
                        <div className="text-sm text-gray-400 mb-2 line-clamp-4 leading-tight">
                            {place}
                        </div>

                        {/* Bot info */}
                        <div className="mt-auto text-white">
                            <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold">{time}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Price */}
                <div className="mt-3 pt-3 border-t border-[#333] flex items-center gap-4">
                    <div className="flex items-center gap-2 text-white font-bold">
                        <div className="w-5 h-5 flex items-center justify-center text-gray-400">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" /><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" /><path d="M4 22h16" /><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" /><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" /><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" /></svg>
                        </div>
                        {price}
                    </div>
                </div>
            </div>
        </div>
    );
}
