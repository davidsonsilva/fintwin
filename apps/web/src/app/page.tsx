import { Sparkles } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 bg-background px-16 text-center text-foreground">
      <div className="ft-brand-logo">
        <Sparkles size={28} />
      </div>
      <h1 className="text-3xl font-semibold tracking-tight">
        FinTwin <span style={{ color: "var(--ft-primary)" }}>AI</span>
      </h1>
      <p className="max-w-md text-lg text-muted-foreground">
        Simulação e prevenção financeira com um motor determinístico no núcleo.
      </p>
      <Button nativeButton={false} render={<Link href="/onboarding">Iniciar onboarding</Link>} />
    </div>
  );
}
