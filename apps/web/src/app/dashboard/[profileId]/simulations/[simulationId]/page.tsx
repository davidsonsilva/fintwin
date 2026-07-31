/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/shell/PageHeader";

import { SimulationDetailClient } from "./SimulationDetailClient";

export default async function SimulationDetailPage({
  params,
}: {
  params: Promise<{ profileId: string; simulationId: string }>;
}) {
  const { profileId, simulationId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <PageHeader
        title="Detalhe da simulação"
        description="Comparação entre o cenário-base e o cenário simulado."
        info="Mostra lado a lado como seus números ficariam com e sem a decisão simulada, para você comparar o impacto antes de agir."
      >
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href={`/dashboard/${profileId}/simulations`}>Voltar às simulações</Link>}
        />
      </PageHeader>
      <SimulationDetailClient simulationId={simulationId} />
    </div>
  );
}
