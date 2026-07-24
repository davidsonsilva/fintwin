# FinTwin AI — Convenções de Código

Ainda não há código de produto no repositório (apenas scaffold do template). Convenções abaixo são as exigidas pela especificação (`docs/Spec.md` seções 22-23) e deverão ser seguidas desde a VS-01:

- **Back-end (Python)**: domínio sem dependência de FastAPI/SQLAlchemy; `Decimal` para todo valor monetário (nunca `float`); casos de uso explícitos na camada de aplicação; repositórios definidos por interface; validação Pydantic apenas na borda (API); relógio injetável (não usar `datetime.now()` direto no domínio); respostas HTTP versionadas (`v1`).
- **Front-end (TypeScript)**: TypeScript estrito; zero lógica financeira no front-end (toda regra vem da API); schemas Zod compartilhados para validação de formulários; separação por feature (não por tipo de arquivo); tratamento explícito de estados loading/empty/success/error.
- **Geral**: nenhuma abstração especulativa; não implementar além da Vertical Slice ativa; evidências obrigatórias em qualquer fragilidade/alerta gerado.

Atualizar esta memória com padrões reais observados assim que o código da VS-01 existir.
