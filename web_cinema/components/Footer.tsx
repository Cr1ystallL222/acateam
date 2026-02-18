import Link from 'next/link';
import { Mail, ArrowUp, Landmark, Drama } from 'lucide-react';

export default function Footer() {
    return (
        <footer className="bg-[#1F1F1F] text-gray-400 py-12 mt-12 border-t border-gray-800">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
                    {/* Logos & Desc */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="flex gap-4 opacity-80">
                            <Landmark className="w-10 h-10" />
                            <Drama className="w-10 h-10" />
                        </div>
                        <p className="text-sm leading-relaxed max-w-2xl">
                            «AFISHON.RU» — гуманитарный просветительский проект, посвящённый культуре России. Мы рассказываем об интересных и значимых событиях и людях в истории литературы, архитектуры, музыки, кино, театра, а также о народных традициях и памятниках нашей природы.
                        </p>
                        {/* Links Removed as requested */}
                    </div>

                    {/* Contacts */}
                    <div className="space-y-4">
                        <h4 className="text-white font-bold uppercase tracking-wider text-sm mb-4">Контакты</h4>
                        <div className="text-sm flex flex-col gap-2">
                            <div className="flex items-center gap-2">
                                <span>E-mail:</span>
                                <a href="mailto:afisha@afishon.ru" className="text-gray-300 hover:text-white transition-colors">afisha@afishon.ru</a>
                            </div>
                            {/* Feedback link removed */}
                        </div>
                    </div>
                </div>

                <div className="border-t border-gray-800 mt-12 pt-6 text-xs text-center lg:text-left text-gray-500">
                    © 2013–2026 ФКУ «Цифровая культура». Все права защищены
                </div>
            </div>
        </footer>
    );
}
