#!/usr/bin/env bash
# Meta Harness — roda o Codex CLI como revisor independente do commit mais
# recente (uma Vertical Slice = um commit), uma vez por slice concluída.
#
# `codex review --uncommitted` não aceita prompt customizado (mutuamente
# exclusivo nesta versão da CLI), por isso usamos `--commit <sha>`, que
# revisa exatamente o diff introduzido por um commit já existente.
#
# Uso:
#   scripts/validate-step.sh              # revisa o commit HEAD
#   scripts/validate-step.sh <sha-ou-ref>  # revisa um commit específico
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

TARGET_COMMIT="${1:-HEAD}"
RESOLVED_SHA="$(git rev-parse "$TARGET_COMMIT")"

HARNESS_DIR="$PROJECT_ROOT/.meta-harness"
PROMPT_PATH="$HARNESS_DIR/prompts/codex-review.md"
CONFIG_PATH="$HARNESS_DIR/config.json"
CONTRACTS_DIR="$HARNESS_DIR/contracts"
REPORTS_DIR="$HARNESS_DIR/reports"

if ! command -v codex >/dev/null 2>&1; then
  echo "Codex CLI não foi encontrado no PATH." >&2
  exit 1
fi

if [[ ! -f "$PROMPT_PATH" ]]; then
  echo "Prompt de revisão não encontrado: $PROMPT_PATH" >&2
  exit 1
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Config do harness não encontrado: $CONFIG_PATH" >&2
  exit 1
fi

CONFIG_PATH_WIN=$(cygpath -w "$CONFIG_PATH" 2>/dev/null || echo "$CONFIG_PATH")
MODEL=$(python -c "import json;print(json.load(open(r'$CONFIG_PATH_WIN'))['model'])")
REASONING_EFFORT=$(python -c "import json;print(json.load(open(r'$CONFIG_PATH_WIN'))['reasoning_effort'])")
SANDBOX=$(python -c "import json;print(json.load(open(r'$CONFIG_PATH_WIN'))['sandbox'])")

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_PATH="$REPORTS_DIR/codex-review-$TIMESTAMP.md"

mkdir -p "$REPORTS_DIR"

FULL_PROMPT_FILE=$(mktemp)
trap 'rm -f "$FULL_PROMPT_FILE"' EXIT

cat "$PROMPT_PATH" > "$FULL_PROMPT_FILE"

if [[ -f "$CONTRACTS_DIR/current-slice.md" ]]; then
  {
    echo ""
    echo "# CONTRATO DA ETAPA ATUAL"
    echo ""
    cat "$CONTRACTS_DIR/current-slice.md"
  } >> "$FULL_PROMPT_FILE"
fi

if [[ -f "$CONTRACTS_DIR/acceptance-criteria.md" ]]; then
  {
    echo ""
    echo "# CRITÉRIOS DE ACEITAÇÃO"
    echo ""
    cat "$CONTRACTS_DIR/acceptance-criteria.md"
  } >> "$FULL_PROMPT_FILE"
fi

PARENT_SHA="$(git rev-parse "$RESOLVED_SHA^" 2>/dev/null || echo "")"

{
  echo ""
  echo "# CONTEXTO DE EXECUÇÃO"
  echo ""
  echo "Diretório do projeto: $PROJECT_ROOT"
  echo ""
  echo "Commit a revisar: $RESOLVED_SHA"
  if [[ -n "$PARENT_SHA" ]]; then
    echo "Commit pai (base da comparação): $PARENT_SHA"
    echo ""
    echo "IMPORTANTE: este comando não usa as flags de escopo da CLI (--uncommitted/--base/--commit)"
    echo "porque elas são mutuamente exclusivas com instruções de prompt customizadas nesta versão"
    echo "do Codex CLI. Em vez disso, identifique o diff a revisar você mesmo, executando:"
    echo "  git diff $PARENT_SHA..$RESOLVED_SHA"
    echo "  git show --stat $RESOLVED_SHA"
    echo "Trate esse diff (não o estado geral do repositório) como o escopo desta revisão."
  else
    echo "Este commit não tem pai (commit raiz) — revise o conteúdo completo dele."
  fi
  echo ""
  echo "Execute a revisão agora e devolva somente o relatório solicitado."
} >> "$FULL_PROMPT_FILE"

echo "Iniciando revisão independente com Codex ($MODEL, reasoning_effort=$REASONING_EFFORT, sandbox=$SANDBOX) sobre o commit $RESOLVED_SHA..."
echo "Relatório: $REPORT_PATH"

set +e
codex review \
  -c "model=\"$MODEL\"" \
  -c "model_reasoning_effort=\"$REASONING_EFFORT\"" \
  - < "$FULL_PROMPT_FILE" \
  | tee "$REPORT_PATH"
CODEX_EXIT=${PIPESTATUS[0]}
set -e

if [[ $CODEX_EXIT -ne 0 ]]; then
  echo "A execução do Codex falhou com exit code $CODEX_EXIT." >&2
  exit "$CODEX_EXIT"
fi

echo ""
echo "Revisão concluída:"
echo "$REPORT_PATH"
