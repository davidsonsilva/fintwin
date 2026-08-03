import { describe, expect, it } from "vitest";

import { assignToColumns, composeLayout, type CompactCardSpec } from "../AdaptiveDashboardSection";

/*
 * Regressão do bug de oscilação: a composição da fileira de indicadores era
 * decidida pontuando ALTURAS medidas, e a altura de um card depende da largura
 * da coluna que a própria decisão define. Estes testes fixam o contrato que
 * elimina o laço: a composição é função pura da largura da seção.
 */

const CARDS: CompactCardSpec[] = [
  "autonomia-basica",
  "autonomia-provavel",
  "autonomia-adversa",
  "perda-de-renda",
  "proximo-deficit",
  "fragilidades",
].map((key) => ({ key, node: null }));

describe("composeLayout", () => {
  it("devolve sempre o mesmo resultado para a mesma largura", () => {
    for (let width = 320; width <= 2200; width += 1) {
      expect(composeLayout(width)).toEqual(composeLayout(width));
    }
  });

  it("nunca produz cards compactos abaixo da largura mínima", () => {
    for (let width = 320; width <= 2200; width += 1) {
      const { columnCount, eventsBeside } = composeLayout(width);
      if (columnCount === 1) continue; // fallback: sempre cabe, por definição
      const available = eventsBeside ? width - 16 - Math.max(320, ((width - 16) * 1.1) / 4.1) : width;
      const cardWidth = (available - 16 * (columnCount - 1)) / columnCount;
      expect(cardWidth, `largura de card em ${width}px`).toBeGreaterThanOrEqual(260);
    }
  });

  it("é monotônica dentro de cada modo: alargar nunca reduz o número de colunas", () => {
    /*
     * Alargar a seção e ganhar MENOS colunas dentro do mesmo modo é o que um
     * algoritmo alimentado por alturas medidas fora de contexto produz — a
     * decisão passa a depender do que foi renderizado antes, não da largura.
     *
     * A comparação é por modo porque a passagem de "eventos embaixo" para
     * "eventos ao lado" legitimamente devolve largura ao card de eventos e pode
     * custar uma coluna à área compacta: em 871px a fileira dá 3 colunas de
     * 280px com os eventos embaixo, e em 872px dá 2 colunas de 260px com os
     * eventos ao lado. Isso é uma decisão de composição, não uma inversão.
     */
    const lastByMode = new Map<boolean, number>();
    for (let width = 320; width <= 2200; width += 1) {
      const { columnCount, eventsBeside } = composeLayout(width);
      const previous = lastByMode.get(eventsBeside);
      if (previous !== undefined) {
        expect(columnCount, `regressão de colunas em ${width}px (ao lado=${eventsBeside})`).toBeGreaterThanOrEqual(
          previous
        );
      }
      lastByMode.set(eventsBeside, columnCount);
    }
  });

  it("nunca coloca uma única coluna compacta ao lado do card de eventos", () => {
    for (let width = 320; width <= 2200; width += 1) {
      const layout = composeLayout(width);
      expect(layout.columnCount === 1 && layout.eventsBeside).toBe(false);
    }
  });
});

describe("assignToColumns", () => {
  it("distribui por rodízio, sem reordenar os cards", () => {
    const columns = assignToColumns(CARDS, 3);
    expect(columns.map((c) => c.map((card) => card.key))).toEqual([
      ["autonomia-basica", "perda-de-renda"],
      ["autonomia-provavel", "proximo-deficit"],
      ["autonomia-adversa", "fragilidades"],
    ]);
  });

  it("não perde nem duplica cards em nenhuma quantidade de colunas", () => {
    for (const columnCount of [1, 2, 3]) {
      const keys = assignToColumns(CARDS, columnCount)
        .flat()
        .map((card) => card.key);
      expect(keys.sort()).toEqual(CARDS.map((card) => card.key).sort());
    }
  });
});
