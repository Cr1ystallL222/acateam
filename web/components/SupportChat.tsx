"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";

interface Message {
    id: string | number;
    text: string;
    isSupport: boolean;
    timestamp: Date;
    attachment_url?: string;
    isRead?: boolean;
}

export default function SupportChat() {
    const { user, loading: authLoading } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState("");
    const [isSending, setIsSending] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [hasNewReply, setHasNewReply] = useState(false);

    // File upload state
    const [file, setFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    // const lastMessageCount = useRef(0); // Removed in favor of server status

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen, previewUrl]);

    // Load messages from API
    const loadMessages = useCallback(async () => {
        if (!user) return;

        try {
            const data = await api.support.messages();
            const loadedMessages = data.messages.map((m) => ({
                ...m,
                timestamp: new Date(m.timestamp),
            }));

            // Server source of truth for unread
            if (data.has_unread !== undefined) {
                setHasNewReply(data.has_unread && !isOpen);
            } else {
                // Fallback (should not be needed after API update)
                const hasSupport = loadedMessages.some(m => m.isSupport);
                // Simple logic: if last message is support and we are closed? 
                // Better to rely on server.
            }

            setMessages(loadedMessages);
        } catch (err) {
            // Silently fail on polling
        }
    }, [user, isOpen]);

    // Load messages when chat opens
    useEffect(() => {
        if (isOpen && user) {
            loadMessages();
            // Mark as read
            api.support.read().then(() => {
                setHasNewReply(false);
            }).catch(() => { });
        }
    }, [isOpen, user, loadMessages]);

    // Poll for new messages every 5 seconds when chat is open
    useEffect(() => {
        if (!isOpen || !user) return;

        const interval = setInterval(loadMessages, 5000);
        return () => clearInterval(interval);
    }, [isOpen, user, loadMessages]);

    // Also poll when closed to show notification
    useEffect(() => {
        if (isOpen || !user) return; // Don't poll if open (already polling above) -> logic fix

        // Actually we need to poll when closed to update Red Dot
        const interval = setInterval(loadMessages, 15000);
        return () => clearInterval(interval);
    }, [isOpen, user, loadMessages]);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            if (selectedFile.size > 5 * 1024 * 1024) {
                setError("Файл слишком большой (макс. 5Мб)");
                return;
            }
            setFile(selectedFile);
            setPreviewUrl(URL.createObjectURL(selectedFile));
        }
    };

    const removeFile = () => {
        setFile(null);
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
            setPreviewUrl(null);
        }
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const handleSend = async () => {
        if ((!inputText.trim() && !file) || isSending) return;

        if (!user) {
            setError("Войдите в аккаунт, чтобы написать в поддержку");
            return;
        }

        const text = inputText.trim();
        const currentFile = file;
        const currentPreview = previewUrl;

        setInputText("");
        setFile(null);
        setPreviewUrl(null);
        if (fileInputRef.current) fileInputRef.current.value = "";

        setError(null);
        setIsSending(true);

        // Add message to local state immediately
        const tempId = `temp_${Date.now()}`;
        const newMessage: Message = {
            id: tempId,
            text,
            isSupport: false,
            timestamp: new Date(),
            attachment_url: currentPreview || undefined
        };
        setMessages((prev) => [...prev, newMessage]);

        try {
            await api.support.send(text, currentFile);
            // Reload messages to get the actual ID
            await loadMessages();
        } catch (err: any) {
            setError(err.message || "Ошибка отправки сообщения");
            // Remove the temp message on error
            setMessages((prev) => prev.filter((m) => m.id !== tempId));
            setInputText(text);
            if (currentFile) {
                setFile(currentFile);
                setPreviewUrl(currentPreview);
            }
        } finally {
            setIsSending(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // Don't render while auth is loading
    if (authLoading) return null;

    return (
        <>
            {/* Floating Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full shadow-lg flex items-center justify-center transition-all duration-300 hover:scale-105"
                style={{
                    backgroundColor: "#29a9eb",
                    boxShadow: "0 4px 14px rgba(41, 169, 235, 0.4)"
                }}
                aria-label="Открыть чат поддержки"
            >
                {hasNewReply && !isOpen && (
                    <span className="absolute 0 top-0 right-0 w-5 h-5 bg-red-500 border-2 border-white rounded-full flex items-center justify-center text-white text-[10px] font-bold z-10">
                        !
                    </span>
                )}
                {isOpen ? (
                    <svg
                        className="w-8 h-8 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                        />
                    </svg>
                ) : (
                    <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="currentColor" />
                    </svg>
                )}
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div
                    className="fixed bottom-24 right-4 sm:right-6 z-50 w-[360px] max-w-[calc(100vw-32px)] rounded-2xl shadow-2xl overflow-hidden flex flex-col font-sans"
                    style={{
                        height: "550px",
                        maxHeight: "80vh",
                        backgroundColor: "#ffffff",
                        boxShadow: "0 10px 40px rgba(0,0,0,0.15)"
                    }}
                >
                    {/* Header */}
                    <div
                        className="p-4 flex items-center gap-3 relative overflow-hidden"
                        style={{
                            backgroundColor: "#29a9eb",
                        }}
                    >
                        {/* Avatar */}
                        <div className="relative">
                            <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center overflow-hidden border-2 border-white/30">
                                <img
                                    src="/images/OperatorImage.jpg"
                                    alt="Agent"
                                    className="w-full h-full object-cover"
                                    style={{ opacity: 0 }} // Fallback if image fails or just use a nice placeholder
                                    onLoad={(e) => e.currentTarget.style.opacity = "1"}
                                    onError={(e) => {
                                        e.currentTarget.src = "https://ui-avatars.com/api/?name=Александра&background=fff&color=29a9eb&rounded=true"
                                    }}
                                />
                                <div className="absolute inset-0 flex items-center justify-center bg-white text-[#29a9eb] font-bold text-lg" style={{ zIndex: -1 }}>A</div>
                            </div>
                            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 border-2 border-[#29a9eb] rounded-full"></div>
                        </div>

                        <div className="flex-1 text-white">
                            <h3 className="font-bold text-lg leading-tight">Александра</h3>
                            <p className="text-xs opacity-90 font-light">специалист клиентской службы</p>
                        </div>

                        <button
                            onClick={() => setIsOpen(false)}
                            className="text-white/80 hover:text-white transition-colors p-1"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* Messages Area */}
                    <div
                        className="flex-1 p-4 overflow-y-auto bg-[#f0f2f5] scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
                        style={{
                            backgroundImage: "radial-gradient(#e5e7eb 1px, transparent 1px)",
                            backgroundSize: "20px 20px"
                        }}
                    >
                        {messages.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-gray-400">
                                <p className="text-sm bg-white/50 px-4 py-2 rounded-full mb-4">Специалист на связи 24/7</p>
                                <div className="bg-white p-4 rounded-xl shadow-sm text-center max-w-[80%]">
                                    <p className="text-gray-800 font-medium mb-1">Здравствуйте!</p>
                                    <p className="text-gray-500 text-sm">Чем я могу вам помочь сегодня?</p>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {messages.map((msg) => (
                                    <div
                                        key={msg.id}
                                        className={`flex ${msg.isSupport ? "justify-start" : "justify-end"
                                            } items-end gap-2`}
                                    >
                                        {msg.isSupport && (
                                            <div className="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 bg-gray-200 border border-white shadow-sm mb-1">
                                                <img
                                                    src="/images/OperatorImage.jpg"
                                                    alt="Support"
                                                    className="w-full h-full object-cover"
                                                />
                                            </div>
                                        )}

                                        <div
                                            className={`max-w-[85%] px-4 py-3 shadow-sm ${msg.isSupport
                                                ? "bg-white text-gray-800 rounded-2xl rounded-bl-none"
                                                : "bg-[#29a9eb] text-white rounded-2xl rounded-br-none"
                                                }`}
                                        >
                                            {msg.attachment_url && (
                                                <div className="mb-2 rounded-lg overflow-hidden">
                                                    <img
                                                        src={msg.attachment_url}
                                                        alt="attachment"
                                                        className="max-w-full h-auto max-h-48 object-cover"
                                                    />
                                                </div>
                                            )}
                                            <p className="text-[15px] leading-snug whitespace-pre-wrap break-words">
                                                {msg.text}
                                            </p>
                                            <p
                                                className={`text-[10px] mt-1 text-right ${msg.isSupport ? "text-gray-400" : "text-white/70"
                                                    }`}
                                            >
                                                {msg.timestamp.toLocaleTimeString([], {
                                                    hour: "2-digit",
                                                    minute: "2-digit",
                                                    hour12: false
                                                })}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                                <div ref={messagesEndRef} />
                            </div>
                        )}
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="px-4 py-2 bg-red-100 border-t border-red-200 text-red-600 text-sm text-center">
                            {error}
                        </div>
                    )}

                    {/* Input Area */}
                    <div className="p-3 bg-white border-t border-gray-100">
                        {!user ? (
                            <div className="text-center py-3">
                                <p className="text-sm text-gray-500 mb-2">Авторизуйтесь, чтобы начать чат</p>
                                <a
                                    href="/auth/login"
                                    className="inline-block px-4 py-2 bg-[#29a9eb] text-white rounded-lg text-sm font-medium hover:bg-[#2390c9] transition-colors"
                                >
                                    Войти
                                </a>
                            </div>
                        ) : (
                            <div className="relative">
                                {/* Preview Area if file selected */}
                                {previewUrl && (
                                    <div className="absolute bottom-full left-0 right-0 p-2 bg-gray-50 border-t border-gray-200 mb-2 rounded-t-lg">
                                        <div className="relative inline-block">
                                            <img src={previewUrl} alt="Preview" className="h-16 w-auto rounded-lg border border-gray-300" />
                                            <button
                                                onClick={removeFile}
                                                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-0.5 shadow-md hover:bg-red-600"
                                            >
                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                            </button>
                                        </div>
                                    </div>
                                )}

                                <div className="flex items-center gap-2 bg-gray-50 p-1 rounded-2xl border border-gray-200 focus-within:border-[#29a9eb] focus-within:ring-1 focus-within:ring-[#29a9eb] transition-all">
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        onChange={handleFileSelect}
                                        className="hidden"
                                        accept="image/*"
                                    />

                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                                        title="Прикрепить фото"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                                        </svg>
                                    </button>

                                    <textarea
                                        value={inputText}
                                        onChange={(e) => setInputText(e.target.value)}
                                        onKeyDown={handleKeyPress}
                                        placeholder="Введите сообщение..."
                                        rows={1}
                                        className="flex-1 bg-transparent border-none text-gray-800 placeholder-gray-400 resize-none focus:ring-0 py-2.5 px-1 max-h-24"
                                        style={{ minHeight: "44px" }}
                                        disabled={isSending}
                                    />

                                    <button
                                        onClick={handleSend}
                                        disabled={(!inputText.trim() && !file) || isSending}
                                        className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 ${inputText.trim() || file
                                            ? "bg-[#29a9eb] text-white shadow-md hover:bg-[#2390c9] transform hover:scale-105 active:scale-95"
                                            : "bg-gray-200 text-gray-400 cursor-not-allowed"
                                            }`}
                                    >
                                        {isSending ? (
                                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        ) : (
                                            <svg className="w-5 h-5 ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                            </svg>
                                        )}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </>
    );
}
