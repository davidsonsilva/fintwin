"use client";

/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { useCallback, useMemo, useRef, useState, type ReactNode } from "react";

const GAP = 16;

/*
 * Larguras mínimas de CONTEÚDO — restrições de viabilidade do layout externo,
 * não alturas nem tamanhos impostos aos cards. Um layout que viole qualquer uma
 * delas é descartado ANTES de qualquer pontuação de simetria: legibilidade nunca
 * perde para equilíbrio visual.
 */
const MIN_COMPACT_WIDTH = 260;
const MIN_EVENTS_WIDTH = 320;

/* Proporção do grid quando o card de eventos fica ao lado. O `minmax` garante o
 * piso: se a fração `1.1fr` resolver abaixo de `MIN_EVENTS_WIDTH`, o card de
 * eventos fica com o piso e quem cede largura é a área compacta — que então
 * pode deixar de comportar 3 colunas e cair para 2, ou inviabilizar o "ao lado"
 * por inteiro. O cálculo em `eventsWidthWhenBeside` reproduz exatamente essa
 * resolução para a decisão bater com o que o CSS vai fazer de fato. */
const EVENTS_FR = 1.1;
const COMPACT_FR = 3;
const BESIDE_GRID_COLS = "grid-cols-[minmax(0,3fr)_minmax(320px,1.1fr)]";

function eventsWidthWhenBeside(sectionWidth: number) {
  const available = sectionWidth - GAP;
  const byFraction = (available * EVENTS_FR) / (COMPACT_FR + EVENTS_FR);
  return Math.max(MIN_EVENTS_WIDTH, byFraction);
}

export type CompactCardSpec = { key: string; node: ReactNode };

function useResizeSize<T extends HTMLElement>(dimension: "width" | "height", initial = 0) {
  const [size, setSize] = useState(initial);
  const observerRef = useRef<ResizeObserver | null>(null);
  const ref = useCallback(
    (el: T | null) => {
      observerRef.current?.disconnect();
      observerRef.current = null;
      if (!el) return;
      const observer = new ResizeObserver(([entry]) => {
        const next = dimension === "width" ? entry.contentRect.width : entry.contentRect.height;
        setSize((prev) => (Math.abs(prev - next) < 0.5 ? prev : next));
      });
      observer.observe(el);
      observerRef.current = observer;
    },
    [dimension]
  );
  return [ref, size] as const;
}

/*
 * Mede a altura de vários elementos (um por `key`) com um único `ResizeObserver`
 * compartilhado — chamar um hook por card violaria as Rules of Hooks (o número
 * de cards é fixo aqui, mas `.map(() => useX())` não é estaticamente seguro).
 * `registerRef(key)` devolve sempre a MESMA função de ref para aquela chave
 * (cacheada), então trocar a coluna de um card não força um
 * unobserve/observe a cada render.
 */
function useMultiHeightObserver() {
  const [heights, setHeights] = useState<Record<string, number>>({});
  const observerRef = useRef<ResizeObserver | null>(null);
  const elementsRef = useRef(new Map<string, HTMLElement>());
  const callbacksRef = useRef(new Map<string, (el: HTMLElement | null) => void>());

  const registerRef = useCallback((key: string) => {
    const cached = callbacksRef.current.get(key);
    if (cached) return cached;

    const callback = (el: HTMLElement | null) => {
      if (!observerRef.current) {
        observerRef.current = new ResizeObserver((entries) => {
          setHeights((prev) => {
            let changed = false;
            const next = { ...prev };
            for (const entry of entries) {
              const entryKey = (entry.target as HTMLElement).getAttribute("data-measure-key");
              if (!entryKey) continue;
              const height = entry.contentRect.height;
              if (Math.abs((next[entryKey] ?? 0) - height) >= 0.5) {
                next[entryKey] = height;
                changed = true;
              }
            }
            return changed ? next : prev;
          });
        });
      }
      const observer = observerRef.current;
      const prevEl = elementsRef.current.get(key);
      if (prevEl && prevEl !== el) {
        observer.unobserve(prevEl);
        elementsRef.current.delete(key);
      }
      if (el) {
        el.setAttribute("data-measure-key", key);
        observer.observe(el);
        elementsRef.current.set(key, el);
      }
    };

    callbacksRef.current.set(key, callback);
    return callback;
  }, []);

  return [registerRef, heights] as const;
}

