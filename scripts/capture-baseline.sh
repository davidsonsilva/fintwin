#!/usr/bin/env bash
# Meta Harness — captura o estado dos quality gates ANTES de implementar uma
# slice, para o harness distinguir falha nova (bloqueia) de falha
# pré-existente (não deve ser atribuída à slice atual).
#
# Uso:
#   scripts/capture-baseline.sh <slice-slug>   # ex: vs-08
set -uo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso: scripts/capture-baseline.sh <slice-slug>" >&2
  exit 1
fi

SLUG="$1"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASELINE_DIR="$PROJECT_ROOT/.meta-harness/baselines"
BASELINE_PATH="$BASELINE_DIR/${SLUG}-before.json"
mkdir -p "$BASELINE_DIR"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Capturando baseline de quality gates para '$SLUG'..."

# --- Backend: pytest ---
(
  cd "$PROJECT_ROOT/apps/api"
  source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null
  python -m pytest -q > "$TMP_DIR/pytest.log" 2>&1
  echo $? > "$TMP_DIR/pytest.exit"
)

# --- Frontend: tsc --noEmit ---
(
  cd "$PROJECT_ROOT/apps/web"
  npx tsc --noEmit > "$TMP_DIR/tsc.log" 2>&1
  echo $? > "$TMP_DIR/tsc.exit"
)
grep -E "error TS" "$TMP_DIR/tsc.log" > "$TMP_DIR/tsc.errors" 2>/dev/null || true

# --- Frontend: lint ---
(
  cd "$PROJECT_ROOT/apps/web"
  npm run lint > "$TMP_DIR/lint.log" 2>&1
  echo $? > "$TMP_DIR/lint.exit"
)
# Guarda o log inteiro (não só linhas com "error") — o resumo por arquivo
# (que inclui o caminho do arquivo) é o que permite casar findings do Codex
# com falhas conhecidas de lint; um grep filtrando só "error" descartaria
# justamente as linhas de caminho de arquivo.
grep -v "^$" "$TMP_DIR/lint.log" > "$TMP_DIR/lint.errors" 2>/dev/null || true

# --- Frontend: vitest ---
(
  cd "$PROJECT_ROOT/apps/web"
  npx vitest run > "$TMP_DIR/vitest.log" 2>&1
  echo $? > "$TMP_DIR/vitest.exit"
)

python - "$TMP_DIR" "$BASELINE_PATH" "$SLUG" <<'PYEOF'
import json
import sys
from pathlib import Path

tmp_dir, baseline_path, slug = Path(sys.argv[1]), sys.argv[2], sys.argv[3]

def read_exit(name):
    path = tmp_dir / name
    return int(path.read_text().strip()) if path.exists() else None

def read_lines(name, limit=30):
    path = tmp_dir / name
    if not path.exists():
        return []
    lines = [line.strip() for line in path.read_text(errors="replace").splitlines() if line.strip()]
    return lines[:limit]

baseline = {
    "slug": slug,
    "pytest": {"exitCode": read_exit("pytest.exit")},
    "typecheck": {"exitCode": read_exit("tsc.exit"), "knownFailures": read_lines("tsc.errors")},
    "lint": {"exitCode": read_exit("lint.exit"), "knownFailures": read_lines("lint.errors")},
    "vitest": {"exitCode": read_exit("vitest.exit")},
}

with open(baseline_path, "w", encoding="utf-8") as f:
    json.dump(baseline, f, ensure_ascii=False, indent=2)

print(f"Baseline salva em: {baseline_path}")
print(json.dumps(baseline, ensure_ascii=False, indent=2))
PYEOF
