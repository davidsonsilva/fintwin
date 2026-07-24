import { DashboardView } from "@/features/dashboard/DashboardView";

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;
  return <DashboardView profileId={profileId} />;
}
