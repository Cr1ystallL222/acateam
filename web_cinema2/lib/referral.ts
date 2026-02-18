/**
 * Утилиты для работы с реферальной системой
 */

const REFERRAL_STORAGE_KEY = 'referral_tracked';
const REFERRAL_FAILED_KEY = 'referral_failed';
const REFERRAL_EXPIRY_HOURS = 24;
const REFERRAL_RETRY_DELAY_MINUTES = 5;

export interface ReferralData {
    ref: string;
    expiry: number;
    timestamp: number;
}

export interface FailedReferralData {
    ref: string;
    attempts: number;
    lastAttempt: number;
    nextRetry: number;
}

export function isReferralTracked(ref: string): boolean {
    try {
        if (typeof window === 'undefined') return false;
        const stored = localStorage.getItem(REFERRAL_STORAGE_KEY);
        if (!stored) return false;

        const data: ReferralData = JSON.parse(stored);
        const now = Date.now();

        if (now > data.expiry) {
            localStorage.removeItem(REFERRAL_STORAGE_KEY);
            return false;
        }

        return data.ref === ref;
    } catch (error) {
        console.error('Error checking referral storage:', error);
        return false;
    }
}

export function shouldRetryReferral(ref: string): boolean {
    try {
        if (typeof window === 'undefined') return true;
        const stored = localStorage.getItem(REFERRAL_FAILED_KEY);
        if (!stored) return true;

        const data: FailedReferralData = JSON.parse(stored);
        const now = Date.now();

        if (data.ref !== ref) return true;
        if (now < data.nextRetry) return false;
        if (data.attempts >= 3) return false;

        return true;
    } catch (error) {
        return true;
    }
}

export function markReferralAsFailed(ref: string): void {
    try {
        if (typeof window === 'undefined') return;
        const stored = localStorage.getItem(REFERRAL_FAILED_KEY);
        let data: FailedReferralData;

        if (stored) {
            const existing = JSON.parse(stored);
            if (existing.ref === ref) {
                data = {
                    ...existing,
                    attempts: existing.attempts + 1,
                    lastAttempt: Date.now(),
                    nextRetry: Date.now() + (REFERRAL_RETRY_DELAY_MINUTES * 60 * 1000)
                };
            } else {
                data = { ref, attempts: 1, lastAttempt: Date.now(), nextRetry: Date.now() + (REFERRAL_RETRY_DELAY_MINUTES * 60 * 1000) };
            }
        } else {
            data = { ref, attempts: 1, lastAttempt: Date.now(), nextRetry: Date.now() + (REFERRAL_RETRY_DELAY_MINUTES * 60 * 1000) };
        }

        localStorage.setItem(REFERRAL_FAILED_KEY, JSON.stringify(data));
    } catch (error) { }
}

export function markReferralAsTracked(ref: string): void {
    try {
        if (typeof window === 'undefined') return;
        const expiry = Date.now() + (REFERRAL_EXPIRY_HOURS * 60 * 60 * 1000);
        const data: ReferralData = { ref, expiry, timestamp: Date.now() };
        localStorage.setItem(REFERRAL_STORAGE_KEY, JSON.stringify(data));
        localStorage.removeItem(REFERRAL_FAILED_KEY);
    } catch (error) { }
}

export function cleanUrlFromRef(): void {
    try {
        if (typeof window === 'undefined') return;
        const url = new URL(window.location.href);
        url.searchParams.delete('ref');
        window.history.replaceState({}, '', url.toString());
    } catch (error) { }
}

export function cleanUrlFromCl(): void {
    try {
        if (typeof window === 'undefined') return;
        const url = new URL(window.location.href);
        url.searchParams.delete('cl');
        window.history.replaceState({}, '', url.toString());
    } catch (error) { }
}
