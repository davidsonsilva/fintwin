import Link from "next/link";

import { Button } from "@/components/ui/button";
import { FragilityList } from "@/features/fragility/FragilityList";

export default async function FragilitiesPage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 py-12 px-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">FinTwin AI</h1>
        <Button variant="outline" nativeButton={false} render={<Link href={`/dashboard/${profileId}`}>Voltar ao dashboard</Link>} />
      </header>
      <FragilityList profileId={profileId} />
    </div>
  );
}
