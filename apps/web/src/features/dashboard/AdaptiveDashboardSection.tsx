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
 * delas não entra na lista de composições possíveis.
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

function fits(compactAreaWidth: number, columnCount: number) {
  return (compactAreaWidth - GAP * (columnCount - 1)) / columnCount >= MIN_COMPACT_WIDTH;
}

export type DashboardLayout = { columnCount: number; eventsBeside: boolean };

/*
 * A composição é função APENAS da largura da seção.
 *
 * Não é uma escolha estética: é o que impede o bug de oscilação. A versão
 * anterior media a altura de cada card com `ResizeObserver` e pontuava as
 * composições candidatas por altura total. Mas a altura de um card depende da
 * largura da coluna, e a largura da coluna é justamente o que a decisão altera
 * — a saída do algoritmo voltava para a entrada. Pior: as alturas medidas eram
 * as da composição ATUAL, e eram aplicadas a candidatos cujas colunas têm outra
 * largura, ou seja, todo candidato era pontuado com alturas erradas.
 *
 * Esse laço não tinha amortecimento nem ponto fixo garantido: em 3 colunas o
 * card media alto, o que elegia 2 colunas; em 2 colunas media baixo, o que
 * reelegia 3 colunas; e assim indefinidamente, sem redimensionamento nem
 * interação. Basta que um card mude de altura entre as duas larguras de coluna
 * candidatas — um título ou um valor que quebra numa e não na outra — para o
 * sistema deixar de ter ponto fixo. Se converge ou fica alternando depende
 * inteiramente do conteúdo, e o algoritmo não dava nenhuma garantia.
 *
 * Ordem de preferência: o maior número de colunas que cabe, com o card de
 * eventos ao lado sempre que couber. Uma coluna só existe empilhada — uma
 * coluna compacta ao lado do card de eventos produz compactos larguíssimos
 * espremendo um card de eventos estreito, o pior dos dois mundos — e é o
 * fallback que sempre cabe.
 */
export function composeLayout(sectionWidth: number): DashboardLayout {
  const besideCompactWidth = sectionWidth - GAP - eventsWidthWhenBeside(sectionWidth);
  for (const columnCount of [3, 2]) {
    if (fits(besideCompactWidth, columnCount)) return { columnCount, eventsBeside: true };
  }
  for (const columnCount of [3, 2]) {
    if (fits(sectionWidth, columnCount)) return { columnCount, eventsBeside: false };
  }
  return { columnCount: 1, eventsBeside: false };
}

/*
 * Distribuição em colunas por rodízio na ordem semântica dos cards: o primeiro
 * vai para a coluna 0, o segundo para a 1, e assim por diante. Determinística,
 * sem medir nada, e preserva a leitura da esquerda para a direita.
 *
 * A versão anterior enfileirava cada card na coluna de menor altura acumulada.
 * Com seis cards de alturas quase iguais (113 a 145px), qualquer variação
 * subpixel na medição trocava a coluna de um card — mesmo container, mesmos
 * dados, arranjo diferente. Como as colunas são `flex-1` e têm todas a mesma
 * largura, o equilíbrio que se perde aqui é desprezível: para 6 cards em 3
 * colunas o rodízio reproduz exatamente a distribuição que o algoritmo antigo
 * escolhia.
 */
export function assignToColumns(cards: CompactCardSpec[], columnCount: number) {
  const columns: CompactCardSpec[][] = Array.from({ length: columnCount }, () => []);
  cards.forEach((card, index) => columns[index % columnCount].push(card));
  return columns;
}

/*
 * Composição externa da fileira de indicadores: 6 cards compactos + o card de
 * eventos, como duas regiões sempre independentes (nunca um grid/linha
 * compartilhada entre eles — era isso que esticava os compactos até a altura
 * do card de eventos antes desta refatoração).
 *
 * A única medição que alimenta a decisão é a largura da própria seção, que
 * ninguém aqui dentro altera. Nenhuma altura renderizada é lida.
 */
export function AdaptiveDashboardSection({
  compactCards,
  eventsCard,
  debug = false,
}: {
  compactCards: CompactCardSpec[];
  eventsCard: ReactNode;
  /** Mostra um selo com a medição/decisão ao vivo — só para depuração visual. */
  debug?: boolean;
}) {
  const [sectionRef, sectionWidth] = useResizeSize<HTMLDivElement>("width", 1200);

  const layout = useMemo(() => composeLayout(sectionWidth), [sectionWidth]);
  const columns = useMemo(
    () => assignToColumns(compactCards, layout.columnCount),
    [compactCards, layout.columnCount]
  );

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
            largura por card compacto:{" "}
            {Math.round(
              ((layout.eventsBeside ? sectionWidth - GAP - eventsWidthWhenBeside(sectionWidth) : sectionWidth) -
                GAP * (layout.columnCount - 1)) /
                layout.columnCount
            )}
            px (mínimo {MIN_COMPACT_WIDTH}px)
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
            /* O índice é a identidade real da coluna: ela é uma posição fixa na
             * fileira, não um dado. Os cards, esses sim, são keyados por
             * `card.key` — trocar de coluna não pode remontar o card. */
            <div key={`coluna-${columnIndex}`} className="flex min-w-0 flex-1 flex-col items-start gap-[16px]">
              {column.map((card) => (
                <div key={card.key} data-compact-card={card.key} className="w-full">
                  {card.node}
                </div>
              ))}
            </div>
          ))}
        </div>

        <div>{eventsCard}</div>
      </section>
    </div>
  );
}
