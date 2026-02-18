import Link from 'next/link';
import MovieCard from '@/components/MovieCard';
import { movies } from '@/data/movies';

export default function MoviesPage() {
    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-8 text-white">Все фильмы</h1>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {movies.map((movie) => (
                    <Link key={movie.id} href={`/movie/${movie.id}`} className="block h-full">
                        <MovieCard {...movie} />
                    </Link>
                ))}
            </div>
        </div>
    );
}
