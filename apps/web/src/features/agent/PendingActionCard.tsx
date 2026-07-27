"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */


import { Button } from "@/components/ui/button";
import { DECISION_LABELS } from "@/features/simulation/decisionFields";

import type { PendingActionDto } from "./types";

export function PendingActionCard({
  pendingAction,
  onConfirm,
  onCancel,
  isConfirming,
}: {
  pendingAction: PendingActionDto;
  onConfirm: () => void;
  onCancel: () => void;
  isConfirming: boolean;
}) {
  const label = DECISION_LABELS[pendingAction.decision_type as keyof typeof DECISION_LABELS] ?? pendingAction.decision_type;

  if (pendingAction.confirmed) {
    return (
      <div className="ft-agent-pending-action">
        <p className="ft-agent-pending-title">Simulação confirmada</p>
        <p className="ft-agent-pending-params">{label} já foi executada e salva.</p>
      </div>
    );
  }

  return (
    <div className="ft-agent-pending-action">
      <p className="ft-agent-pending-title">Proposta de simulação: {label}</p>
      <p className="ft-agent-pending-params">
        {Object.entries(pendingAction.parameters).map(([key, value]) => (
          <span key={key}>
            {key}: {String(value)}
            <br />
          </span>
        ))}
      </p>
      <div className="ft-agent-pending-actions">
        <Button size="sm" variant="secondary" onClick={onCancel} disabled={isConfirming}>
          Cancelar
        </Button>
        <Button size="sm" onClick={onConfirm} disabled={isConfirming}>
          {isConfirming ? "Confirmando..." : "Confirmar"}
        </Button>
      </div>
    </div>
  );
}
