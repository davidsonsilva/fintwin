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
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 py-12 px-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">FinTwin AI</h1>
        <Button
          variant="outline"
          nativeButton={false}
          render={<Link href={`/dashboard/${profileId}/simulations`}>Voltar às simulações</Link>}
        />
      </header>
      <SimulationDetailClient simulationId={simulationId} />
    </div>
  );
}
