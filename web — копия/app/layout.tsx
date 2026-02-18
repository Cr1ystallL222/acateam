import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Suspense } from "react";
import { ReferralTracker } from "@/components/ReferralTracker";
import { AuthProvider } from "@/context/AuthContext";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "Афиша — AFISHON.RU",
  description: "Куда сходить. Афиша культурных мероприятий: выставки, концерты, спектакли и другие события.",
};

import Header from "@/components/Header";
import Footer from "@/components/Footer";
import SupportChat from "@/components/SupportChat";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body className={inter.className}>
        <AuthProvider>
          {/* Referral Tracker - обрабатывает реферальные ссылки */}
          <Suspense fallback={null}>
            <ReferralTracker />
          </Suspense>

          {/* Global Top Banner */}
          <div className="relative w-full hidden md:block group z-[60]">
            <img
              src="/images/1440kh80_1-png.jpeg"
              alt="Banner"
              className="w-full h-auto object-cover max-h-[80px]"
            />
            {/* Note: In a real app, this Close button would need to be a client component or handle visibility via state */}
          </div>
          <Header />
          {children}
          <Footer />
          {/* Support Chat Widget */}
          <SupportChat />
        </AuthProvider>
      </body>
    </html>
  );
}
