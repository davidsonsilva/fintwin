"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

type TooltipPayloadItem = {
  name?: string;
  value?: number | string;
  color?: string;
  payload?: { fill?: string };
};

export function ChartTooltip({
  active,
  label,
  payload,
  formatter,
}: {
  active?: boolean;
  label?: string | number;
  payload?: TooltipPayloadItem[];
  formatter?: (value: number | string, name?: string) => string;
}) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="ft-chart-tooltip">
      {label !== undefined && <p className="ft-chart-tooltip-label">{label}</p>}
      {payload.map((entry, index) => (
        <p key={`${entry.name}-${index}`} className="ft-chart-tooltip-row">
          <span className="ft-chart-tooltip-dot" style={{ background: entry.color ?? entry.payload?.fill }} />
          {entry.name && <span className="ft-chart-tooltip-name">{entry.name}</span>}
          <span className="ft-chart-tooltip-value">
            {formatter ? formatter(entry.value ?? "", entry.name) : entry.value}
          </span>
        </p>
      ))}
    </div>
  );
}
