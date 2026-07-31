# Índice de memórias — FinTwin AI (gemeo-financeiro)

Mapeia **área do código → memória**. Serve para o portão de entrada: antes do primeiro `Edit`
em qualquer arquivo, procure a linha que cobre esse caminho e leia a memória apontada.

Nomes de memória são por *assunto + data da conversa*, então o nome sozinho não diz onde a
decisão se aplica. É para isso que este arquivo existe.

> **Manutenção**: ao consolidar um `planning/*` novo, adicione a linha correspondente aqui.
> Índice desatualizado entrega lixo para o portão, o que é pior do que não ter portão.

## Design system e UI

| Área / arquivos | Memória | O que ela decide |
|---|---|---|
| `apps/web/src/app/design-system.css`, `apps/web/src/design-system/**` | `planning/migracao-css-cva-fechada_20260731` | **Leia antes de tocar em qualquer classe `.ft-*`.** Migração CSS→CVA FECHADA. Regra dura: componente novo só entra se a regra global sair no mesmo commit. Migração = zero mudança visual, incluindo curva de transição. Método de fidelidade (`git show HEAD:`). Lista do que NÃO repetir (`min-h-[2lh]`, `min-h-[2.75em]`). |
| idem, escopo histórico | `planning/design-system-css-para-cva-e-meta-harness_20260727` | Escopo original da migração e o que foi **deliberadamente excluído**: Onboarding e AgentPanel — *não reavaliar sem novo motivo*. |
| `apps/web/src/app/design-system.css`, `components/shell/**` (AppShell, Sidebar, PageHeader) | `planning/redesign-layout-fintwin_20260724` | Fonte de verdade visual do projeto: design system próprio `--ft-*`, dark-only. **Este projeto não segue MD3** (exceção à regra global). |
| `features/onboarding/**`, `components/shell/PageHeader.tsx` | `planning/polish-visual-inicial-onboarding_20260727` | Polimento visual, hierarquia tipográfica, coordenadas do toolbar. |
| `.ft-grid--indicators`, altura de card em grid | `global/css-grid-spanning-item-dita-altura-das-linhas` | Por que `grid-auto-rows: 1fr` fazia um card ditar a altura dos outros. |
| Qualquer trabalho visual comparando com `imagens/**` | `feedback/comparar-assets-visuais-antes-de-reusar` | Conferir o asset antes de reusar. |

## Dashboard

| Área / arquivos | Memória | O que ela decide |
|---|---|---|
| `features/dashboard/**` (gráficos, snapshots, categorias) | `planning/dashboard-3-graficos-linha_20260727` | Donut de despesas, evolução do saldo, gauge de comprometimento. `BalanceSnapshot` e endpoints. |
| `features/dashboard/ProjectionChart.tsx`, `AutonomyPanel.tsx` | `planning/redistribuicao-projecao-autonomia_20260728` | Reposicionamento e divisão de responsabilidade entre os dois. |
| `features/dashboard/**` — responsividade | `planning/responsividade-dashboard_20260730` | ⚠️ **SUPERSEDED** — contém 4 hipóteses refutadas. A conclusão real está em `planning/migracao-css-cva-fechada_20260731`. Contém pendências herdadas ainda abertas (`recurrence` ignorado, ano do evento escondido). |
| Frente de **layout de cards** (MetricCard, EventsCard, AnalyticsCard, Sidebar) | `planning/temp_card-variantes-e-grid-indicadores_20260731` | Diretriz do Davidson: card com partes definidas, dono da própria altura e reação à largura (container query, não media query global). **PARADA por decisão dele** até ele retomar. |

## Backend / domínio

| Área / arquivos | Memória | O que ela decide |
|---|---|---|
| `apps/api/**` — decisões arquiteturais | `project_decisions`, `project_decisions_pos_mvp_20260727` | Arquitetura em camadas, motor determinístico, o que não pode virar heurística. |
| `apps/api/**` — agente conversacional | `planning/vs09-agente-conversacional_20260725` | Leitura, proposta e confirmação de ação; guard anti-número-sem-evidência. |
| `apps/api/**` — consolidação do MVP | `planning/vs10-consolidacao-mvp_20260726` | E2E, acessibilidade, hardening. |

## Processo e ferramentas

| Área / arquivos | Memória | O que ela decide |
|---|---|---|
| `.meta-harness/**`, `scripts/validate-step.sh` | `planning/meta-harness_20260724` + seção do `planning/migracao-css-cva-fechada_20260731` | Como o harness funciona de fato. **`current-slice.md` e `acceptance-criteria.md` se atualizam JUNTOS** — contrato desatualizado faz o Codex rejeitar código correto. Limitação atual: o sandbox não roda pytest/vitest/build (NOT_VERIFIED sempre). |
| `apps/api/pyproject.toml`, `apps/api/Dockerfile`, `apps/api/.venv`, qualquer coisa que envolva versão de Python | `gotcha/pythons-instalados-e-versao-do-projeto` | Projeto fixado em **3.12** (pyproject + Dockerfile); a venv funciona (201 testes passam). `pytest` como NOT_VERIFIED no Meta Harness é o sandbox read-only, **não** venv quebrada. A máquina tem 6 instalações de Python, uma fantasma — limpeza adiada por decisão do Davidson. |
| `docker-compose.yml`, qualquer verificação visual de `apps/web` | `gotcha/docker-web-sem-hot-reload` | **`docker compose build web && up -d web` antes de olhar qualquer mudança.** Sem isso a comparação visual é inútil. |
| Sistema de memória, hooks, `ai-dev-template` | `planning/temp_20260731_115424` | Task do portão de entrada da memória. Regra: **toda mudança global passa pelo `ai-dev-template`**, nunca por um projeto. |
| Convenções de código | `coding_conventions` | Estilo, nomenclatura, padrões do projeto. |
| Estrutura do codebase | `graphify_architecture`, `project_overview` | Mapa estrutural e visão geral. |
| Como trabalhar com o Davidson | `global/estilo-de-trabalho-davidson` | Estilo de comunicação, o que ele corrige, o que espera antes de commitar. |
| Licenciamento e remote | `planning/copyright-agpl-e-remote-github_20260727` | Cabeçalho AGPL-3.0 obrigatório em arquivo novo. |

## Temporárias (consolidar ou apagar)

- `planning/temp_polish-dashboard-11-itens_20260729` — nunca consolidada
- `planning/temp_card-variantes-e-grid-indicadores_20260731` — frente de layout, parada
- `planning/temp_20260731_115424` — portão de memória, em execução no `ai-dev-template`
