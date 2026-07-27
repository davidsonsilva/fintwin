"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { Bell, ChevronDown, Menu, RefreshCw, Settings, UserCircle } from "lucide-react";

import { Button } from "@/design-system/components/Button";
import { IconButton } from "@/design-system/components/IconButton";

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
        <IconButton onClick={toggleMobileSidebar} aria-label="Abrir menu">
          <Menu size={20} />
        </IconButton>
        <div>
          <h2 className="ft-page-title">{title}</h2>
          {description && <p className="ft-page-description">{description}</p>}
        </div>
      </div>

      <div className="ft-header-actions">
        <div className="ft-header-actions-top">
          {children}
          <IconButton disabled aria-label="Notificações">
            <Bell size={17} />
            <span className="absolute top-2 right-2 size-[7px] rounded-full border border-[color:var(--ft-bg-page)] bg-[color:var(--ft-primary)]" />
          </IconButton>
          <IconButton disabled aria-label="Configurações">
            <Settings size={18} />
          </IconButton>
          <div className="flex items-center gap-[11px]">
            <IconButton variant="avatar" disabled aria-label="Conta">
              <UserCircle size={24} />
            </IconButton>
            <ChevronDown size={13} className="text-[#d0d6de]" />
          </div>
        </div>
        <Button variant="outline" size="sm" disabled>
          <RefreshCw size={13} />
          Sincronizar dados
        </Button>
      </div>
    </header>
  );
}
