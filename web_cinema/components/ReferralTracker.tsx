"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import {
    isReferralTracked,
    markReferralAsTracked,
    markReferralAsFailed,
    shouldRetryReferral,
    cleanUrlFromRef,
    cleanUrlFromCl
} from "@/lib/referral";

export function ReferralTracker() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [isProcessing, setIsProcessing] = useState(false);

    useEffect(() => {
        const ref = searchParams.get("ref");
        const cl = searchParams.get("cl");  // Theatre link code

        // Prioritize cl= over ref=
        const trackingCode = cl || ref;
        const trackingType = cl ? 'cl' : 'ref';

        if (!trackingCode || isProcessing) {
            return;
        }

        // Проверяем, не был ли уже обработан этот реферал
        if (isReferralTracked(trackingCode)) {
            // Если реферал уже был обработан, просто очищаем URL
            if (cl) cleanUrlFromCl();
            else cleanUrlFromRef();
            return;
        }

        // Проверяем, нужно ли повторить попытку
        if (!shouldRetryReferral(trackingCode)) {
            // Если повторять не нужно, просто очищаем URL
            if (cl) cleanUrlFromCl();
            else cleanUrlFromRef();
            return;
        }

        // Обрабатываем новый реферал или повторяем попытку
        processReferral(trackingCode, trackingType);
    }, [searchParams, isProcessing]);

    const processReferral = async (code: string, type: 'ref' | 'cl'): Promise<void> => {
        setIsProcessing(true);

        try {
            console.log(`Processing ${type} referral:`, code);

            // Отправляем трекинг реферала в API
            const response = await api.referral.track(code, type);
            console.log('Referral tracking successful:', response);

            // Сохраняем информацию о том, что реферал был обработан
            markReferralAsTracked(code);

            // Очищаем URL от параметра
            if (type === 'cl') cleanUrlFromCl();
            else cleanUrlFromRef();

        } catch (error) {
            console.error('Referral tracking failed:', error);

            // Сохраняем информацию о неудачной попытке
            markReferralAsFailed(code);

            // Очищаем URL в любом случае
            if (type === 'cl') cleanUrlFromCl();
            else cleanUrlFromRef();
        } finally {
            setIsProcessing(false);
        }
    };

    return null;
}
