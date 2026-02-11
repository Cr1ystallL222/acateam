"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";

export default function RegisterPage() {
    const router = useRouter();
    const params = useSearchParams();
    const sessionId = params.get("session_id");
    const { refreshUser } = useAuth();

    const [form, setForm] = useState({
        first_name: '',
        last_name: '',
        phone: '',
        email: '',
        consent_terms: false,
        consent_pd: false
    });
    const [error, setError] = useState('');

    useEffect(() => {
        if (!sessionId) {
            router.push("/auth/telegram?mode=register");
            return;
        }
        const fn = params.get("first_name");
        if (fn) setForm(f => ({ ...f, first_name: fn }));
    }, [sessionId, params, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.auth.register({
                session_id: sessionId,
                ...form
            });
            await refreshUser();
            router.push("/");
        } catch (e: any) {
            setError(e.message);
        }
    };

    return (
        <div className="container min-h-screen flex items-center justify-center py-10">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="card w-full max-w-md"
            >
                <h1 className="text-2xl font-bold mb-6">Complete Registration</h1>
                {error && <div className="p-3 mb-4 bg-red-500/20 text-red-200 rounded">{error}</div>}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <input
                        className="input"
                        placeholder="First Name"
                        value={form.first_name}
                        onChange={e => setForm({ ...form, first_name: e.target.value })}
                        required
                    />
                    <input
                        className="input"
                        placeholder="Last Name"
                        value={form.last_name}
                        onChange={e => setForm({ ...form, last_name: e.target.value })}
                    />
                    <input
                        className="input"
                        placeholder="Phone"
                        value={form.phone}
                        onChange={e => setForm({ ...form, phone: e.target.value })}
                        required
                    />
                    <input
                        className="input"
                        placeholder="Email"
                        type="email"
                        value={form.email}
                        onChange={e => setForm({ ...form, email: e.target.value })}
                        required
                    />

                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                        <input type="checkbox" checked={form.consent_terms} onChange={e => setForm({ ...form, consent_terms: e.target.checked })} />
                        I agree to Terms & Conditions
                    </label>
                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                        <input type="checkbox" checked={form.consent_pd} onChange={e => setForm({ ...form, consent_pd: e.target.checked })} />
                        I agree to Personal Data Processing
                    </label>

                    <button type="submit" className="btn w-full mt-4" disabled={!form.consent_terms || !form.consent_pd}>
                        Register
                    </button>
                </form>
            </motion.div>
        </div>
    );
}
