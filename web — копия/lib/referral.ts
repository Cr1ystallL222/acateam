/**
 * Утилиты для работы с реферальной системой
 */

const REFERRAL_STORAGE_KEY = 'referral_tracked';
const REFERRAL_FAILED_KEY = 'referral_failed';
const REFERRAL_EXPIRY_HOURS = 24;
const REFERRAL_RETRY_DELAY_MINUTES = 5; // Повторная попытка через 5 минут при ошибке

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

/**
 * Проверяет, был ли уже обработан данный реферал
 */
export function isReferralTracked(ref: string): boolean {
    try {
        const stored = localStorage.getItem(REFERRAL_STORAGE_KEY);
        if (!stored) return false;

        const data: ReferralData = JSON.parse(stored);
        const now = Date.now();

        // Проверяем, не истекло ли время жизни записи
        if (now > data.expiry) {
            localStorage.removeItem(REFERRAL_STORAGE_KEY);
            return false;
        }

        // Проверяем, тот же ли это реферал
        return data.ref === ref;
    } catch (error) {
        console.error('Error checking referral storage:', error);
        localStorage.removeItem(REFERRAL_STORAGE_KEY);
        return false;
    }
}

/**
 * Проверяет, нужно ли повторить попытку отправки реферала
 */
export function shouldRetryReferral(ref: string): boolean {
    try {
        const stored = localStorage.getItem(REFERRAL_FAILED_KEY);
        if (!stored) return true;

        const data: FailedReferralData = JSON.parse(stored);
        const now = Date.now();

        // Если это другой реферал, можно попробовать
        if (data.ref !== ref) return true;

        // Если время для повторной попытки еще не пришло
        if (now < data.nextRetry) return false;

        // Если слишком много попыток (более 3), прекращаем
        if (data.attempts >= 3) return false;

        return true;
    } catch (error) {
        console.error('Error checking failed referral storage:', error);
        localStorage.removeItem(REFERRAL_FAILED_KEY);
        return true;
    }
}

/**
 * Сохраняет информацию о неудачной попытке отправки реферала
 */
export function markReferralAsFailed(ref: string): void {
    try {
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
                // Новый реферал
                data = {
                    ref,
                    attempts: 1,
                    lastAttempt: Date.now(),
                    nextRetry: Date.now() + (REFERRAL_RETRY_DELAY_MINUTES * 60 * 1000)
                };
            }
        } else {
            data = {
                ref,
                attempts: 1,
                lastAttempt: Date.now(),
                nextRetry: Date.now() + (REFERRAL_RETRY_DELAY_MINUTES * 60 * 1000)
            };
        }

        localStorage.setItem(REFERRAL_FAILED_KEY, JSON.stringify(data));
    } catch (error) {
        console.error('Error saving failed referral to storage:', error);
    }
}

/**
 * Сохраняет информацию о том, что реферал был обработан
 */
export function markReferralAsTracked(ref: string): void {
    try {
        const expiry = Date.now() + (REFERRAL_EXPIRY_HOURS * 60 * 60 * 1000);
        const data: ReferralData = {
            ref,
            expiry,
            timestamp: Date.now()
        };
        localStorage.setItem(REFERRAL_STORAGE_KEY, JSON.stringify(data));

        // Удаляем информацию о неудачных попытках
        localStorage.removeItem(REFERRAL_FAILED_KEY);
    } catch (error) {
        console.error('Error saving referral to storage:', error);
    }
}

/**
 * Получает информацию о текущем активном реферале
 */
export function getCurrentReferral(): ReferralData | null {
    try {
        const stored = localStorage.getItem(REFERRAL_STORAGE_KEY);
        if (!stored) return null;

        const data: ReferralData = JSON.parse(stored);
        const now = Date.now();

        // Проверяем, не истекло ли время жизни записи
        if (now > data.expiry) {
            localStorage.removeItem(REFERRAL_STORAGE_KEY);
            return null;
        }

        return data;
    } catch (error) {
        console.error('Error getting current referral:', error);
        localStorage.removeItem(REFERRAL_STORAGE_KEY);
        return null;
    }
}

/**
 * Получает информацию о неудачных попытках
 */
export function getFailedReferralInfo(): FailedReferralData | null {
    try {
        const stored = localStorage.getItem(REFERRAL_FAILED_KEY);
        if (!stored) return null;

        return JSON.parse(stored);
    } catch (error) {
        console.error('Error getting failed referral info:', error);
        localStorage.removeItem(REFERRAL_FAILED_KEY);
        return null;
    }
}

/**
 * Очищает URL от параметра ref без перезагрузки страницы
 */
export function cleanUrlFromRef(): void {
    try {
        const url = new URL(window.location.href);
        url.searchParams.delete('ref');

        // Используем replaceState для изменения URL без перезагрузки
        window.history.replaceState({}, '', url.toString());
    } catch (error) {
        console.error('Error cleaning URL:', error);
    }
}

/**
 * Очищает URL от параметра cl (theatre link) без перезагрузки страницы
 */
export function cleanUrlFromCl(): void {
    try {
        const url = new URL(window.location.href);
        url.searchParams.delete('cl');

        // Используем replaceState для изменения URL без перезагрузки
        window.history.replaceState({}, '', url.toString());
    } catch (error) {
        console.error('Error cleaning URL:', error);
    }
}

/**
 * Очищает все данные о рефералах из localStorage
 */
export function clearReferralData(): void {
    try {
        localStorage.removeItem(REFERRAL_STORAGE_KEY);
        localStorage.removeItem(REFERRAL_FAILED_KEY);
    } catch (error) {
        console.error('Error clearing referral data:', error);
    }
}