/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { PageHeader } from "@/components/shell/PageHeader";

import { SimulationsPageClient } from "./SimulationsPageClient";

export default async function SimulationsPage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <PageHeader
        title="Simulador de decisões"
        description="Compare o cenário atual com uma decisão financeira hipotética."
        info="Simule uma decisão (ex.: financiar um carro ou aumentar um aporte) e veja o impacto no seu fluxo antes de decidir. Nada é aplicado de verdade."
      />
      <SimulationsPageClient profileId={profileId} />
    </div>
  );
}
