O piloto foi um sucesso porque revelou exatamente onde o desenho teórico não correspondia ao comportamento real da CLI.

A arquitetura deve ser atualizada para refletir o que funcionou na prática.

## Veredito

**O Meta Harness está validado como revisor estático independente, mas não como executor completo de quality gates.**

Ele já provou valor ao encontrar quatro bugs HIGH reais que passaram pela implementação inicial. Isso justifica manter o fluxo.

## Novo desenho correto

```text
Claude implementa
→ executa testes, lint, typecheck e demo no ambiente normal
→ cria commit de checkpoint
→ Meta Harness chama codex review com prompt customizado
→ Codex compara pai..checkpoint
→ Codex faz revisão estática independente
→ Claude corrige findings
→ executa novamente os quality gates
→ cria novo checkpoint
→ Codex revalida
→ commit final ou squash
```

A separação passa a ser:

### Claude

Responsável por evidências executáveis:

* pytest;
* Vitest;
* lint;
* typecheck;
* build;
* demo real;
* validação Docker, quando aplicável.

### Codex Review

Responsável por revisão independente:

* diff delimitado;
* regras de negócio;
* aderência à Spec;
* regressões;
* erros lógicos;
* contratos;
* validação;
* persistência;
* cobertura ausente;
* qualidade arquitetural.

Não devemos insistir para que `codex review` execute testes se o subcomando é read-only e seu ambiente não oferece as dependências necessárias.

## O commit de checkpoint agora é obrigatório

A descoberta elimina a estratégia baseada apenas em working tree.

Use dois tipos de commit durante a slice:

```text
checkpoint(vs-07): implementation candidate
fix(vs-07): address codex findings
```

Depois da aprovação, você pode manter esses commits para auditoria ou fazer squash:

```text
feat(vs-07): implement financial decision simulation
```

Para o seu contexto de governança e evidência, eu manteria os commits separados inicialmente. Eles mostram:

* implementação original;
* findings encontrados;
* correções realizadas;
* revalidação.

## Escopo do diff

O prompt deve receber explicitamente:

```text
Base commit: <pai>
Target commit: <checkpoint>
```

E instruir:

```bash
git diff <base>..<target>
git diff --stat <base>..<target>
git show --name-only <target>
```

Assim o Codex não revisa as 27 mil linhas do repositório como escopo primário. Ele pode consultar o restante apenas para contexto.

Se ele realmente processou cerca de 27 mil linhas, vale reforçar no prompt:

```md
Analise prioritariamente apenas o diff entre BASE_COMMIT e TARGET_COMMIT.

Não faça uma auditoria geral do repositório.

Leia arquivos fora do diff somente quando forem necessários para:
- compreender contratos;
- confirmar uma regressão;
- validar uma regra de domínio;
- verificar chamadas afetadas.

Não reporte problemas preexistentes fora do escopo, exceto quando a alteração atual:
- os agravar;
- depender deles;
- tornar o build impossível;
- ou declarar falsamente que os quality gates estão verdes.
```

Isso deve reduzir quota e tempo.

## O formato nativo não é um problema

Não vale lutar contra o formato nativo do `codex review` neste momento.

Crie um pequeno normalizador após a revisão:

```text
Saída nativa do Codex
→ parser/normalizador local
→ relatório do Meta Harness
```

O normalizador pode extrair:

* prioridade;
* arquivo;
* linha;
* descrição;
* recomendação;
* quantidade por severidade;
* veredito derivado.

Regra simples:

```text
P0 ou P1 / HIGH ou BLOCKER → REJECTED
P2 / MEDIUM sem HIGH       → APPROVED_WITH_WARNINGS
Somente LOW/INFO           → APPROVED
Sem findings               → APPROVED
```

Não precisa usar outra chamada de IA para isso. Faça deterministicamente no script.

## Quality gates preexistentes

O Codex está correto ao tratar `lint` e `tsc` quebrados como problemas reais, mas o Meta Harness precisa distinguir duas categorias:

```text
NEW_FAILURE
PRE_EXISTING_FAILURE
```

Uma falha preexistente não deve ser escondida, mas também não deve ser atribuída automaticamente à VS atual.

Sugestão de política:

* `NEW_FAILURE`: bloqueia a slice.
* `PRE_EXISTING_FAILURE_AFFECTED`: bloqueia se a slice tocar ou depender da área.
* `PRE_EXISTING_FAILURE_UNRELATED`: warning obrigatório.
* `PRE_EXISTING_FAILURE_WORSENED`: bloqueia.

O ideal é registrar uma baseline antes da implementação:

```text
.meta-harness/baselines/vs-07-before.json
```

Exemplo:

```json
{
  "lint": {
    "exitCode": 1,
    "knownFailures": [
      "src/resourceConfigs.ts"
    ]
  },
  "typecheck": {
    "exitCode": 1,
    "knownFailures": [
      "erro preexistente A",
      "erro preexistente B"
    ]
  },
  "tests": {
    "exitCode": 0
  }
}
```

Depois da implementação, o harness compara antes e depois.

## Os quatro HIGH encontrados

Todos parecem legítimos e devem bloquear a VS-07:

1. **LOAN sem entrada do principal**
   Erro de regra financeira central. A simulação fica economicamente incorreta.

2. **Custo recorrente contabilizado apenas uma vez**
   Subestima o custo total e pode induzir uma decisão errada.

3. **Ausência de validação por tipo de decisão**
   Erro de contrato e API: entrada inválida não deve virar erro interno 500.

4. **`scenario_override` não persistido**
   Violação direta da Spec e perda de rastreabilidade da simulação.

O finding de lint e os erros preexistentes de TypeScript devem ser classificados separadamente, conforme a baseline.

## Estrutura revisada

```text
.meta-harness/
├─ prompts/
│  └─ codex-review.md
├─ contracts/
│  ├─ current-slice.md
│  └─ acceptance-criteria.md
├─ baselines/
│  └─ vs-07-before.json
├─ raw/
│  └─ codex-review-<timestamp>.txt
├─ reports/
│  └─ codex-review-<timestamp>.md
├─ state/
│  └─ current-review.json
└─ config.json

scripts/
├─ capture-baseline.sh
├─ validate-step.sh
└─ normalize-codex-review.py
```

## Decisões que devem ser alteradas na memória

Substitua:

```text
codex review --uncommitted
```

por:

```text
codex review com prompt customizado e commits explícitos de base e target
```

Substitua:

```text
workspace-write para execução real de testes
```

por:

```text
codex review read-only para análise estática;
quality gates executados previamente pelo Claude no ambiente normal;
resultados anexados ao contexto da revisão.
```

Substitua:

```text
relatório no template produzido diretamente pelo Codex
```

por:

```text
saída nativa preservada em raw/;
relatório padronizado gerado deterministicamente pelo harness.
```

E registre:

```text
Checkpoint por slice é obrigatório para delimitar o diff.
```

## Aprovação

O piloto cumpriu seu objetivo e encontrou falhas materiais. **Pode corrigir os quatro HIGH e atualizar o Meta Harness com esse desenho revisado.**

Não fixe ainda o `gpt-5.6-terra + high` como padrão definitivo. Faça pelo menos mais duas medições:

* uma slice pequena;
* uma slice média após restringir explicitamente o escopo ao diff.

O dado mais importante agora não é dólar, mas **quota consumida, duração e quantidade de findings úteis por revisão**.
