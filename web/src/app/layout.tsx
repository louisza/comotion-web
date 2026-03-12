import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Comotion — Coach Analytics",
  description: "Match analytics for field hockey coaches",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <nav className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-lg font-bold text-emerald-400 hover:text-emerald-300 transition-colors">
              ⌚ Comotion
            </Link>
            <div className="flex items-center gap-4">
              <NavLink href="/">Dashboard</NavLink>
              <NavLink href="/matches">Matches</NavLink>
              <NavLink href="/settings">Settings</NavLink>
            </div>
          </div>
          <div className="text-xs text-gray-600">v0.1.0</div>
        </nav>
        <main className="px-6 py-8 max-w-7xl mx-auto">{children}</main>
      </body>
    </html>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="text-sm text-gray-400 hover:text-white transition-colors">
      {children}
    </Link>
  );
}
