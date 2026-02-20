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
        <div className="w-full h-[400px] bg-[#1a1a1a] rounded-2xl overflow-hidden relative group transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-red-600/30 cursor-pointer border border-[#333] hover:border-red-600/50">
            {/* Background Image with Gradient */}
            <div className="absolute inset-0">
                <img src={image} alt={title} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent"></div>
            </div>



            {/* Content Container positioned at bottom */}
            <div className="absolute bottom-0 left-0 right-0 p-5 flex flex-col z-20">

                {/* Labels/Badges */}
                <div className="flex flex-wrap gap-2 mb-3">
                    {labels && labels.map((label, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-full bg-[#E60000] text-white text-[10px] font-bold tracking-wider uppercase">
                            {label.text}
                        </span>
                    ))}
                    <span className="px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md border border-white/20 text-white text-[10px] font-medium tracking-wider">
                        {age}
                    </span>
                    <span className="px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md border border-white/20 text-white text-[10px] font-medium tracking-wider border-[#3b82f6]/50">
                        {format}
                    </span>
                </div>

                {/* Title */}
                <h3 className="text-2xl font-bold text-white mb-1 line-clamp-2 leading-tight group-hover:text-[#E60000] transition-colors drop-shadow-md">
                    {title}
                </h3>

                {/* Genre/Place */}
                <p className="text-sm text-gray-400 mb-4 line-clamp-1">
                    {place}
                </p>

                {/* Bottom Row: Time and Price */}
                <div className="flex items-center justify-between pt-4 border-t border-white/10">
                    <div className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-[#E60000]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        <span className="text-sm font-medium text-gray-200">{time}</span>
                    </div>
                    <div className="flex items-center gap-1 bg-red-600/10 px-3 py-1.5 rounded-lg border border-red-600/30 group-hover:bg-red-600 group-hover:border-red-600 transition-colors">
                        <span className="text-sm font-bold text-[#E60000] group-hover:text-white transition-colors">
                            {typeof price === 'number' ? `от ${price} ₽` : price}
                        </span>
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
