import Link from "next/link";

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">Settings</h1>
        <p className="text-sm text-gray-400">Manage your schools and teams</p>
      </div>
      <div className="flex gap-1 mb-6 border-b border-gray-800">
        <SettingsTab href="/settings/schools">🏫 Schools</SettingsTab>
        <SettingsTab href="/settings/teams">👥 Teams</SettingsTab>
      </div>
      {children}
    </div>
  );
}

function SettingsTab({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white hover:border-b-2 hover:border-emerald-400 transition-colors -mb-px"
    >
      {children}
    </Link>
  );
}
