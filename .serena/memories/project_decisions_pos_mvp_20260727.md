# Decisões pós-MVP (registradas 2026-07-27, durante o polimento visual do dashboard)

Contexto: ao validar o dashboard contra `imagens/proposta-de-layout.png` (mockup original,
anterior à implementação das VS), o usuário pediu para eu auditar o que na imagem é real vs.
decorativo. Resultado da auditoria em `mem:gotcha/docker-web-sem-hot-reload` (sessão) — resumo
das decisões tomadas a partir dela:

## 1. Sem versão "Pro"
O card "FinTwin AI Pro / Upgrade agora" do mockup **não deve ser implementado**. Não há e não
haverá conceito de plano pago/billing/upgrade neste produto — decisão explícita do usuário,
não é uma lacuna a fechar. Se esse card aparecer em referências visuais futuras, ignorar/remover,
não tentar recriar como feature real.

## 2. Layout dos 3 gráficos em coluna — CONCLUÍDO (2026-07-29)
Reorganizado em `planning/redistribuicao-projecao-autonomia_20260728` (2ª rodada): donut +
linha + gauge na mesma linha, Projeção full-width, Autonomia virou cards compactos na grid de
indicadores, Próximos eventos virou 4ª coluna dessa grid. Validado visualmente pelo usuário.

## 3. "Evolução do saldo líquido" (histórico) — A IMPLEMENTAR, é feature nova de domínio
Confirmado pela investigação: **não existe** nenhum conceito de série histórica/snapshot de saldo
no backend (`apps/api/src/domain`) — só estado atual (`FinancialAccount.balance`) + projeção
futura (`domain/projection/engine.py`). Precisa de modelagem de domínio nova (ex.: snapshot
periódico do saldo líquido, provavelmente mensal) + endpoint novo + componente de gráfico de
linha no front (distinto do `ProjectionChart.tsx`, que projeta o FUTURO, não mostra o passado).
Usuário confirmou que quer isso implementado — não é só CSS, é uma slice de domínio nova.

## 4. Saudação personalizada por nome — A IMPLEMENTAR, é feature nova de domínio
Confirmado: `FinancialProfile` (`apps/api/src/domain/financial_profile/entities.py`) não tem
campo `name`/`display_name`, e não existe conceito de usuário/autenticação no domínio inteiro
(profile_id é livre nas rotas, é limitação conhecida documentada no README). Para a saudação
"Olá, {nome}!" funcionar de verdade (não ser decorativa/inventada), precisa adicionar um campo
de nome ao perfil (migração Alembic + schema + onboarding form) — não dá pra simplesmente pôr
"Davidson" fixo no código, violaria o princípio do projeto de nunca fingir dado real.

## 5. Card "Insight do seu Gêmeo Financeiro" → ação financeira concreta — A IMPLEMENTAR, feature
nova de domínio (registrado 2026-07-29, ainda SEM plano — usuário pediu só para guardar por agora)
Motivação: hoje "Insight" e "IA FinTwin" são pontos de entrada redundantes pro mesmo chat
(`openAgent`). Usuário quer que "Insight" pare de abrir o chat e passe a mostrar recomendação
acionável direto no card. Proposta completa do usuário está em
`imagens/Transformar a análise do FinTwin em uma ação financeira concreta.md` — não duplicar aqui,
ler o arquivo quando for planejar. Resumo do escopo (todo novo, não existe ainda no domínio):
- Motor calcula sobra mensal recorrente não comprometida (renda − despesas essenciais − obrigações
  − aporte atual da meta), quando comprometimento está numa faixa saudável.
- Recomendação principal: redirecionar um % adicional da renda pra meta principal (não é valor
  fixo tipo "+5%" — o motor calcula com base em renda/despesas/compromissos futuros/reserva de
  emergência/projeção de caixa do perfil real).
- 3 cenários comparáveis (conservador/recomendado/acelerado), cada um recalculando: nova data da
  meta, valor acumulado, impacto no saldo mensal, autonomia financeira restante, riscos, efeito
  sobre outras metas.
- Fluxo ao clicar "Ver recomendações": diagnóstico + dados usados + recomendação + simulação
  antes/depois + riscos/limitações + botões "Rejeitar" / "Simular outro valor" / "Aprovar plano".
- Aprovação é humana sempre — a IA nunca movimenta dinheiro sozinha (mesmo princípio de
  `Spec.md` sobre não fazer consultoria/investimento automatizado). "Aprovar plano" provavelmente
  significa só atualizar o aporte-alvo da meta no perfil, não uma transação real.
- Isso é da mesma categoria dos itens 3 e 4 acima: requer modelagem de domínio nova (não dá pra
  fingir com dado estático no front), então antes de implementar precisa passar por
  `/discutir-tarefa` pra desenhar a regra de cálculo, o endpoint e a persistência da decisão —
  usuário optou por só registrar a pendência nesta sessão, não abrir o planejamento ainda.

## Ordem de execução acordada
Usuário decidiu **continuar primeiro o polimento visual** (cards/CSS/CVA) e tratar os itens 3-5
como trabalho futuro registrado. Item 2 já foi concluído. Ver
`mem:planning/design-system-css-para-cva-e-meta-harness_20260727` para o estado da migração CVA.
