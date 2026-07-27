# Critérios de aceitação: VS-10 — Consolidação do MVP

> Extraído da seção "Critérios de Aceite" do plano aprovado em `planning/vs10-consolidacao-mvp_20260726`.

1. **E2E real contra a stack**: `apps/web/e2e/critical-flow.spec.ts` (Playwright) roda contra Docker Compose real (não mocka backend) e cobre onboarding→dashboard→simulação→comparação→detecção de fragilidades→geração e aprovação de plano preventivo — sem passar pelo agente conversacional (evita não-determinismo de chamada real à Anthropic).
2. **Acessibilidade**: `@axe-core/playwright` integrado ao E2E, sem violações `critical`/`serious` em nenhum dos 4 pontos varridos (dashboard, simulação, fragilidades, planos); violações encontradas foram corrigidas no código, não silenciadas/excluídas do scan.
3. **Segurança — sem regressão, com hardening pontual**: CORS permanece restrito a `http://localhost:3000`; nenhuma chamada de log/print expõe `ANTHROPIC_API_KEY` em nenhum ponto do código; endpoint `POST /agent/messages` (único que chama a API paga da Anthropic) ganhou rate limit (`RateLimiter`, 20 req/60s por IP) sem quebrar nenhum teste de integração existente do agente.
4. **Sem autenticação de usuário adicionada**: nenhuma mudança de escopo para login/autorização — não é critério de aceite da seção 31; limitação documentada explicitamente no README.
5. **README.md na raiz**: existe, cobre setup Docker/Windows (PowerShell), como rodar cada suíte de testes (pytest, vitest, playwright), roteiro de demonstração ponta a ponta reprodutível manualmente (distinto do teste automatizado), e uma seção "Limitações conhecidas" não vazia.
6. **Nenhuma regressão de domínio/aplicação/interface**: os 185 testes de backend pré-existentes + os 34 de frontend continuam passando; únicos testes novos são os 4 do `RateLimiter` (`tests/unit/test_rate_limit.py`) e o spec E2E — nenhuma mudança em regra de negócio, caso de uso ou contrato HTTP já entregue em slice anterior.
7. **Pureza de domínio preservada**: nenhuma mudança nesta slice toca `src/domain/`; toda alteração de back-end está em `interfaces/http/` (rate limit) — sem regra financeira nova nem alterada.
8. **Sem scope creep**: nenhuma feature de produto nova (nem no domínio, nem no agente); mudanças de front-end limitadas a acessibilidade (`aria-label`) e infraestrutura de teste (Playwright/vitest config).
9. **Migração de banco**: nenhuma migração Alembic nova nesta slice (sem mudança de schema).
10. **Fluxo manual real**: seguir o roteiro do README (onboarding via demo → dashboard → simulação → fragilidades → planos → agente) via `docker compose`, confirmando que cada etapa funciona como documentado.
