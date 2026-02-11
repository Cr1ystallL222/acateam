"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";

export default function BuyPage() {
    const router = useRouter();
    const params = useSearchParams();
    const movieTitle = params.get("movie");
    const { user } = useAuth();

    const [qty, setQty] = useState(1);
    const [session, setSession] = useState("");
    const [success, setSuccess] = useState(false);
    const [orderId, setOrderId] = useState<number | null>(null);

    useEffect(() => {
        if (!movieTitle) router.push("/");
    }, [movieTitle, router]);

    const handlePay = async () => {
        if (!session) {
            alert("Select a session time");
            return;
        }
        try {
            const res = await api.orders.pay({
                movie: movieTitle!,
                session_time: session,
                qty
            });
            if (res.status === 'ok') {
                setSuccess(true);
                setOrderId(res.order.id);
            }
        } catch (e: any) {
            alert(e.message);
        }
    };

    if (success) {
        return (
            <div className="container min-h-screen flex items-center justify-center">
                <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="card text-center">
                    <h1 className="text-3xl font-bold mb-4 text-green-400">Order Successful! 🎉</h1>
                    <p className="text-xl">Order #{orderId}</p>
                    <p className="mb-6">See you at the cinema.</p>
                    <button onClick={() => router.push("/")} className="btn">Back to Home</button>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="container min-h-screen flex items-center justify-center py-10">
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="card w-full max-w-lg"
            >
                <button onClick={() => router.back()} className="text-gray-400 hover:text-white mb-4">← Back</button>
                <h1 className="text-2xl font-bold mb-2">Buy Ticket</h1>
                <h2 className="text-xl text-blue-400 mb-6">{movieTitle} (500 RUB)</h2>

                <div className="space-y-6">
                    <div>
                        <label className="block mb-2 text-sm text-gray-400">Session Time</label>
                        <div className="flex gap-2">
                            {["12:00", "15:00", "19:00", "21:30"].map(t => (
                                <button
                                    key={t}
                                    onClick={() => setSession(t)}
                                    className={`px-4 py-2 rounded border ${session === t ? 'border-blue-500 bg-blue-500/20 text-blue-400' : 'border-gray-700 bg-gray-800'}`}
                                >
                                    {t}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="block mb-2 text-sm text-gray-400">Quantity</label>
                        <div className="flex items-center gap-4">
                            <button onClick={() => setQty(q => Math.max(1, q - 1))} className="w-10 h-10 bg-gray-700 rounded">-</button>
                            <span className="text-xl font-mono">{qty}</span>
                            <button onClick={() => setQty(q => q + 1)} className="w-10 h-10 bg-gray-700 rounded">+</button>
                        </div>
                    </div>

                    <div className="pt-4 border-t border-gray-700 flex justify-between items-center">
                        <span className="text-xl font-bold">Total: {qty * 500} RUB</span>
                        <button onClick={handlePay} className="btn">Pay Now</button>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
