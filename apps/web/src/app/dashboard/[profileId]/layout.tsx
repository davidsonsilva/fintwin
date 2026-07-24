import { Sidebar } from "@/components/shell/Sidebar";

export default async function DashboardLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-app">
      <Sidebar profileId={profileId} />
      <main className="ft-main">
        <div className="ft-content">{children}</div>
      </main>
    </div>
  );
}
