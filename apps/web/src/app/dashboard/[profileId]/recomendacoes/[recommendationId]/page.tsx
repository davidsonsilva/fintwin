/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { RecommendationScreen } from "@/features/recommendations/RecommendationScreen";

/*
 * O id na URL é o que torna a recomendação compartilhável e auditável: a mesma
 * URL sempre abre os mesmos números, mesmo depois que os dados financeiros
 * mudarem ou que outra versão a substituir.
 */
export default async function RecommendationPage({
  params,
}: {
  params: Promise<{ profileId: string; recommendationId: string }>;
}) {
  const { profileId, recommendationId } = await params;
  return <RecommendationScreen profileId={profileId} recommendationId={recommendationId} />;
}
