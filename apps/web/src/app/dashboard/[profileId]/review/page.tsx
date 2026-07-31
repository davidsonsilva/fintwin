/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { PageHeader } from "@/components/shell/PageHeader";
import { ReviewStep } from "@/features/onboarding/ReviewStep";

export default async function ReviewPage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <PageHeader
        title="Revisão"
        description="Panorama do que está cadastrado no seu perfil."
        info="Confira tudo que você cadastrou (contas, rendas, obrigações, dívidas, metas e eventos) antes de confiar nas projeções."
      />
      <ReviewStep profileId={profileId} />
    </div>
  );
}
