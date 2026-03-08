import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Comotion — Coach Analytics",
  description: "Match analytics for field hockey coaches",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <nav className="border-b border-gray-800 px-6 py-3 flex items-center gap-4">
          <span className="text-lg font-bold text-emerald-400">⌚ Comotion</span>
          <a href="/" className="text-sm text-gray-400 hover:text-white">Dashboard</a>
          <a href="/matches" className="text-sm text-gray-400 hover:text-white">Matches</a>
        </nav>
        <main className="px-6 py-8 max-w-7xl mx-auto">{children}</main>
      </body>
    </html>
  );
}
