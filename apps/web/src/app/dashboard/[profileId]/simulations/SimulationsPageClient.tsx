"use client";

import { useRouter } from "next/navigation";

import { DecisionForm } from "@/features/simulation/DecisionForm";
import { SimulationHistory } from "@/features/simulation/SimulationHistory";

export function SimulationsPageClient({ profileId }: { profileId: string }) {
  const router = useRouter();

  return (
    <>
      <DecisionForm
        profileId={profileId}
        onCreated={(simulationId) => router.push(`/dashboard/${profileId}/simulations/${simulationId}`)}
      />
      <SimulationHistory profileId={profileId} />
    </>
  );
}
