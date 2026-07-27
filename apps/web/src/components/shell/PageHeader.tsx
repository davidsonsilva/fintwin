"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { Bell, ChevronDown, Menu, RefreshCw, Settings, UserCircle } from "lucide-react";

import { useSidebarContext } from "./SidebarContext";

export function PageHeader({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: React.ReactNode;
}) {
  const { toggleMobileSidebar } = useSidebarContext();

  return (
    <header className="ft-header">
      <div className="ft-header-left">
        <button type="button" className="ft-menu-button" onClick={toggleMobileSidebar} aria-label="Abrir menu">
          <Menu size={20} />
        </button>
        <div>
          <h2 className="ft-page-title">{title}</h2>
          {description && <p className="ft-page-description">{description}</p>}
        </div>
      </div>

      <div className="ft-header-actions">
        <div className="ft-header-actions-top">
          {children}
          <button type="button" className="ft-icon-button" disabled aria-label="Notificações">
            <Bell size={17} />
            <span className="ft-notification-dot" />
          </button>
          <button type="button" className="ft-icon-button" disabled aria-label="Configurações">
            <Settings size={18} />
          </button>
          <div className="ft-header-profile">
            <button type="button" className="ft-header-avatar" disabled aria-label="Conta">
              <UserCircle size={24} />
            </button>
            <ChevronDown size={13} className="ft-header-chevron" />
          </div>
        </div>
        <button type="button" className="ft-header-sync" disabled>
          <RefreshCw size={13} />
          Sincronizar dados
        </button>
      </div>
    </header>
  );
}
