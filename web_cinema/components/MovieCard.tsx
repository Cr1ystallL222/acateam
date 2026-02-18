
import React from 'react';

export const MovieCard = ({ movie, onBuy }: { movie: any, onBuy: (title: string) => void }) => {
  return (
    <li data-index={movie.id} className="my-4.5 xl:my-4 lg:my-2 md:my-5 sm:my-3 xs:my-2">
      <div className="flex w-full cursor-pointer compilation-tile--event relative h-full" data-selenide="compilationItem" onClick={() => onBuy(movie.title)}>
        <article className="recommendation-item compilation-tile">
          <div></div><div></div>
          <div className="recommendation-item_text-block compilation-tile__text-block">
            <a href="#" onClick={(e) => { e.preventDefault(); onBuy(movie.title); }} className="">
              <h2 className="recommendation-item_title compilation-tile__title" title={movie.title}>{movie.title}</h2>
              <time dateTime={movie.date} className="recommendation-item_date compilation-tile__date">
                <span className="z-10 inline-flex whitespace-nowrap">{new Date(movie.date).toLocaleDateString()} {new Date(movie.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </time>
            </a>
            <a href="#" className="recommendation-item_venue compilation-tile__venue hover:underline">{movie.venue || "TBA"}</a>
          </div>
          <a href="#" onClick={(e) => { e.preventDefault(); onBuy(movie.title); }} className="recommendation-item_img-block compilation-tile__img-block">
            <div className="recommendation-item_image compilation-tile__image">
              <picture className="size-full object-cover ui-picture">
                <img src={movie.image || "/original/placeholder.png"} alt={movie.title} className="size-full object-cover" />
              </picture>
            </div>
            <ul className="recommendation-item_features-list compilation-tile__features-list">
              <li className="recommendation-item_price-block compilation-tile__price-block">
                <div className="flex items-center justify-center rounded-full p-3 text-center text-sm bg-white/70 !bg-transparent !p-0">
                  <span className="mr-2 flex size-[18px] items-center justify-center rounded-full bg-neutral-800 text-sm leading-5 text-neutral-100"> ₽ </span>
                  <span className="text-[0.65rem]"> от {movie.price}&nbsp;</span>
                </div>
              </li>
            </ul>
          </a>
        </article>
      </div>
    </li>
  );
};
