# FinTwin AI

Plataforma Web de simulação e prevenção financeira pessoal. O núcleo é um
motor financeiro determinístico e auditável (projeção de fluxo de caixa,
autonomia financeira, radar de fragilidade, simulador de decisões, planos
preventivos); o agente conversacional é uma camada sobre esse motor, nunca o
substitui — toda resposta do agente que contenha números vem de uma chamada
real a um caso de uso, nunca de cálculo do próprio modelo de linguagem.

Especificação completa do produto: [`docs/Spec.md`](docs/Spec.md).
Visão de arquitetura e fluxo de dados: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Demonstração em vídeo

[youtu.be/iuUjemtm7f4](https://youtu.be/iuUjemtm7f4) — onboarding, dashboard,
radar de fragilidade, simulador de decisões, planos preventivos e agente
conversacional.

## Status

MVP completo (VS-01 a VS-10, ver seção 30 do Spec para a ordem das Vertical
Slices e seção 31 para os critérios de aceitação).

## Segurança — leia antes de expor a aplicação

Este projeto é um **MVP de demonstração para rodar localmente**, não um
serviço pronto para produção multiusuário. Especificamente:

- **Não há autenticação.** Qualquer chamada à API que informe um `profile_id`
  válido lê e escreve os dados daquele perfil — não há verificação de dono.
- **CORS aceita credenciais** (`allow_credentials=True`) com origens
  configuráveis por `CORS_ALLOW_ORIGINS`; inócuo sem sessão, mas exige
  atenção antes de introduzir autenticação.
- **Rate limit é em memória, por processo** — protege apenas contra abuso
  trivial do endpoint pago da Anthropic num único worker; não é um limitador
  distribuído.
- **Credenciais padrão do Postgres** (`fintwin`/`fintwin` em
  `.env.example`) servem só para desenvolvimento local.

**Não exponha esta instância na internet pública sem antes adicionar
autenticação e revisar CORS/rate limit.** Detalhes completos na seção
"Limitações conhecidas" abaixo.

## Arquitetura

- **Back-end** (`apps/api`): Python 3.12, FastAPI, Pydantic, SQLAlchemy,
  Alembic, PostgreSQL. Domínio financeiro isolado de framework, banco e
  front-end (`src/domain` → `application` → `infrastructure` → `interfaces`).
  Todo valor monetário usa `Decimal`, nunca `float`.
- **Front-end** (`apps/web`): Next.js 16 (App Router), TypeScript, Tailwind
  v4, shadcn/ui (Base UI), Recharts, TanStack Query. Sem regra financeira no
  front-end — ele só exibe o que a API calculou.
- **Agente conversacional**: chamada direta à API da Anthropic (Claude Haiku
  4.5, tool calling nativo), sem LangChain/LangGraph. Tools de leitura
  (`get_dashboard_summary`, `get_autonomy`, `list_fragilities`) e uma tool de
  proposta (`propose_simulation`) que nunca persiste sozinha — toda ação
  proposta pelo agente exige confirmação explícita do usuário antes de gravar
  qualquer dado.

## Estrutura do repositório

```text
gemeo-financeiro/
├── apps/
│   ├── web/                 # Next.js + TypeScript
│   └── api/
│       ├── src/
│       │   ├── domain/          # regras financeiras, sem dependência de framework
│       │   ├── application/     # casos de uso
│       │   ├── infrastructure/  # persistência, repositórios, cliente da Anthropic
│       │   └── interfaces/http/ # routers, schemas FastAPI
│       ├── alembic/             # migrações do banco
│       └── tests/               # unit + integration (pytest)
├── data/demo/                # dados de demonstração
├── docs/Spec.md               # especificação definitiva do MVP
├── docker-compose.yml
└── README.md
```

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (inclui
  Docker Compose) — testado no Windows 11.
- Uma chave de API da Anthropic (opcional — só necessária para usar o agente
  conversacional; o resto do produto funciona sem ela).

## Como rodar (Windows, PowerShell)

```powershell
# 1. Clonar o repositório e entrar na pasta
git clone <url-do-repositorio>
cd gemeo-financeiro

# 2. (Opcional) configurar a chave da Anthropic para o agente conversacional.
#    Crie um arquivo .env na raiz do projeto (o Docker Compose carrega
#    automaticamente):
#    ANTHROPIC_API_KEY=sk-ant-...

# 3. Subir os containers (Postgres + API + Web)
docker compose up -d --build

# 4. Aplicar as migrações do banco (necessário na primeira vez e sempre
#    que houver uma migração nova)
docker compose exec api python -m alembic upgrade head
```

A aplicação fica disponível em:

- Web: http://localhost:3000
- API: http://localhost:8000 (health check em `/health`)

Para reaplicar código depois de alterar algo, repita o passo 3
(`docker compose up -d --build`) — containers já em execução não recarregam
código novo sozinhos.

Para encerrar:

```powershell
docker compose down
```

## Como rodar os testes

### Back-end (pytest)

```powershell
cd apps/api
.venv\Scripts\python.exe -m pytest -q
```

Se o `.venv` não existir (ambiente Python 3.12):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Front-end (vitest)

```powershell
cd apps/web
npm test
```

### End-to-end (Playwright)

Requer a stack completa rodando via Docker Compose (seção anterior).

```powershell
cd apps/web
npx playwright test
```

## Demonstração ponta a ponta

Roteiro manual reproduzível para validar o produto completo — do onboarding
até a geração de um plano preventivo. Assume a stack rodando conforme "Como
rodar" acima.

1. Abra http://localhost:3000 e complete o onboarding (ou carregue os dados
   de demonstração, se a tela oferecer essa opção) para obter um perfil com
   contas, rendas, obrigações, dívidas e metas de exemplo (`data/demo/`).
