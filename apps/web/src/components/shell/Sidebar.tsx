"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import {
  Banknote,
  Calculator,
  Calendar,
  ClipboardCheck,
  ClipboardList,
  Home,
  MessageCircleMore,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
  UserCircle,
  Wallet,
  Wand2,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useSyncExternalStore } from "react";

import { Button } from "@/design-system/components/Button";

import { useSidebarContext } from "./SidebarContext";

const subscribeNoop = () => () => {};

function useHasMounted() {
  return useSyncExternalStore(
    subscribeNoop,
    () => true,
    () => false
  );
}

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number }>;
}

function buildNavItems(profileId: string): NavItem[] {
  return [
    { href: `/dashboard/${profileId}`, label: "Início", icon: Home },
    { href: `/dashboard/${profileId}/fragilities`, label: "Radar de fragilidade", icon: ShieldAlert },
    { href: `/dashboard/${profileId}/simulations`, label: "Simulações", icon: TrendingUp },
    { href: `/dashboard/${profileId}/plans`, label: "Planos preventivos", icon: Sparkles },
  ];
}

function buildProfileNavItems(profileId: string): NavItem[] {
  return [
    { href: `/dashboard/${profileId}/profile`, label: "Perfil", icon: UserCircle },
    { href: `/dashboard/${profileId}/resources/accounts`, label: "Contas e saldos", icon: Wallet },
    { href: `/dashboard/${profileId}/resources/incomes`, label: "Rendas", icon: Banknote },
    { href: `/dashboard/${profileId}/resources/obligations`, label: "Obrigações e despesas", icon: ClipboardList },
    { href: `/dashboard/${profileId}/resources/debts`, label: "Dívidas", icon: Calculator },
    { href: `/dashboard/${profileId}/resources/goals`, label: "Metas", icon: Target },
    { href: `/dashboard/${profileId}/resources/events`, label: "Eventos futuros", icon: Calendar },
    { href: `/dashboard/${profileId}/review`, label: "Revisão", icon: ClipboardCheck },
  ];
}

export function Sidebar({ profileId }: { profileId: string }) {
  const pathname = usePathname();
  const navItems = buildNavItems(profileId);
  const profileNavItems = buildProfileNavItems(profileId);
  const { isMobileOpen, closeMobileSidebar, openAgent } = useSidebarContext();

  // O shell do dashboard (layout) pode ser servido por um cache de rota diferente
  // da página atual em navegações client-side com Turbopack, fazendo o pathname
  // usado no SSR divergir do pathname real no primeiro paint. Só calculamos o
  // item ativo após montar no cliente para evitar o hydration mismatch.
  const mounted = useHasMounted();

  useEffect(() => {
    closeMobileSidebar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  const firstNavLinkRef = useRef<HTMLAnchorElement>(null);
  useEffect(() => {
    if (isMobileOpen) {
      firstNavLinkRef.current?.focus();
    }
  }, [isMobileOpen]);

  return (
    <>
      {isMobileOpen && <div className="ft-sidebar-overlay" onClick={closeMobileSidebar} />}
      <aside className={`ft-sidebar${isMobileOpen ? " is-open" : ""}`}>
        <div className="ft-brand">
          <div className="ft-brand-logo">
            <Image src="/logo-icon.png" alt="" width={48} height={48} priority />
          </div>
          <div>
            <h1 className="ft-brand-title">
              FinTwin <span>AI</span>
            </h1>
            <p className="ft-brand-subtitle">Gêmeo Financeiro Pessoal</p>
          </div>
        </div>

        <nav className="ft-nav">
          {navItems.map((item, index) => {
            const isActive =
              mounted &&
              (item.href === `/dashboard/${profileId}` ? pathname === item.href : pathname?.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                ref={index === 0 ? firstNavLinkRef : undefined}
                className={`ft-nav-item${isActive ? " is-active" : ""}`}
              >
                <span className="ft-nav-icon">
                  <Icon size={20} />
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="ft-nav-divider" />

        <nav className="ft-nav">
          {profileNavItems.map((item) => {
            const isActive = mounted && pathname === item.href;
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href} className={`ft-nav-item${isActive ? " is-active" : ""}`}>
                <span className="ft-nav-icon">
                  <Icon size={20} />
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="ft-nav-divider" />

        <nav className="ft-nav">
          <Link href="/onboarding" className={`ft-nav-item${mounted && pathname === "/onboarding" ? " is-active" : ""}`}>
            <span className="ft-nav-icon">
              <Wand2 size={20} />
            </span>
            Onboarding guiado
          </Link>
        </nav>

        <div className="ft-sidebar-panel ft-sidebar-panel--ai">
          <div className="ft-sidebar-panel-header">
            <Image src="/agent-icon.png" alt="" width={28} height={28} className="rounded-full" />
            <h3 className="ft-sidebar-panel-title ft-sidebar-panel-title--ai">IA FinTwin</h3>
          </div>
          <p className="ft-sidebar-panel-text">Pergunte algo sobre suas finanças para o seu gêmeo.</p>
          <Button variant="ghost-purple" fullWidth onClick={openAgent} className="px-3 text-[13px]">
            <MessageCircleMore size={16} />
            Conversar com IA
          </Button>
        </div>
      </aside>
    </>
  );
}
