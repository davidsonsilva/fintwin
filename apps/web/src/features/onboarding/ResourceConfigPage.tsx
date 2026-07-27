"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { notFound } from "next/navigation";

import { PageHeader } from "@/components/shell/PageHeader";

import { ResourceStepForm } from "./ResourceStepForm";
import {
  accountStepConfig,
  debtStepConfig,
  eventStepConfig,
  goalStepConfig,
  incomeStepConfig,
  obligationStepConfig,
} from "./resourceConfigs";

const RESOURCE_CONFIGS = {
  accounts: accountStepConfig,
  incomes: incomeStepConfig,
  obligations: obligationStepConfig,
  debts: debtStepConfig,
  goals: goalStepConfig,
  events: eventStepConfig,
} as const;

export function ResourceConfigPage({ profileId, resource }: { profileId: string; resource: string }) {
  const config = RESOURCE_CONFIGS[resource as keyof typeof RESOURCE_CONFIGS];

  if (!config) {
    notFound();
  }

  return (
    <div className="ft-section flex flex-col gap-6 pb-8">
      <PageHeader title={config.title} />
      <ResourceStepForm profileId={profileId} config={config} />
    </div>
  );
}