2. No dashboard do perfil, confira o resumo (saldo, projeção de 12 meses,
   gráfico, primeiro déficit projetado) e a autonomia financeira (básica e
   ajustada).
3. Abra o radar de fragilidade e confirme que há fragilidades detectadas,
   cada uma com evidência associada (não apenas um rótulo).
4. Clique em "Simular decisão", escolha um tipo de decisão (ex.: compra à
   vista), preencha os parâmetros e veja a comparação antes/depois.
5. Abra "Planos preventivos", gere planos a partir das fragilidades
   detectadas e aprove um deles — confirme que o status muda.
6. Abra o painel do agente conversacional (lateral, no dashboard) e peça um
   resumo da situação financeira — confirme que os valores respondidos
   batem com o dashboard (evidência real, não invenção).

## Limitações conhecidas

- **Não é um produto de Open Finance nem de investimentos.** Não há conexão
  com fontes financeiras externas, não há recomendação de investimentos —
  decisões arquiteturais deliberadas da Spec (seção 32).
- **Sem autenticação de usuário.** O `profile_id` é passado livremente nas
  rotas; qualquer pessoa com acesso à API pode ler/escrever qualquer perfil.
  Aceitável para um MVP de demonstração local, não para produção
  multiusuário.
- **`calculate_autonomy` é independente de renda e de serviço de dívida** —
  mede apenas ativos vs. despesas essenciais. Decisões que só afetam renda ou
  dívida não mudam a autonomia calculada; o efeito aparece somente no fluxo
  de caixa projetado.
- **O agente conversacional não lista renda/obrigações via tool própria** —
  cenários como "perda de renda" ou "provisionar um imposto anual" exigem que
  o usuário informe os valores manualmente na conversa, em vez do agente
  buscá-los sozinho.
- **O agente não compara cenários nem gera planos preventivos diretamente** —
  essas ações continuam disponíveis pela UI padrão (fora do agente); a
  integração do agente com esses fluxos foi adiada para uma iteração futura.
- **Rate limit do endpoint do agente é em memória, por processo** — não
  sobrevive a múltiplos workers/réplicas nem a reinícios; suficiente para
  mitigar abuso trivial num MVP de instância única, não é um limitador
  distribuído.
- **Migrações do banco não rodam automaticamente ao subir os containers** —
  é necessário `docker compose exec api python -m alembic upgrade head`
  manualmente após cada `docker compose up`.

## Licença

Este projeto está licenciado sob a GNU Affero General Public License
v3.0 (`AGPL-3.0-only`).

Para uso comercial sob termos diferentes, entre em contato com o autor.
