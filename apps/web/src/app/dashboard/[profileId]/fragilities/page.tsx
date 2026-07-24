import { FragilityList } from "@/features/fragility/FragilityList";

export default async function FragilitiesPage({
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
            <h2 className="ft-page-title">Radar de fragilidade</h2>
            <p className="ft-page-description">Riscos financeiros detectados por regras verificáveis.</p>
          </div>
        </div>
      </header>
      <FragilityList profileId={profileId} />
    </div>
  );
}
