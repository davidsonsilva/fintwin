/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { PreventivePlanList } from "@/features/preventive-plans/PreventivePlanList";

export default async function PlansPage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 py-8">
      <header className="ft-header">
        <div className="ft-header-left">
          <div>
            <h2 className="ft-page-title">Planos preventivos</h2>
            <p className="ft-page-description">Ações propostas por regras a partir das fragilidades detectadas.</p>
          </div>
        </div>
      </header>
      <PreventivePlanList profileId={profileId} />
    </div>
  );
}
