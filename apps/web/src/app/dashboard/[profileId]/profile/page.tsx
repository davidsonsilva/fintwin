/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { PageHeader } from "@/components/shell/PageHeader";
import { ProfileSummary } from "@/features/onboarding/ProfileSummary";

export default async function ProfilePage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <PageHeader
        title="Perfil"
        description="Dados básicos do seu perfil financeiro."
        info="Dados básicos usados para calibrar todos os cálculos do seu gêmeo financeiro (moeda, dependentes e capacidade de redução de despesas)."
      />
      <ProfileSummary profileId={profileId} />
    </div>
  );
}
