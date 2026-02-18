export interface User {
    id: number;
    first_name: string;
    last_name: string;
    telegram_display_name: string;
    telegram_username?: string;
    display_name?: string;
    email: string;
    balance: number;
}

export interface AuthStartResponse {
    session_id: string;
    bot_link: string;
}

export interface AuthVerifyResponse {
    status: 'login' | 'verified' | 'need_register';
    user?: {
        id: number;
        first_name?: string;
        display_name?: string;
    };
    prefill?: {
        first_name: string;
        last_name: string;
    };
}

export interface RegisterResponse {
    status: 'ok';
    user_id: number;
}

// Helper to fetch valid JSON or throw - always includes credentials
async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
    const res = await fetch(url, {
        ...options,
        credentials: 'include',  // Always send cookies
    });
    if (!res.ok) {
        let errorMsg = 'An error occurred';
        try {
            const text = await res.text();
            try {
                const err = JSON.parse(text);
                errorMsg = err.detail || err.message || errorMsg;
            } catch {
                console.error("API Error (Non-JSON):", res.status, text);
                errorMsg = `API Error ${res.status}: ${text.slice(0, 100)}`;
            }
        } catch (e) {
            errorMsg = `API Error ${res.status}`;
        }
        throw new Error(errorMsg);
    }
    return res.json();
}

// Special fetch for /api/me that returns null on 401 (not authenticated)
async function fetchMe(): Promise<User | null> {
    const res = await fetch('/api/me', { credentials: 'include' });
    if (res.status === 401) {
        return null; // Not authenticated is not an error
    }
    if (!res.ok) {
        throw new Error(`API Error ${res.status}`);
    }
    return res.json();
}

export const api = {
    me: () => fetchMe(),
    movies: () => fetchJson<any[]>('/api/movies'),

    auth: {
        start: (intent: 'login' | 'register' = 'login') =>
            fetchJson<AuthStartResponse>('/api/auth/telegram/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ intent })
            }),
        verify: (session_id: string, code: string) =>
            fetchJson<AuthVerifyResponse>('/api/auth/telegram/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id, code })
            }),
        register: (data: any) =>
            fetchJson<RegisterResponse>('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
    },

    register: {
        draft: (data: any) =>
            fetchJson<{ session_id: string; bot_link: string }>('/api/register/draft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }),
        verify: (session_id: string, code: string) =>
            fetchJson<AuthVerifyResponse>('/api/register/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id, code })
            })
    },

    orders: {
        pay: (data: { movie: string; session_time: string; qty: number }) =>
            fetchJson<{ status: 'ok', order: any }>('/api/orders/pay', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
    },

    referral: {
        track: (code: string, type: 'ref' | 'cl' = 'ref') => {
            const param = type === 'cl' ? `cl=${code}` : `ref=${code}`;
            return fetchJson<{ status: string; link_type?: string }>(`/api/referral/track?${param}`);
        }
    },

    topup: {
        create: (amount: number) =>
            fetchJson<{ status: string; deposit_id: number }>('/api/topup/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount })
            }),
        status: (deposit_id: number) =>
            fetchJson<{
                deposit_id: number;
                status: string;
                amount: number;
                requisites: string | null;
                bank_name: string | null;
                exact_amount: number | null;
                expires_at: string | null;
                expired_reason: string | null;
                time_remaining: number | null;
            }>(`/api/topup/status?deposit_id=${deposit_id}`),
        cancel: (deposit_id: number) =>
            fetchJson<{ status: string }>(`/api/topup/cancel?deposit_id=${deposit_id}`, {
                method: 'POST'
            }),
        paid: (deposit_id: number) =>
            fetchJson<{ status: string }>(`/api/topup/paid?deposit_id=${deposit_id}`, {
                method: 'POST'
            })
    },

    support: {
        send: (message: string, file?: File | null) => {
            const formData = new FormData();
            formData.append('message', message);
            if (file) {
                formData.append('file', file);
            }

            return fetchJson<{ status: string; message: string; ticket_id: number }>('/api/support/send', {
                method: 'POST',
                body: formData
            });
        },
        messages: () =>
            fetchJson<{ messages: Array<{ id: string | number; text: string; isSupport: boolean; timestamp: string; attachment_url?: string; isRead?: boolean }>; has_unread?: boolean }>('/api/support/messages'),
        read: () =>
            fetchJson<{ status: string }>('/api/support/read', { method: 'POST' })
    }
};
