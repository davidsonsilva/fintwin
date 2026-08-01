/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { RecommendationScreen } from "@/features/opportunity/RecommendationScreen";

/*
 * O `analysisId` na URL é o que torna a recomendação compartilhável e
 * auditável: a mesma URL sempre abre os mesmos números, mesmo depois que os
 * dados financeiros mudarem.
 */
export default async function RecommendationPage({
  params,
}: {
  params: Promise<{ profileId: string; analysisId: string }>;
}) {
  const { profileId, analysisId } = await params;
  return <RecommendationScreen profileId={profileId} analysisId={analysisId} />;
}
