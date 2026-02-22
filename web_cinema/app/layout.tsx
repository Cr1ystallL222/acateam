import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Suspense } from "react";
import { ReferralTracker } from "@/components/ReferralTracker";
import { AuthProvider } from "@/context/AuthContext";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "Афиша — AFISHON.RU",
  description: "Куда сходить. Афиша кино: новинки кинопроката, расписание сеансов.",
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
