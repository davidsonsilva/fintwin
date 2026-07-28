"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { createContext, useContext, useState } from "react";

interface SidebarContextValue {
  isMobileOpen: boolean;
  toggleMobileSidebar: () => void;
  closeMobileSidebar: () => void;
  isAgentOpen: boolean;
  openAgent: () => void;
  closeAgent: () => void;
}

const SidebarContext = createContext<SidebarContextValue | null>(null);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isAgentOpen, setIsAgentOpen] = useState(false);

  return (
    <SidebarContext.Provider
      value={{
        isMobileOpen,
        toggleMobileSidebar: () => setIsMobileOpen((current) => !current),
        closeMobileSidebar: () => setIsMobileOpen(false),
        isAgentOpen,
        openAgent: () => setIsAgentOpen(true),
        closeAgent: () => setIsAgentOpen(false),
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebarContext() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebarContext deve ser usado dentro de SidebarProvider");
  }
  return context;
}
