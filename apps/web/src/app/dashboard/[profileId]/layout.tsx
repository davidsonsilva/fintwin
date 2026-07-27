/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { Sidebar } from "@/components/shell/Sidebar";
import { AgentPanel } from "@/features/agent/AgentPanel";

export default async function DashboardLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-app">
      <Sidebar profileId={profileId} />
      <main className="ft-main">
        <div className="ft-content">{children}</div>
      </main>
      <AgentPanel profileId={profileId} />
    </div>
  );
}
