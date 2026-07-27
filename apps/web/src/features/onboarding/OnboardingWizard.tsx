"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { useState } from "react";
import Link from "next/link";
import {
  Banknote,
  Calculator,
  Calendar,
  ClipboardCheck,
  ClipboardList,
  Target,
  UserCircle,
  Wallet,
} from "lucide-react";

import { Button } from "@/components/ui/button";

import { ProfileStep } from "./ProfileStep";
import { ResourceStepForm } from "./ResourceStepForm";
import { ReviewStep } from "./ReviewStep";
import {
  accountStepConfig,
  debtStepConfig,
  eventStepConfig,
  goalStepConfig,
  incomeStepConfig,
  obligationStepConfig,
} from "./resourceConfigs";

const resourceSteps = [
  accountStepConfig,
  incomeStepConfig,
  obligationStepConfig,
  debtStepConfig,
  goalStepConfig,
  eventStepConfig,
];

const STEP_LABELS = ["Perfil", ...resourceSteps.map((step) => step.title), "Revisão"];

// Ícones por etapa, extraídos de imagens/desing.md.json (sidebar.navigation).
const STEP_ICONS = [UserCircle, Wallet, Banknote, ClipboardList, Calculator, Target, Calendar, ClipboardCheck];

export function OnboardingWizard() {
  const [stepIndex, setStepIndex] = useState(0);
  const [profileId, setProfileId] = useState<string | null>(null);

  const goToReview = () => setStepIndex(STEP_LABELS.length - 1);

  return (
    <div className="ft-onboarding flex flex-col gap-6">
      {profileId && (
        <div className="flex justify-end">
          <Button
            variant="outline"
            size="sm"
            nativeButton={false}
            render={<Link href={`/dashboard/${profileId}`}>Ir para o dashboard</Link>}
          />
        </div>
      )}

      <ol className="ft-stepper">
        {STEP_LABELS.map((label, index) => {
          const Icon = STEP_ICONS[index];
          return (
            <li
              key={label}
              className={`ft-step${index < stepIndex ? " is-complete" : index === stepIndex ? " is-active" : ""}`}
            >
              <span className="ft-step-icon">
                <Icon size={18} />
              </span>
              <span className="ft-step-indicator" />
              <span className="ft-step-label">
                {index + 1}. {label}
              </span>
            </li>
          );
        })}
      </ol>

      {stepIndex === 0 && (
        <ProfileStep
          onCreated={(id) => {
            setProfileId(id);
            setStepIndex(1);
          }}
          onDemoLoaded={(id) => {
            setProfileId(id);
            goToReview();
          }}
        />
      )}

      {profileId &&
        stepIndex > 0 &&
        stepIndex <= resourceSteps.length &&
        (() => {
          const config = resourceSteps[stepIndex - 1];
          return (
            <ResourceStepForm
              key={config.key}
              profileId={profileId}
              config={config}
              onBack={() => setStepIndex((current) => current - 1)}
              onNext={() => setStepIndex((current) => current + 1)}
            />
          );
        })()}

      {profileId && stepIndex === STEP_LABELS.length - 1 && (
        <ReviewStep profileId={profileId} onBack={() => setStepIndex(resourceSteps.length)} />
      )}
    </div>
  );
}
