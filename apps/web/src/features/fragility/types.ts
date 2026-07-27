/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

export interface FragilityFindingDto {
  id: string;
  profile_id: string;
  code: string;
  title: string;
  description: string;
  formula: string;
  threshold: string;
  severity: "low" | "medium" | "high" | "critical";
  evidence: Record<string, unknown>;
  detected_at: string;
  status: string;
}
