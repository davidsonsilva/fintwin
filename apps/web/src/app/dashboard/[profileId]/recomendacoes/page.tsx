/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { PageHeader } from "@/components/shell/PageHeader";
import { RecommendationRegistry } from "@/features/recommendations/RecommendationRegistry";

export default async function RecommendationsPage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <PageHeader
        title="Registro de recomendações"
        description="Tudo o que o seu Gêmeo Financeiro já recomendou, com o desfecho de cada uma."
        info="Guarda a memória de decisão: o que foi sugerido, com quais números, e o que você decidiu. O card do dashboard mostra só a próxima ação; os planos preventivos acompanham o que você aprovou."
      />
      <RecommendationRegistry profileId={profileId} />
    </div>
  );
}
