---
name: graphify_architecture
description: Grafo de conhecimento gerado pelo /graphify sobre o codebase gemeo-financeiro (2026-07-25)
metadata:
  type: project
---

# Grafo de conhecimento do projeto (graphify)

Rodado em 2026-07-25: `graphify-out/graph.json`, `graphify-out/graph.html`, `graphify-out/GRAPH_REPORT.md`.

- **1343 nodes · 3368 edges · 109 comunidades** (grafo **direcionado** — `DiGraph`, source→target preservado).
- Corpus: 261 arquivos (226 código, 35 docs), ~64.950 palavras.
- God nodes: `Money` (148 arestas), `Recurrence` (42), `Percentage` (41), `DecisionContext` (33), `project_cashflow()` (33), `FragilityContext` (32), `calculate_autonomy()` (29).
- `Money` é hub cross-community esperado: value object compartilhado por todas as entidades de domínio (contas, dívidas, obrigações, eventos, metas) e por toda a camada de repositórios/casos de uso — não é acoplamento acidental, é o desenho pretendido (motor determinístico, "sem números inventados").

## Correção aplicada nesta sessão
O grafo foi construído inicialmente com `directed=False` (undirected), o que descartava a direção real das arestas source→target ao consultar/exportar. Foi reconstruído com `directed=True`, reaproveitando a extração AST + cache semântico (sem re-rodar subagents). Confirmado: `SimulationOutcome --uses--> AutonomyResult` (direção correta, `decisions/engine.py:L17`).

**Gotcha para próximas execuções de `/graphify` neste projeto (Windows/PowerShell):**
- `python3` puro não funciona neste ambiente (alias da Microsoft Store) — sempre usar o interpretador salvo em `graphify-out/.graphify_python` (instalado via `uv tool install graphifyy`).
- Scripts Python que chamam `graphify.extract.extract()` com multiprocessing **precisam** de `if __name__ == "__main__":` guard, senão quebra o spawn no Windows.
- f-strings com aspas duplas aninhadas dentro de heredocs PowerShell (`@'...'@`) quebram — preferir escrever um arquivo `.py` via Write e rodar com `& $PY script.py` em vez de `-c "..."` inline para blocos com f-strings complexos.
- Sem `GEMINI_API_KEY`/`GOOGLE_API_KEY` configurada — extração semântica cai para subagents Claude via Agent tool (`general-purpose`, nunca `Explore`).

## Amostra de qualidade da extração (verificada manualmente)
Arestas INFERRED do tipo `uses` tendem a acertar a existência da relação mas às vezes generalizam demais o tipo de relação (ex.: um vínculo temático/conceitual rotulado como "uses" estrutural quando na verdade é só mesma-área-de-domínio). Direção agora é confiável após o fix; o rótulo de relação ainda vale checar no código antes de confiar cegamente.
