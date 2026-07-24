import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 bg-zinc-50 px-16 text-center dark:bg-black">
      <h1 className="text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">FinTwin AI</h1>
      <p className="max-w-md text-lg text-zinc-600 dark:text-zinc-400">
        Simulação e prevenção financeira com um motor determinístico no núcleo.
      </p>
      <Button nativeButton={false} render={<Link href="/onboarding">Iniciar onboarding</Link>} />
    </div>
  );
}
