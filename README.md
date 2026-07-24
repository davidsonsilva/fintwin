# FinTwin AI

Plataforma Web de simulação e prevenção financeira pessoal, com um motor financeiro determinístico e auditável no núcleo. Consulte `docs/Spec.md` para a especificação completa do produto.

> **VS-01 — Fundação do repositório e domínio.** Esta etapa entrega apenas a fundação do monorepo, os Value Objects `Money`/`Percentage`, as entidades de domínio e a subida via Docker Compose. Não há dashboard funcional, API de negócio nem persistência real ainda — essas capacidades chegam nas próximas Vertical Slices (veja seção 30 do Spec).

## Estrutura do repositório

```text
gemeo-financeiro/
├── apps/
│   ├── web/                 # Next.js + TypeScript estrito (scaffold mínimo)
│   └── api/
│       ├── src/
│       │   ├── domain/      # Money, Percentage, enums e entidades (sem dependência de framework)
│       │   │   ├── shared/
│       │   │   ├── financial_profile/
│       │   │   ├── cashflow/
│       │   │   ├── autonomy/        # vazio nesta slice (VS-05)
│       │   │   ├── fragility/
│       │   │   ├── decisions/
│       │   │   ├── obligations/
│       │   │   └── preventive_plans/
│       │   ├── application/ # casos de uso (vazio nesta slice, VS-02+)
│       │   ├── infrastructure/ # persistência/repositórios/IA (vazio nesta slice)
│       │   └── interfaces/http/main.py  # apenas endpoint /health nesta slice
│       ├── tests/unit/      # testes pytest de Money, Percentage e entidades
│       └── pyproject.toml
├── packages/contracts/       # tipos compartilhados (placeholder)
├── data/demo/                 # dados de demonstração (populados na VS-02)
├── docs/Spec.md               # especificação definitiva do MVP
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

## Pré-requisitos

- Docker Desktop (Windows)
- Python 3.12 (para rodar os testes fora do Docker)
- Node.js 20+ (para rodar o front-end fora do Docker)

## Como executar (Windows PowerShell)

1. Copiar as variáveis de ambiente:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Subir os serviços via Docker Compose:

   ```powershell
   docker compose up --build
   ```

   - API disponível em `http://localhost:8000/health`
   - Web disponível em `http://localhost:3000`
   - PostgreSQL disponível em `localhost:5432`

3. Encerrar os serviços:

   ```powershell
   docker compose down
   ```

## Como rodar os testes do back-end

Fora do Docker, usando um ambiente virtual Python 3.12:

```powershell
cd apps/api
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest -q
```

Ou, em ambientes com `make` disponível (ex.: Git Bash):

```bash
make test
```

## Regras de domínio implementadas nesta slice

- `Money`: usa `Decimal`, rejeita `float`, impede operações entre moedas diferentes, arredonda com `ROUND_HALF_UP` (2 casas), serializa como string.
- `Percentage`: fração `Decimal` entre 0 e 1, rejeita `float` e valores fora do intervalo.
- Entidades principais (`FinancialProfile`, `FinancialAccount`, `IncomeSource`, `FinancialObligation`, `Debt`, `FinancialGoal`, `FinancialEvent`, `Simulation`, `FragilityFinding`, `PreventivePlan`) com validação básica de invariantes, sem dependência de FastAPI/SQLAlchemy.

## Limitações intencionais desta slice

- Sem persistência real (SQLAlchemy/Alembic) — chega na VS-02.
- Sem onboarding, CRUD ou endpoints de negócio — chega na VS-02.
- Sem dashboard, gráficos, projeção, autonomia, fragilidade, simulador, planos ou agente — chegam a partir da VS-03.

## Próxima Vertical Slice

VS-02 — Persistência e onboarding.
