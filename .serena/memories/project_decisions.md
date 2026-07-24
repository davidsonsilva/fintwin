# FinTwin AI — Decisões de Projeto (atualizado 2026-07-23)

## VS-02 — Onboarding: visual está propositalmente cru, polish adiado
- O wizard de onboarding (VS-02) foi entregue com UI funcional mas visualmente simples (formulários shadcn/ui básicos, sem refinamento de design).
- **Feedback do usuário**: "Achei muito simples esse onboard!" — confirmado que o problema é visual/design, não funcional. Usuário decidiu explicitamente adiar a melhoria: "Depois vamos melhorar esse layout certo?"
- **Decisão**: o polish visual do onboarding fica para uma passada dedicada futura, usando a skill `/ui-material3` (padrão definido no CLAUDE.md do projeto para paineis internos do FinTwin — Hallmark é só para landing pages externas). Não bloqueia o fechamento da VS-02.
- **Como aplicar**: ao retomar esse trabalho, rodar `/ui-material3` sobre `apps/web/src/features/onboarding/` e `apps/web/src/app/onboarding/page.tsx`. Não confundir com trabalho de VS-03 (dashboard) — é um retrofit da VS-02.

## VS-02 — Bugs reais encontrados durante verificação com Docker real (não SQLite de teste)
- **Dockerfile da API não copiava `alembic.ini`/`alembic/`** para a imagem — só `pyproject.toml` e `src/`. Corrigido: `apps/api/Dockerfile` agora copia ambos. Sem isso, `alembic upgrade head` falhava com "No 'script_location' key found".
- **Path resolution do `data/demo/` quebrava dentro do container**: `demo_use_cases.py` calculava `DEMO_DIR` via `Path(__file__).resolve().parents[5]`, que só funciona em dev local (repo inteiro presente). Em Docker, o build context da API é só `apps/api/`, então `data/` nem existe na imagem. Corrigido com env var `DEMO_DATA_DIR` (fallback seguro para local dev) + volume mount `./data/demo:/app/data/demo:ro` no `docker-compose.yml` + env `DEMO_DATA_DIR: /app/data/demo` no serviço `api`.
- **CORS não configurado**: front-end (`localhost:3000`) chamando a API (`localhost:8000`) era bloqueado por CORS no browser (erro só aparecia em teste manual, não em testes automatizados com `TestClient`, que não simula CORS). Corrigido com `CORSMiddleware` em `apps/api/src/interfaces/http/main.py` (`allow_origins=["http://localhost:3000"]`).
- **Lição geral**: testes automatizados com SQLite in-memory e `TestClient` (sem navegador real) não pegam esses 3 bugs — só apareceram ao rodar `docker compose up` de verdade e testar manualmente no navegador. Fluxo de verificação da VS-02 (seção 33/`.agents/personas/principal-fintwin-engineer.md`) que exige "rodar uma demonstração real" continua sendo essencial, não apenas formalidade.

## Front-end — shadcn/ui neste projeto usa Base UI, não Radix
- A versão do shadcn/ui instalada (`shadcn@^4.14.0`) usa `@base-ui/react` como base, não Radix UI. O padrão `asChild` do Radix não é suportado da mesma forma (Base UI usa prop `render` em vez de `asChild` em alguns componentes) — gera warning no console React se usado incorretamente.
- O componente `form` do shadcn (wrapper para react-hook-form) não está disponível neste registry/versão — os formulários do onboarding usam react-hook-form diretamente com os primitivos (Input/Label/Select/Checkbox/Card).
- **Armadilha confirmada por `apps/web/AGENTS.md`**: esta versão do Next.js (16.2.11) e do toolchain relacionado têm breaking changes reais vs. conhecimento de treinamento — sempre verificar `node_modules/next/dist/docs/` antes de assumir comportamento padrão.
