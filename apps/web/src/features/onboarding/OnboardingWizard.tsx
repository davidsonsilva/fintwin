"use client";

import { useState } from "react";

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

export function OnboardingWizard() {
  const [stepIndex, setStepIndex] = useState(0);
  const [profileId, setProfileId] = useState<string | null>(null);

  const goToReview = () => setStepIndex(STEP_LABELS.length - 1);

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 py-12">
      <ol className="flex flex-wrap gap-2 text-xs text-muted-foreground">
        {STEP_LABELS.map((label, index) => (
          <li key={label} className={index === stepIndex ? "font-semibold text-foreground" : undefined}>
            {index + 1}. {label}
          </li>
        ))}
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
