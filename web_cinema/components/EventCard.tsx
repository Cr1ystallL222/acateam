import Link from 'next/link';

interface EventProps {
    id?: string | number;
    title: string;
    image: string;
    place?: string; // Originally genre in MovieCard
    time: string;
    age?: string;
    format?: string;
    price: string | number;
    labels?: { text: string; icon?: string }[];
}

export default function EventCard({ id, title, image, place, time, age = "12+", format = "2D", price, labels }: EventProps) {
    const cardContent = (
        <div className="w-full h-full bg-[#222] rounded-lg overflow-hidden relative group border border-[#333] hover:border-[#555] transition-colors cursor-pointer">
            <div className="block p-4 h-full flex flex-col">
                <div className="text-xl font-bold mb-3 text-white group-hover:text-[#E60000] transition-colors truncate">
                    {title}
                </div>

                <div className="flex gap-4 flex-1">
                    {/* Photo */}
                    <div className="w-[100px] h-[140px] shrink-0 relative rounded overflow-hidden">
                        <img src={image} alt={title} className="w-full h-full object-cover" />
                    </div>

                    {/* Content */}
                    <div className="flex flex-col flex-1">
                        <div className="text-sm text-gray-400 mb-2 line-clamp-2 min-h-[40px]">
                            {place}
                        </div>

                        <div className="mb-auto">
                            {/* Spacer */}
                        </div>

                        {/* Bot info */}
                        <div className="mt-2 text-white">
                            <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold">{time}</span>
                                <div className="h-6 w-px bg-gray-600 mx-2"></div>
                                <div className="flex flex-col leading-none text-xs text-gray-400">
                                    <span className="border border-gray-600 px-1 rounded mb-0.5 w-fit">{age}</span>
                                    <span className="border border-gray-600 px-1 rounded w-fit">{format}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Stocks/Labels */}
                {labels && labels.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                        {labels.map((label, i) => (
                            <div key={i} className="flex items-center gap-1 text-xs text-gray-300 bg-[#333] px-2 py-1 rounded">
                                {label.icon && <img src={label.icon} alt="" className="w-4 h-4" />}
                                {label.text}
                            </div>
                        ))}
                    </div>
                )}

                {/* Price */}
                <div className="mt-3 pt-3 border-t border-[#333] flex items-center gap-4 mt-auto">
                    <div className="flex items-center gap-2 text-white font-bold">
                        <div className="w-5 h-5 flex items-center justify-center">
                            {/* SVG Place icon placeholder */}
                            <div className="w-4 h-4 border border-white/50 rounded-sm"></div>
                        </div>
                        {typeof price === 'number' ? `${price}₽` : price}
                    </div>
                </div>
            </div>
        </div>
    );

    if (id) {
        return <Link href={`/event/${id}`} className="block h-full">{cardContent}</Link>;
    }

    return cardContent;
}
