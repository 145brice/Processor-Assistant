import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: "Processor Assistant",
  description: "Scan loan documents, track conditions and manage your mortgage pipeline.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: "try { var t = localStorage.getItem('pa_theme'); if (t === 'dark' || t === 'light') document.documentElement.dataset.theme = t; } catch (_) {}" }} />
      </head>
      <body className="bg-background text-foreground antialiased">{children}</body>
    </html>
  );
}
