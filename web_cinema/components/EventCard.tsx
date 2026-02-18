"use client";
import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';

interface EventCardProps {
    id: string | number;
    title: string;
    venue: string;
    date: string;
    time?: string;
    price?: string;
    image: string;
    badge?: string; // e.g. "Пушкинская карта"
    isStatic?: boolean; // Static events from the original site
    isSystem?: boolean; // System events from database
    creatorName?: string; // Creator name for user events
}

export default function EventCard({
    id, title, venue, date, time, price, image, badge,
    isStatic = false, isSystem = false, creatorName
}: EventCardProps) {
    // Determine the link based on event type
    const getEventLink = () => {
        // All events now use /event/ routing with numeric IDs
        return `/event/${id}`;
    };


    // Determine badge text - only show explicit badges, not system/creator badges
    const getBadgeText = () => {
        if (badge) return badge;
        return null;
    };

    const badgeText = getBadgeText();
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            whileHover={{ y: -5 }}
            className="group relative flex flex-col h-full bg-white overflow-hidden rounded-xl"
        >
            <Link href={getEventLink()} className="block relative aspect-[4/3] overflow-hidden rounded-xl mb-3">
                <div className="absolute inset-0 bg-gray-200 animate-pulse" /> {/* Placeholder */}
                <div
                    className="absolute inset-0 w-full h-full bg-cover bg-center transition-transform duration-500 group-hover:scale-110"
                    style={{ backgroundImage: `url(${image})` }}
                />

                {/* Badges Overlay */}
                <div className="absolute inset-0 p-3 flex flex-col justify-between">
                    <div className="flex justify-between items-start">
                        {/* Date Badge */}
                        <div className="text-white text-xs font-bold leading-tight drop-shadow-md bg-black/30 backdrop-blur-sm px-2 py-1 rounded">
                            <span className="text-lg block tracking-tighter">{date.split(' ')[0]}</span>
                            <span className="uppercase text-[10px] tracking-wide">{date.split(' ')[1]}</span>
                        </div>
                        <div className="flex flex-col gap-1">
                            {time && (
                                <div className="text-white text-xs font-medium bg-black/30 backdrop-blur-sm px-2 py-1 rounded">
                                    {time}
                                </div>
                            )}
                            {badgeText && (
                                <div className="text-white text-xs font-medium px-2 py-1 rounded bg-purple-500/80">
                                    {badgeText}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="flex justify-start">
                        {price ? (
                            <span className="bg-white/90 text-black text-xs font-bold px-2 py-1 rounded-full shadow-sm">
                                {price}
                            </span>
                        ) : (
                            <span className="bg-[#E60000] text-white text-xs font-bold px-2 py-1 rounded-full shadow-sm">
                                Билеты в продаже
                            </span>
                        )}
                    </div>
                </div>
            </Link>

            <div className="flex-1 flex flex-col">
                <h3 className="text-[#171717] font-bold text-lg leading-snug mb-1 group-hover:text-[#E60000] transition-colors line-clamp-2">
                    {title}
                </h3>
                <p className="text-gray-500 text-xs mt-auto line-clamp-2">
                    {venue}
                </p>
            </div>
        </motion.div>
    );
}
