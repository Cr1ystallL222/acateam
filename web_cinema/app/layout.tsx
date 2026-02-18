import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";
import SvgSprite from "@/components/SvgSprite";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "Афиша кино в Москве в кинотеатрах Мираж Синема",
  description: "Расписание сеансов в кинотеатрах Москвы.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body className={`${inter.className} bg-black text-white`}>
        <SvgSprite />
        <Header />

        <div className="pt-16 pb-20 lg:pb-0 min-h-screen flex flex-col">
          <div className="container mx-auto px-4 flex flex-1">
            <Sidebar />
            <main className="flex-1 py-8 w-full max-w-full overflow-hidden">
              {children}
            </main>
          </div>
          <Footer />
        </div>

        <MobileNav />
      </body>
    </html>
  );
}
