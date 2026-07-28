"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { AgentPanel } from "@/features/agent/AgentPanel";

import { Sidebar } from "./Sidebar";
import { SidebarProvider, useSidebarContext } from "./SidebarContext";

export function DashboardShell({ profileId, children }: { profileId: string; children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <DashboardShellContent profileId={profileId}>{children}</DashboardShellContent>
    </SidebarProvider>
  );
}

function DashboardShellContent({ profileId, children }: { profileId: string; children: React.ReactNode }) {
  const { isAgentOpen, closeAgent } = useSidebarContext();

  return (
    <div className={`ft-app${isAgentOpen ? "" : " ft-app--agent-closed"}`}>
      <Sidebar profileId={profileId} />
      <main className="ft-main">
        <div className="ft-content">{children}</div>
      </main>
      {isAgentOpen && <AgentPanel profileId={profileId} onClose={closeAgent} />}
    </div>
  );
}
