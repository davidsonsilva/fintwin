#!/usr/bin/env bash
# Meta Harness — roda o Codex CLI como revisor independente de um commit
# (uma Vertical Slice ou uma rodada de correção = um commit), normaliza a
# saída nativa dele num relatório determinístico, e classifica findings
# como novos ou pré-existentes quando uma baseline é informada.
#
# `codex review --uncommitted`/`--base`/`--commit` são mutuamente exclusivos
# com prompt customizado nesta versão da CLI, por isso chamamos `codex
# review` sem flag de escopo e colocamos BASE_COMMIT/TARGET_COMMIT no
# próprio prompt, instruindo o Codex a rodar `git diff` ele mesmo.
#
# Uso:
#   scripts/validate-step.sh                              # revisa HEAD, sem baseline
#   scripts/validate-step.sh <sha-ou-ref>                  # revisa um commit específico
#   scripts/validate-step.sh <sha-ou-ref> <baseline.json>  # com baseline para NEW/PRE_EXISTING
#
# Códigos de saída: 0 = APPROVED/APPROVED_WITH_WARNINGS; 2 = REJECTED; 1 = erro de ferramenta.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

TARGET_COMMIT="${1:-HEAD}"
BASELINE_PATH="${2:-}"
RESOLVED_TARGET="$(git rev-parse "$TARGET_COMMIT")"
RESOLVED_BASE="$(git rev-parse "$RESOLVED_TARGET^" 2>/dev/null || echo "")"

HARNESS_DIR="$PROJECT_ROOT/.meta-harness"
PROMPT_PATH="$HARNESS_DIR/prompts/codex-review.md"
CONFIG_PATH="$HARNESS_DIR/config.json"
CONTRACTS_DIR="$HARNESS_DIR/contracts"
RAW_DIR="$HARNESS_DIR/raw"
REPORTS_DIR="$HARNESS_DIR/reports"
STATE_DIR="$HARNESS_DIR/state"
NORMALIZER="$PROJECT_ROOT/scripts/normalize-codex-review.py"

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
RAW_PATH="$RAW_DIR/codex-review-$TIMESTAMP.txt"
REPORT_PATH="$REPORTS_DIR/codex-review-$TIMESTAMP.md"
STATE_PATH="$STATE_DIR/current-review.json"

mkdir -p "$RAW_DIR" "$REPORTS_DIR" "$STATE_DIR"

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
  echo "TARGET_COMMIT: $RESOLVED_TARGET"
  if [[ -n "$RESOLVED_BASE" ]]; then
    echo "BASE_COMMIT: $RESOLVED_BASE"
    echo ""
    echo "Analise prioritariamente apenas o diff entre BASE_COMMIT e TARGET_COMMIT, executando você mesmo:"
    echo "  git diff $RESOLVED_BASE..$RESOLVED_TARGET"
    echo "  git diff --stat $RESOLVED_BASE..$RESOLVED_TARGET"
    echo "  git show --name-only $RESOLVED_TARGET"
    echo "Não faça uma auditoria geral do repositório — consulte arquivos fora do diff só quando necessário"
    echo "para entender contratos, confirmar uma regressão ou validar uma regra de domínio referenciada."
  else
    echo "TARGET_COMMIT não tem pai (commit raiz) — revise o conteúdo completo dele."
  fi
  if [[ -n "$BASELINE_PATH" && -f "$BASELINE_PATH" ]]; then
    echo ""
    echo "Baseline de quality gates desta etapa (falhas conhecidas ANTES da implementação): $BASELINE_PATH"
    echo "--- conteúdo da baseline ---"
    cat "$BASELINE_PATH"
    echo "--- fim da baseline ---"
  fi
  echo ""
  echo "Execute a revisão agora e devolva somente o relatório solicitado."
} >> "$FULL_PROMPT_FILE"

echo "Iniciando revisão independente com Codex ($MODEL, reasoning_effort=$REASONING_EFFORT, sandbox=$SANDBOX) sobre o commit $RESOLVED_TARGET..."

set +e
codex review \
  -c "model=\"$MODEL\"" \
  -c "model_reasoning_effort=\"$REASONING_EFFORT\"" \
  - < "$FULL_PROMPT_FILE" \
  | tee "$RAW_PATH"
CODEX_EXIT=${PIPESTATUS[0]}
set -e

if [[ $CODEX_EXIT -ne 0 ]]; then
  echo "A execução do Codex falhou com exit code $CODEX_EXIT." >&2
  exit 1
fi

echo ""
echo "Saída nativa preservada em: $RAW_PATH"
echo "Normalizando relatório..."

NORMALIZE_ARGS=("$RAW_PATH" "$REPORT_PATH")
if [[ -n "$BASELINE_PATH" ]]; then
  NORMALIZE_ARGS+=(--baseline "$BASELINE_PATH")
fi

NORMALIZE_OUTPUT=$(python "$NORMALIZER" "${NORMALIZE_ARGS[@]}")
echo "$NORMALIZE_OUTPUT"

VERDICT=$(echo "$NORMALIZE_OUTPUT" | grep -oE "APPROVED_WITH_WARNINGS|APPROVED|REJECTED" | head -1)

python - "$STATE_PATH" "$RESOLVED_TARGET" "$RESOLVED_BASE" "$TIMESTAMP" "$VERDICT" "$REPORT_PATH" "$RAW_PATH" <<'PYEOF'
import json
import sys

state_path, target, base, timestamp, verdict, report_path, raw_path = sys.argv[1:8]
state = {
    "target_commit": target,
    "base_commit": base or None,
    "timestamp": timestamp,
    "verdict": verdict,
    "report_path": report_path,
    "raw_path": raw_path,
}
with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
PYEOF

echo ""
echo "Revisão concluída — veredito: $VERDICT"
echo "Relatório padronizado: $REPORT_PATH"
echo "Estado salvo em: $STATE_PATH"

if [[ "$VERDICT" == "REJECTED" ]]; then
  exit 2
fi
exit 0
