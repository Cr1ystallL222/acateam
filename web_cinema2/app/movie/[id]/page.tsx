import { getMovieById, movies } from "@/data/movies";
import { notFound } from "next/navigation";
import Link from "next/link";
import Image from "next/image";

interface PageProps {
    params: Promise<{ id: string }>;
}

export async function generateStaticParams() {
    return movies.map((movie) => ({
        id: movie.id,
    }));
}

export default async function MoviePage({ params }: PageProps) {
    const { id } = await params;
    const movie = getMovieById(id);

    if (!movie) {
        notFound();
    }

    return (
        <div className="text-white">
            <div className="mb-6">
                <Link href="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors w-fit">
                    <svg className="w-5 h-5 fill-current rotate-180"><use href="#icon-arrow-right" /></svg>
                    <span>Все фильмы</span>
                </Link>
            </div>

            <div className="flex flex-col md:flex-row gap-8">
                {/* Poster Image */}
                <div className="w-full md:w-[300px] lg:w-[350px] shrink-0">
                    <div className="relative rounded-lg overflow-hidden aspect-[2/3] shadow-lg">
                        <img
                            src={movie.image}
                            alt={movie.title}
                            className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent pointer-events-none"></div>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1">
                    <h1 className="text-3xl md:text-5xl font-bold mb-4">{movie.title}</h1>

                    <div className="text-gray-400 mb-4 text-lg">
                        {movie.genre}
                    </div>

                    <div className="text-gray-400 mb-6">
                        {/* Placeholder for Country, Year if available in future data */}
                        США, Великобритания, 2025
                    </div>

                    <div className="flex flex-wrap gap-4 items-center mb-8">
                        <div className="px-3 py-1 bg-[#E60000] text-white font-bold rounded">
                            {movie.time !== "Скоро" ? `Сеанс: ${movie.time}` : "Скоро в кино"}
                        </div>
                        <div className="px-3 py-1 border border-white/30 text-white rounded">
                            {movie.age}
                        </div>
                        <div className="px-3 py-1 border border-white/30 text-white rounded">
                            {movie.format}
                        </div>
                        <div className="text-gray-400 text-sm">
                            {/* Placeholder duration */}
                            02 ч 16 м
                        </div>
                    </div>

                    <p className="text-gray-300 leading-relaxed max-w-2xl mb-8">
                        {movie.description}
                    </p>

                    <div className="flex flex-wrap gap-4">
                        <button className="flex items-center gap-2 px-6 py-3 bg-[#333] hover:bg-[#555] rounded-full transition-colors font-bold">
                            <svg className="w-5 h-5"><use href="#icon-video" /></svg>
                            <span>Трейлер</span>
                        </button>
                        <button className="flex items-center gap-2 px-6 py-3 bg-[#222] hover:bg-[#333] border border-gray-600 rounded-full transition-colors font-bold">
                            <svg className="w-5 h-5"><use href="#icon-info" /></svg>
                            <span>О фильме</span>
                        </button>
                    </div>

                </div>
            </div>

            {/* Additional Info Section (Placeholder for schedule or similar) */}
            <div className="mt-12 pt-8 border-t border-[#333]">
                <h2 className="text-2xl font-bold mb-4">Расписание сеансов</h2>
                <div className="bg-[#222] p-4 rounded-lg inline-block">
                    <div className="flex items-center gap-4">
                        <div className="text-gray-400">{movie.hall}</div>
                        <div className="text-xl font-bold text-white">{movie.time}</div>
                        <div className="text-gray-400 text-sm">{movie.price > 0 ? `${movie.price} ₽` : ""}</div>
                    </div>
                </div>
            </div>

        </div>
    );
}
