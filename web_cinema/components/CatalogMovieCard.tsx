import Link from 'next/link';

interface CatalogMovieProps {
    title: string;
    image: string;
    category: string;
    age: string;
    stickers?: string[];
    isPremiere?: boolean; // Red sticker "с 19 Февраля"
    premiereDate?: string;
}

export default function CatalogMovieCard({ title, image, category, age, stickers, isPremiere, premiereDate }: CatalogMovieProps) {
    return (
        <div className="w-[160px] md:w-[240px] mb-8 group relative">
            <Link href="#" className="block relative mb-3 rounded-lg overflow-hidden">
                <img src={image} alt={title} className="w-full h-auto object-cover aspect-[2/3] group-hover:scale-105 transition-transform duration-300" />

                {/* Bottom Panel (Over image) */}
                <div className="absolute bottom-2 left-2 right-2 flex flex-wrap gap-1 items-end">
                    <span className="bg-white text-black text-[10px] font-bold px-1.5 py-0.5 rounded leading-tight">
                        {age}
                    </span>
                    {premiereDate && (
                        <span className="bg-[#E60000] text-white text-[10px] font-bold px-1.5 py-0.5 rounded leading-tight">
                            {premiereDate}
                        </span>
                    )}
                    {stickers && stickers.map((sticker, i) => (
                        <span key={i} className="bg-[#E60000] text-white text-[10px] font-bold px-1.5 py-0.5 rounded leading-tight">
                            {sticker}
                        </span>
                    ))}
                </div>
            </Link>

            <div className="pr-2">
                <Link href="#" className="text-sm md:text-base font-bold text-white leading-tight hover:text-[#E60000] transition-colors block mb-1">
                    {title}
                </Link>
                <div className="text-xs text-gray-500 leading-tight">
                    <Link href="#" className="hover:text-white transition-colors">
                        {category}
                    </Link>
                </div>
            </div>
        </div>
    );
}