function fits(compactAreaWidth: number, columnCount: number) {
  return (compactAreaWidth - GAP * (columnCount - 1)) / columnCount >= MIN_COMPACT_WIDTH;
}

type Candidate = { columnCount: number; eventsBeside: boolean };

/*
 * ETAPA 1 da decisão: quais composições são sequer admissíveis nesta largura.
 * Só o que sobra daqui vai para a pontuação — nenhum score pode ressuscitar um
 * layout que já falhou numa largura mínima.
 *
 * A regra que mais pega na prática é a combinação proibida
 * `columnCount === 1 && eventsBeside`: uma coluna compacta ao lado do card de
 * eventos produz cards compactos larguíssimos espremendo um card de eventos
 * estreito — pior dos dois mundos. Se os compactos só comportam uma coluna, o
 * card de eventos desce e usa a largura toda.
 */
function viableCandidates(sectionWidth: number): Candidate[] {
  const candidates: Candidate[] = [];

  const besideCompactWidth = sectionWidth - GAP - eventsWidthWhenBeside(sectionWidth);
  for (const columnCount of [3, 2]) {
    if (fits(besideCompactWidth, columnCount)) candidates.push({ columnCount, eventsBeside: true });
  }

  for (const columnCount of [3, 2]) {
    if (fits(sectionWidth, columnCount)) candidates.push({ columnCount, eventsBeside: false });
  }

  // Uma coluna só existe empilhada, e é o fallback que sempre cabe.
  candidates.push({ columnCount: 1, eventsBeside: false });
  return candidates;
}

/* Distribui os cards (em ordem semântica) sempre na coluna com menor altura
 * acumulada até aquele ponto — não reordena, só escolhe ONDE cada card entra. */
function assignToColumns(cards: CompactCardSpec[], heights: Record<string, number>, columnCount: number) {
  const columns: CompactCardSpec[][] = Array.from({ length: columnCount }, () => []);
  const columnHeights = new Array(columnCount).fill(0);
  cards.forEach((card) => {
    const height = heights[card.key] ?? 0;
    let shortest = 0;
    for (let c = 1; c < columnCount; c += 1) {
      if (columnHeights[c] < columnHeights[shortest]) shortest = c;
    }
    columnHeights[shortest] += columns[shortest].length > 0 ? height + GAP : height;
    columns[shortest].push(card);
  });
  return { columns, columnHeights };
}

/*
 * ETAPA 2: entre os candidatos que já passaram nas restrições, o menor score.
 *
 * `sectionHeight` é o custo principal e o que torna a comparação justa entre
 * "ao lado" e "embaixo": lado a lado a seção mede o mais alto dos dois blocos,
 * empilhado mede a soma. Sem esse termo, "embaixo" venceria sempre — ali não
 * existe diferença para o card de eventos a penalizar, e o score cairia para
 * quase zero mesmo desperdiçando meia tela de altura.
 *
 * `imbalance` (diferença entre a coluna mais alta e a mais baixa) é o
 * desempate: entre duas composições de altura parecida, fica a de colunas mais
 * parelhas.
 */
function scoreLayout(columnHeights: number[], eventsHeight: number, eventsBeside: boolean) {
  const gridHeight = Math.max(...columnHeights);
  const imbalance = gridHeight - Math.min(...columnHeights);
  const sectionHeight = eventsBeside
    ? Math.max(gridHeight, eventsHeight)
    : gridHeight + GAP + eventsHeight;
  return sectionHeight + imbalance;
}

