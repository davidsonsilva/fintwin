/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { PageHeader } from "@/components/shell/PageHeader";
import { FragilityList } from "@/features/fragility/FragilityList";

export default async function FragilitiesPage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <PageHeader
        title="Radar de fragilidade"
        description="Riscos financeiros detectados por regras verificáveis."
        info="Fragilidades são riscos no seu perfil detectados por regras objetivas (não por opinião). Cada uma mostra a fórmula e o limite usados no cálculo."
      />
      <FragilityList profileId={profileId} />
    </div>
  );
}
