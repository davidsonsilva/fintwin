#!/usr/bin/env bash
# Meta Harness — roda o Codex CLI como revisor independente contra o diff
# não commitado atual, uma vez por Vertical Slice concluída.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

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

{
  echo ""
  echo "# CONTEXTO DE EXECUÇÃO"
  echo ""
  echo "Diretório do projeto: $PROJECT_ROOT"
  echo ""
  echo "Execute a revisão agora e devolva somente o relatório solicitado."
} >> "$FULL_PROMPT_FILE"

echo "Iniciando revisão independente com Codex ($MODEL, reasoning_effort=$REASONING_EFFORT)..."
echo "Nota: 'codex review' não aceita --sandbox como flag; sandbox de $SANDBOX é o valor pretendido em config.json, mas não é aplicado por este comando (ver .meta-harness/config.json)."
echo "Relatório: $REPORT_PATH"

set +e
codex review \
  --uncommitted \
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