/*
 * Composição externa da fileira de indicadores: 6 cards compactos + o card de
 * eventos, como duas regiões sempre independentes (nunca um grid/linha
 * compartilhada entre eles — era isso que esticava os compactos até a altura
 * do card de eventos antes desta refatoração).
 *
 * O que é novo aqui: quantidade de colunas dos compactos e se o card de eventos
 * fica ao lado ou desce para linha própria deixam de ser um breakpoint fixo e
 * passam a ser calculados a partir de medições reais (`ResizeObserver`):
 * largura da seção, altura natural de cada compacto, altura do card de
 * eventos. A decisão é sobre EM QUAL COLUNA cada card entra — nenhum card muda
 * de tamanho.
 *
 * Sem simulação de "que altura o card teria numa largura hipotética": medimos a
 * altura real do card na coluna em que ele está agora e recalculamos a
 * distribuição a partir disso. Isso é estável na prática porque as larguras de
 * coluna candidatas (2 ou 3 colunas, ambas acima de `MIN_COMPACT_WIDTH`) não
 * cruzam o ponto em que o header dos compactos muda de layout — a mesma
 * medição continua válida ao trocar a quantidade de colunas.
 */
export function AdaptiveDashboardSection({
  compactCards,
  eventsCard,
  debug = false,
}: {
  compactCards: CompactCardSpec[];
  eventsCard: ReactNode;
  /** Mostra um selo com as medições/decisão ao vivo — só para depuração visual. */
  debug?: boolean;
}) {
  const [sectionRef, sectionWidth] = useResizeSize<HTMLDivElement>("width", 1200);
  const [eventsRef, eventsHeight] = useResizeSize<HTMLDivElement>("height");
  const [registerCardRef, cardHeights] = useMultiHeightObserver();

  const layout = useMemo(() => {
    const candidates = viableCandidates(sectionWidth);
    const hasRealHeights = Object.keys(cardHeights).length > 0;

    if (!hasRealHeights) {
      // Antes da primeira medição não há como pontuar altura: fica o primeiro
      // candidato viável (mais colunas, com eventos ao lado quando couber).
      // Evita começar empilhado num desktop largo e reorganizar logo em seguida.
      const first = candidates[0];
      return { ...first, scored: [] as (Candidate & { score: number })[] };
    }

    const scored = candidates.map((candidate) => {
      const { columnHeights } = assignToColumns(compactCards, cardHeights, candidate.columnCount);
      return { ...candidate, score: scoreLayout(columnHeights, eventsHeight, candidate.eventsBeside) };
    });
    const best = scored.reduce((a, b) => (b.score < a.score ? b : a));
    return { ...best, scored };
  }, [sectionWidth, eventsHeight, cardHeights, compactCards]);

  const { columns, columnHeights } = assignToColumns(compactCards, cardHeights, layout.columnCount);

  return (
    <div className="flex flex-col gap-2">
      {debug ? (
        <div className="w-fit rounded-[8px] border border-[color:var(--ft-border)] bg-[#0a1522] px-3 py-2 font-mono text-[11px] leading-[1.6] text-[color:var(--ft-text-secondary)]">
          <div>
            seção: <b className="text-[color:var(--ft-text-primary)]">{Math.round(sectionWidth)}px</b> · colunas:{" "}
            <b className="text-[color:var(--ft-text-primary)]">{layout.columnCount}</b> · eventos ao lado:{" "}
            <b className="text-[color:var(--ft-text-primary)]">{String(layout.eventsBeside)}</b>
          </div>
          <div>
            alturas das colunas: [{columnHeights.map((h) => Math.round(h)).join(", ")}]px · eventos:{" "}
            {Math.round(eventsHeight)}px
          </div>
          <div>
            candidatos viáveis:{" "}
            {layout.scored
              .map((s) => `${s.columnCount}col${s.eventsBeside ? "+lado" : "+abaixo"}=${Math.round(s.score)}`)
              .join(" · ") || "(sem medição ainda)"}
          </div>
        </div>
      ) : null}

      <section
        ref={sectionRef}
        className={
          layout.eventsBeside ? `grid items-start gap-[16px] ${BESIDE_GRID_COLS}` : "flex flex-col gap-[16px]"
        }
      >
        <div className="flex items-start gap-[16px]">
          {columns.map((column, columnIndex) => (
            <div key={columnIndex} className="flex min-w-0 flex-1 flex-col items-start gap-[16px]">
              {column.map((card) => (
                <div key={card.key} ref={registerCardRef(card.key)} className="w-full">
                  {card.node}
                </div>
              ))}
            </div>
          ))}
        </div>

        <div ref={eventsRef}>{eventsCard}</div>
      </section>
    </div>
  );
}
