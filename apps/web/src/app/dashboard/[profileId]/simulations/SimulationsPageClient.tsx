"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


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
