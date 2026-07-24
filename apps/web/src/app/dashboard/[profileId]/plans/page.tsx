import { PreventivePlanList } from "@/features/preventive-plans/PreventivePlanList";

export default async function PlansPage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 py-8">
      <header className="ft-header">
        <div className="ft-header-left">
          <div>
            <h2 className="ft-page-title">Planos preventivos</h2>
            <p className="ft-page-description">Ações propostas por regras a partir das fragilidades detectadas.</p>
          </div>
        </div>
      </header>
      <PreventivePlanList profileId={profileId} />
    </div>
  );
}
