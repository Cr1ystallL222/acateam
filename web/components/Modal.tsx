"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ReactNode } from "react";
import { X } from 'lucide-react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: ReactNode;
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 z-[100] backdrop-blur-sm flex items-center justify-center"
                    />
                    
                    {/* Modal Content */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[101] w-[90%] max-w-[500px]"
                    >
                        <div className="bg-[#1f1f1f] text-white rounded-xl p-6 shadow-2xl relative overflow-hidden ring-1 ring-white/10">
                            {title && <h2 className="text-xl font-bold mb-4 pr-8">{title}</h2>}
                            <div className="relative z-10">
                                {children}
                            </div>
                            <button 
                                onClick={onClose} 
                                className="absolute top-4 right-4 p-1 text-gray-400 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                            >
                                <X size={20} />
                            </button>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
