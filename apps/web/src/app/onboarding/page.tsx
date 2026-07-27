/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { OnboardingWizard } from "@/features/onboarding/OnboardingWizard";

export default function OnboardingPage() {
  return (
    <div className="flex flex-1 justify-center px-4">
      <OnboardingWizard />
    </div>
  );
}
