/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { PageHeader } from "@/components/shell/PageHeader";
import { BalanceHistoryChart } from "@/features/dashboard/BalanceHistoryChart";
import { BalanceHistoryTable } from "@/features/dashboard/BalanceHistoryTable";

export default async function BalanceHistoryPage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;

  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <PageHeader
        title="Histórico de saldo líquido"
        description="Evolução completa do saldo líquido, mês a mês."
        info="Série completa do seu saldo líquido ao longo dos meses registrados. Ajuda a ver a tendência: você está acumulando ou consumindo reservas?"
      />
      <BalanceHistoryChart profileId={profileId} months={24} minChartHeight={380} showFooterLink={false} />
      <BalanceHistoryTable profileId={profileId} months={24} />
    </div>
  );
}
