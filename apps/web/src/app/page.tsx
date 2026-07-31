/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { LineChart, ShieldCheck, Sparkles } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card } from "@/design-system/components/Card";
import { IconChip } from "@/design-system/components/IconChip";

const HIGHLIGHTS = [
  {
    icon: LineChart,
    variant: "primary",
    title: "Projeção de 12 meses",
    description: "Fluxo de caixa, primeiro déficit e autonomia financeira calculados de forma determinística.",
  },
  {
    icon: ShieldCheck,
    variant: "info",
    title: "Radar de fragilidade",
    description: "Detecta riscos financeiros reais, cada um com evidência rastreável — nunca um palpite.",
  },
  {
    icon: Sparkles,
    variant: "purple",
    title: "Agente conversacional",
    description: "Explica seus indicadores e simula decisões, sempre a partir de dados reais do seu perfil.",
  },
] as const;

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-12 bg-background px-6 py-16 text-center text-foreground">
      <div className="flex flex-col items-center gap-6">
        <div className="ft-brand-logo">
          <Image src="/logo-icon.png" alt="" width={48} height={48} priority />
        </div>
        <div className="flex flex-col gap-4">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            FinTwin <span style={{ color: "var(--ft-primary)" }}>AI</span>
          </h1>
          <p className="mx-auto max-w-md text-lg text-muted-foreground">
            Simulação e prevenção financeira com um motor determinístico no núcleo.
          </p>
        </div>
        <Button
          size="lg"
          nativeButton={false}
          render={<Link href="/onboarding">Iniciar onboarding</Link>}
        />
      </div>

      <div className="grid w-full max-w-3xl gap-4 sm:grid-cols-3">
        {HIGHLIGHTS.map(({ icon: Icon, variant, title, description }) => (
          <Card key={title} size="compact" interactive className="flex flex-col items-center gap-3 text-center">
            <IconChip icon={Icon} tone={variant} size="md" />
            <p className="ft-card-title">{title}</p>
            <p className="ft-card-subtitle">{description}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
