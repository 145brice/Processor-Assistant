import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Processor Assistant",
  description: "Scan loan documents, track conditions and manage your mortgage pipeline.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: "try { var t = localStorage.getItem('pa_theme'); if (t === 'dark' || t === 'light') document.documentElement.dataset.theme = t; } catch (_) {}" }} />
      </head>
      <body className="bg-slate-50 text-slate-900 antialiased">{children}</body>
    </html>
  );
}
