"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import * as React from "react";
import { Tooltip as TooltipPrimitive } from "@base-ui/react/tooltip";
import { HelpCircle } from "lucide-react";

import { cn } from "@/lib/utils";

const TooltipProvider = TooltipPrimitive.Provider;
const Tooltip = TooltipPrimitive.Root;
const TooltipTrigger = TooltipPrimitive.Trigger;

function TooltipContent({
  className,
  side = "top",
  sideOffset = 8,
  children,
  ...props
}: TooltipPrimitive.Popup.Props &
  Pick<TooltipPrimitive.Positioner.Props, "side" | "sideOffset">) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Positioner side={side} sideOffset={sideOffset} className="isolate z-50">
        <TooltipPrimitive.Popup data-slot="tooltip-content" className={cn("ft-tooltip", className)} {...props}>
          {children}
        </TooltipPrimitive.Popup>
      </TooltipPrimitive.Positioner>
    </TooltipPrimitive.Portal>
  );
}

/**
 * Ícone de ajuda com tooltip explicativo, reutilizável em labels e cards.
 * O trigger é um `<button>` (base-ui), então funciona por hover no desktop e
 * por toque/foco no mobile. Mantenha `label` curto — nunca esconda dado
 * obrigatório aqui.
 */
function InfoTooltip({
  label,
  side = "top",
  className,
  iconSize = 14,
  "aria-label": ariaLabel = "Mais informações",
}: {
  label: React.ReactNode;
  side?: TooltipPrimitive.Positioner.Props["side"];
  className?: string;
  iconSize?: number;
  "aria-label"?: string;
}) {
  return (
    <Tooltip>
      <TooltipTrigger className={cn("ft-tooltip-trigger", className)} aria-label={ariaLabel}>
        <HelpCircle size={iconSize} aria-hidden />
      </TooltipTrigger>
      <TooltipContent side={side}>{label}</TooltipContent>
    </Tooltip>
  );
}

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider, InfoTooltip };
