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
