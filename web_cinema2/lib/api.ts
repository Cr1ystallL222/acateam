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

export const api = {
    referral: {
        track: (code: string, type: 'ref' | 'cl' = 'ref') => {
            const param = type === 'cl' ? `cl=${code}` : `ref=${code}`;
            return fetchJson<{ status: string; link_type?: string }>(`/api/referral/track?${param}`);
        }
    }
};
