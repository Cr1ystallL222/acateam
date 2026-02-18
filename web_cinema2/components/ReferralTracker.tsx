"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
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
    const [isProcessing, setIsProcessing] = useState(false);

    useEffect(() => {
        const ref = searchParams.get("ref");
        const cl = searchParams.get("cl");

        const trackingCode = cl || ref;
        const trackingType = cl ? 'cl' : 'ref';

        if (!trackingCode || isProcessing) {
            return;
        }

        if (isReferralTracked(trackingCode)) {
            if (cl) cleanUrlFromCl();
            else cleanUrlFromRef();
            return;
        }

        if (!shouldRetryReferral(trackingCode)) {
            if (cl) cleanUrlFromCl();
            else cleanUrlFromRef();
            return;
        }

        processReferral(trackingCode, trackingType as 'ref' | 'cl');
    }, [searchParams, isProcessing]);

    const processReferral = async (code: string, type: 'ref' | 'cl'): Promise<void> => {
        setIsProcessing(true);

        try {
            console.log(`Processing ${type} referral:`, code);
            const response = await api.referral.track(code, type);
            console.log('Referral tracking successful:', response);
            markReferralAsTracked(code);
            if (type === 'cl') cleanUrlFromCl();
            else cleanUrlFromRef();
        } catch (error) {
            console.error('Referral tracking failed:', error);
            markReferralAsFailed(code);
            if (type === 'cl') cleanUrlFromCl();
            else cleanUrlFromRef();
        } finally {
            setIsProcessing(false);
        }
    };

    return null;
}
