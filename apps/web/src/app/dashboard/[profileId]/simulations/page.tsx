/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { SimulationsPageClient } from "./SimulationsPageClient";

export default async function SimulationsPage({
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
            <h2 className="ft-page-title">Simulador de decisões</h2>
            <p className="ft-page-description">Compare o cenário atual com uma decisão financeira hipotética.</p>
          </div>
        </div>
      </header>
      <SimulationsPageClient profileId={profileId} />
    </div>
  );
}
