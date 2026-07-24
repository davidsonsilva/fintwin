"""Testes do normalizador do Meta Harness (scripts/normalize-codex-review.py).

Roda com `python scripts/test_normalize_codex_review.py` — sem framework de
teste externo, para não acoplar o tooling do harness às dependências de
apps/api ou apps/web.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "normalize_codex_review", Path(__file__).parent / "normalize-codex-review.py"
)
normalize = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(normalize)  # type: ignore[union-attr]

_FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        _FAILURES.append(message)


def test_markdown_parsing_handles_path_with_spaces_and_hyphens():
    text = (
        "Resumo aqui.\n\n"
        "- [P1] Título do finding — D:\\IA Projects\\gemeo-financeiro\\apps\\web\\file.tsx:10-12\n"
        "  HIGH: descrição do problema.\n"
    )
    findings = normalize._parse_markdown_findings(text)
    check(len(findings) == 1, "deveria extrair 1 finding do Markdown")
    check(findings[0]["file"] == "D:\\IA Projects\\gemeo-financeiro\\apps\\web\\file.tsx", "arquivo com espaço deveria ser extraído corretamente")
    check(findings[0]["line"] == "10-12", "linha deveria ser extraída corretamente")
    check(findings[0]["severity"] == "HIGH", "severidade deveria vir da linha seguinte")


def test_json_parsing_derives_severity_from_body():
    data = {
        "findings": [
            {
                "title": "[P1] Algo quebrado",
                "body": "HIGH — isso está errado.",
                "code_location": {"absolute_file_path": "apps/api/foo.py", "line_range": {"start": 5}},
            }
        ],
        "overall_explanation": "resumo",
    }
    findings = normalize._parse_json_findings(data)
    check(len(findings) == 1, "deveria extrair 1 finding do JSON")
    check(findings[0]["severity"] == "HIGH", "severidade deveria ser extraída do body")
    check(findings[0]["file"] == "apps/api/foo.py", "arquivo deveria vir de code_location")


def test_verdict_derivation_rules():
    check(normalize._derive_verdict([]) == "APPROVED", "sem findings deveria ser APPROVED")
    check(
        normalize._derive_verdict([{"severity": "LOW"}, {"severity": "INFO"}]) == "APPROVED",
        "só LOW/INFO deveria ser APPROVED",
    )
    check(
        normalize._derive_verdict([{"severity": "MEDIUM"}]) == "APPROVED_WITH_WARNINGS",
        "MEDIUM sem HIGH/BLOCKER deveria ser APPROVED_WITH_WARNINGS",
    )
    check(
        normalize._derive_verdict([{"severity": "HIGH"}]) == "REJECTED",
        "HIGH deveria ser REJECTED",
    )
    check(
        normalize._derive_verdict([{"severity": "BLOCKER"}]) == "REJECTED",
        "BLOCKER deveria ser REJECTED",
    )


def test_baseline_matching_requires_same_line_not_just_same_file():
    """Regressão: um finding novo no mesmo arquivo de uma falha conhecida,
    mas em linha diferente, NÃO pode ser mascarado como pré-existente
    (bug real encontrado pelo Meta Harness revisando este próprio script)."""
    baseline = {
        "typecheck": {
            "knownFailures": [
                "src/features/onboarding/ResourceStepForm.tsx(117,27): error TS2769: No overload matches this call."
            ]
        },
        "lint": {"knownFailures": []},
    }

    findings = [
        {"file": "D:\\proj\\src\\features\\onboarding\\ResourceStepForm.tsx", "line": "200", "severity": "HIGH", "title": "", "description": "npx tsc --noEmit fails here too"},
        {"file": "D:\\proj\\src\\features\\onboarding\\ResourceStepForm.tsx", "line": "117", "severity": "HIGH", "title": "", "description": "npx tsc --noEmit reports an overload error"},
    ]
    normalize._mark_pre_existing(findings, baseline)

    check(
        findings[0]["baseline_status"] == "NEW_FAILURE",
        "finding em linha diferente (200) não deveria ser mascarado como pré-existente",
    )
    check(
        findings[1]["baseline_status"] == "PRE_EXISTING_FAILURE",
        "finding na mesma linha (117) E mesma identidade (TS2769) da baseline deveria ser pré-existente",
    )


def test_baseline_matching_does_not_mask_a_different_problem_on_the_same_line():
    """Regressão: um finding NOVO e DIFERENTE (ex: bug funcional/segurança)
    que por coincidência cai na mesma linha de uma falha de lint/typecheck
    conhecida NÃO pode ser mascarado só por causa da localização — a
    descrição do finding também precisa mencionar o mesmo gate (tsc/lint)
    (segundo bug real encontrado pelo Meta Harness revisando este script)."""
    baseline = {
        "typecheck": {
            "knownFailures": [
                "src/features/onboarding/ResourceStepForm.tsx(117,27): error TS2769: No overload matches this call."
            ]
        },
        "lint": {"knownFailures": []},
    }
    findings = [
        {
            "file": "D:\\proj\\src\\features\\onboarding\\ResourceStepForm.tsx",
            "line": "117",
            "severity": "HIGH",
            "title": "SQL injection via unsanitized input",
            "description": "Completely unrelated security bug that happens to be on this line.",
        }
    ]
    normalize._mark_pre_existing(findings, baseline)

    check(
        findings[0]["baseline_status"] == "NEW_FAILURE",
        "finding que não menciona tsc/typecheck não deveria ser mascarado, mesmo na mesma linha de uma falha de typecheck conhecida",
    )


def test_baseline_matching_handles_lint_file_header_association():
    baseline = {
        "typecheck": {"knownFailures": []},
        "lint": {
            "knownFailures": [
                "D:\\proj\\src\\features\\onboarding\\resourceConfigs.ts",
                "31:86   error  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any",
                "D:\\proj\\src\\other\\File.tsx",
                "10:5   error  Something else  some-other/rule",
            ]
        },
    }
    findings = [
        {
            "file": "D:\\proj\\src\\features\\onboarding\\resourceConfigs.ts",
            "line": "31",
            "severity": "MEDIUM",
            "title": "",
            "description": "Reports @typescript-eslint/no-explicit-any usage here.",
        },
        {
            "file": "D:\\proj\\src\\features\\onboarding\\resourceConfigs.ts",
            "line": "10",
            "severity": "MEDIUM",
            "title": "",
            "description": "Some unrelated new finding.",
        },
    ]
    normalize._mark_pre_existing(findings, baseline)

    check(
        findings[0]["baseline_status"] == "PRE_EXISTING_FAILURE",
        "linha 31 de resourceConfigs.ts deveria casar com a falha conhecida associada a esse arquivo",
    )
    check(
        findings[1]["baseline_status"] == "NEW_FAILURE",
        "linha 10 de resourceConfigs.ts não deveria casar com a falha conhecida de outro arquivo",
    )


def main() -> int:
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()

    if _FAILURES:
        print(f"FALHOU: {len(_FAILURES)} de {len(tests)} testes")
        for failure in _FAILURES:
            print(f"  - {failure}")
        return 1

    print(f"OK: {len(tests)} testes passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
