"use client";

import { LayoutDashboard, ShieldAlert, Sparkles, TrendingUp } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number }>;
}

function buildNavItems(profileId: string): NavItem[] {
  return [
    { href: `/dashboard/${profileId}`, label: "Início", icon: LayoutDashboard },
    { href: `/dashboard/${profileId}/fragilities`, label: "Radar de fragilidade", icon: ShieldAlert },
    { href: `/dashboard/${profileId}/simulations`, label: "Simulações", icon: TrendingUp },
    { href: `/dashboard/${profileId}/plans`, label: "Planos preventivos", icon: Sparkles },
  ];
}

export function Sidebar({ profileId }: { profileId: string }) {
  const pathname = usePathname();
  const navItems = buildNavItems(profileId);

  return (
    <aside className="ft-sidebar">
      <div className="ft-brand">
        <div className="ft-brand-logo">
          <Sparkles size={22} />
        </div>
        <div>
          <h1 className="ft-brand-title">
            FinTwin <span>AI</span>
          </h1>
          <p className="ft-brand-subtitle">Gêmeo Financeiro Pessoal</p>
        </div>
      </div>

      <nav className="ft-nav">
        {navItems.map((item) => {
          const isActive = item.href === `/dashboard/${profileId}` ? pathname === item.href : pathname?.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} className={`ft-nav-item${isActive ? " is-active" : ""}`}>
              <span className="ft-nav-icon">
                <Icon size={18} />
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
