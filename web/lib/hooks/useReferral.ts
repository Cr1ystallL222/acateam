"use client";

import { useState, useEffect } from "react";
import { getCurrentReferral, getFailedReferralInfo, type ReferralData, type FailedReferralData } from "@/lib/referral";

/**
 * Хук для работы с реферальной системой
 * Позволяет получить информацию о текущем активном реферале
 */
export function useReferral() {
    const [referralData, setReferralData] = useState<ReferralData | null>(null);
    const [failedReferralData, setFailedReferralData] = useState<FailedReferralData | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Проверяем наличие активного реферала при монтировании компонента
        const checkReferral = () => {
            try {
                const current = getCurrentReferral();
                const failed = getFailedReferralInfo();
                setReferralData(current);
                setFailedReferralData(failed);
            } catch (error) {
                console.error('Error checking referral:', error);
                setReferralData(null);
                setFailedReferralData(null);
            } finally {
                setIsLoading(false);
            }
        };

        checkReferral();

        // Слушаем изменения в localStorage (если реферал был обработан в другой вкладке)
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === 'referral_tracked' || e.key === 'referral_failed') {
                checkReferral();
            }
        };

        window.addEventListener('storage', handleStorageChange);
        
        return () => {
            window.removeEventListener('storage', handleStorageChange);
        };
    }, []);

    return {
        /** Данные о текущем активном реферале */
        referralData,
        /** Данные о неудачных попытках */
        failedReferralData,
        /** Есть ли активный реферал */
        hasActiveReferral: !!referralData,
        /** Есть ли неудачные попытки */
        hasFailedAttempts: !!failedReferralData,
        /** Код реферала */
        referralCode: referralData?.ref || failedReferralData?.ref || null,
        /** Время когда реферал был обработан */
        trackedAt: referralData ? new Date(referralData.timestamp) : null,
        /** Время истечения реферала */
        expiresAt: referralData ? new Date(referralData.expiry) : null,
        /** Время следующей попытки для неудачного реферала */
        nextRetryAt: failedReferralData ? new Date(failedReferralData.nextRetry) : null,
        /** Количество неудачных попыток */
        failedAttempts: failedReferralData?.attempts || 0,
        /** Загружается ли информация о реферале */
        isLoading
    };
}