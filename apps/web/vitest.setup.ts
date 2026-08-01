import "@testing-library/jest-dom/vitest";

// jsdom não implementa ResizeObserver (usado por gráficos com densidade de
// eixo responsiva). Stub sem-op: os testes não dependem de resize real, só
// precisam que `new ResizeObserver(...)` não lance.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver ??= ResizeObserverStub as unknown as typeof ResizeObserver;
