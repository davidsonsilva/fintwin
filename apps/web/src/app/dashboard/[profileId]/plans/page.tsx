/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { PageHeader } from "@/components/shell/PageHeader";
import { PreventivePlanList } from "@/features/preventive-plans/PreventivePlanList";

export default async function PlansPage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <PageHeader
        title="Planos preventivos"
        description="Ações propostas por regras a partir das fragilidades detectadas."
        info="Sugestões para reduzir os riscos encontrados no seu perfil. São propostas por regras — nada é executado automaticamente, você é quem decide."
      />
      <PreventivePlanList profileId={profileId} />
    </div>
  );
}
