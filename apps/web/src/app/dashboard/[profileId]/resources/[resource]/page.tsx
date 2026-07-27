/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { ResourceConfigPage } from "@/features/onboarding/ResourceConfigPage";

export default async function ResourcePage({
  params,
}: {
  params: Promise<{ profileId: string; resource: string }>;
}) {
  const { profileId, resource } = await params;

  return <ResourceConfigPage profileId={profileId} resource={resource} />;
}
