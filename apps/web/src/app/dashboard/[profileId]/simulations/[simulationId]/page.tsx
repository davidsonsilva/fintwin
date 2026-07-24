import Link from "next/link";

import { Button } from "@/components/ui/button";

import { SimulationDetailClient } from "./SimulationDetailClient";

export default async function SimulationDetailPage({
  params,
}: {
  params: Promise<{ profileId: string; simulationId: string }>;
}) {
  const { profileId, simulationId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 py-8">
      <header className="ft-header">
        <div className="ft-header-left">
          <div>
            <h2 className="ft-page-title">Detalhe da simulação</h2>
            <p className="ft-page-description">Comparação entre o cenário-base e o cenário simulado.</p>
          </div>
        </div>
        <div className="ft-header-actions">
          <Button
            variant="outline"
            nativeButton={false}
            render={<Link href={`/dashboard/${profileId}/simulations`}>Voltar às simulações</Link>}
          />
        </div>
      </header>
      <SimulationDetailClient simulationId={simulationId} />
    </div>
  );
}
