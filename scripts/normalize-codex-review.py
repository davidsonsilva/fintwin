#!/usr/bin/env python3
"""Normaliza a saída nativa do `codex review` (Markdown livre ou JSON) num
relatório padronizado do Meta Harness, com veredito derivado por regra fixa
(sem gastar outra chamada de IA — ver docs/features/ajustes-meta-harness.md).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

_SEVERITY_ORDER = ["BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO"]
_SEVERITY_PATTERN = re.compile(r"\b(BLOCKER|HIGH|MEDIUM|LOW|INFO)\b")
_MD_BULLET_PATTERN = re.compile(
    r"^-\s*\[P(?P<priority>\d+)\]\s*(?P<title>.+?)\s*—\s*(?P<location>.+)\s*$"
)


def _severity_from_priority(priority: int) -> str:
    if priority <= 1:
        return "HIGH"
    if priority == 2:
        return "MEDIUM"
    return "LOW"


def _parse_json_findings(data: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    for item in data.get("findings", []):
        title = str(item.get("title", "")).strip()
        body = str(item.get("body", "")).strip()
        priority_match = re.search(r"\[P(\d+)\]", title)
        priority = int(priority_match.group(1)) if priority_match else None

        severity_match = _SEVERITY_PATTERN.search(body) or _SEVERITY_PATTERN.search(title)
        if severity_match:
            severity = severity_match.group(1)
        elif priority is not None:
            severity = _severity_from_priority(priority)
        else:
            severity = "MEDIUM"

        location = item.get("code_location", {}) or {}
        file_path = location.get("absolute_file_path", "")
        line_range = location.get("line_range", {}) or {}
        line = line_range.get("start")

        findings.append(
            {
                "severity": severity,
                "priority": priority,
                "title": re.sub(r"^\[P\d+\]\s*", "", title),
                "file": file_path,
                "line": line,
                "description": body,
            }
        )
    return findings


def _parse_markdown_findings(text: str) -> list[dict[str, Any]]:
    findings = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = _MD_BULLET_PATTERN.match(lines[i].strip())
        if match:
            priority = int(match.group("priority"))
            title = match.group("title")
            location = match.group("location")
            file_path, _, line = location.rpartition(":")
            if not file_path:
                # Sem ":" no location (raro) — trata tudo como caminho, sem linha.
                file_path, line = location, ""
            description = ""
            severity = _severity_from_priority(priority)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                severity_match = _SEVERITY_PATTERN.match(next_line)
                if severity_match:
                    severity = severity_match.group(1)
                    description = next_line[severity_match.end():].lstrip(": ").strip()
            findings.append(
                {
                    "severity": severity,
                    "priority": priority,
                    "title": title,
                    "file": file_path,
                    "line": line or None,
                    "description": description,
                }
            )
        i += 1
    return findings


def _derive_verdict(findings: list[dict[str, Any]]) -> str:
    severities = {f["severity"] for f in findings}
    if "BLOCKER" in severities or "HIGH" in severities:
        return "REJECTED"
    if "MEDIUM" in severities:
        return "APPROVED_WITH_WARNINGS"
    return "APPROVED"


def _load_baseline(path: Optional[str]) -> dict[str, Any]:
    if not path:
        return {}
    baseline_path = Path(path)
    if not baseline_path.exists():
        return {}
    return json.loads(baseline_path.read_text(encoding="utf-8"))


_TSC_KNOWN_PATTERN = re.compile(r"^(?P<file>.+?)\((?P<line>\d+),\d+\):")
_LINT_KNOWN_PATTERN = re.compile(r"^(?P<line>\d+):\d+\s+(error|warning)")


def _extract_known_locations(baseline: dict[str, Any]) -> list[tuple[str, int]]:
    """Extrai pares (nome-do-arquivo, linha) das falhas conhecidas da baseline.

    Matching por arquivo+linha (não só nome do arquivo) evita que um finding
    novo numa linha diferente do mesmo arquivo seja mascarado como
    pré-existente — bug real encontrado pelo próprio Meta Harness ao revisar
    este script.
    """
    locations: list[tuple[str, int]] = []

    for entry in baseline.get("typecheck", {}).get("knownFailures", []):
        match = _TSC_KNOWN_PATTERN.match(entry.strip())
        if match:
            locations.append((Path(match.group("file")).name.lower(), int(match.group("line"))))

    current_file: Optional[str] = None
    for entry in baseline.get("lint", {}).get("knownFailures", []):
        stripped = entry.strip()
        match = _LINT_KNOWN_PATTERN.match(stripped)
        if match:
            if current_file:
                locations.append((Path(current_file).name.lower(), int(match.group("line"))))
            continue
        if stripped and not stripped[0].isdigit() and ("/" in stripped or "\\" in stripped):
            current_file = stripped

    return locations


def _finding_line_numbers(line_field: Any) -> set[int]:
    if not line_field:
        return set()
    numbers = [int(n) for n in re.findall(r"\d+", str(line_field))]
    if len(numbers) >= 2:
        return set(range(numbers[0], numbers[1] + 1))
    return set(numbers)


def _mark_pre_existing(findings: list[dict[str, Any]], baseline: dict[str, Any]) -> None:
    known_locations = _extract_known_locations(baseline)

    for finding in findings:
        file_path = finding.get("file") or ""
        finding["baseline_status"] = "NEW_FAILURE"
        if not file_path:
            continue
        basename = Path(file_path).name.lower()
        finding_lines = _finding_line_numbers(finding.get("line"))
        for known_basename, known_line in known_locations:
            if known_basename == basename and (not finding_lines or known_line in finding_lines):
                finding["baseline_status"] = "PRE_EXISTING_FAILURE"
                break


def _render_report(
    verdict: str,
    findings: list[dict[str, Any]],
    raw_path: str,
    overall_explanation: str,
    baseline_used: bool,
) -> str:
    lines = [
        "## Veredito",
        "",
        verdict,
        "",
        "## Resumo executivo",
        "",
        overall_explanation or "(ver saída nativa em raw/)",
        "",
        f"## Findings ({len(findings)})",
        "",
    ]
    if not findings:
        lines.append("Nenhum finding reportado.")
    for idx, finding in enumerate(findings, start=1):
        baseline_tag = f" [{finding['baseline_status']}]" if baseline_used and "baseline_status" in finding else ""
        lines.append(
            f"{idx}. **{finding['severity']}**{baseline_tag} — {finding['title']} "
            f"(`{finding['file']}:{finding['line']}`)"
        )
        if finding["description"]:
            lines.append(f"   {finding['description']}")
        lines.append("")

    counts = {sev: sum(1 for f in findings if f["severity"] == sev) for sev in _SEVERITY_ORDER}
    lines.append("## Contagem por severidade")
    lines.append("")
    lines.append(", ".join(f"{sev}: {counts[sev]}" for sev in _SEVERITY_ORDER))
    lines.append("")
    lines.append(f"## Saída nativa preservada em: `{raw_path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_path", help="Caminho do arquivo com a saída nativa do codex review")
    parser.add_argument("report_path", help="Caminho de saída do relatório padronizado")
    parser.add_argument("--baseline", default=None, help="Caminho opcional do baseline JSON da slice")
    args = parser.parse_args()

    raw_text = Path(args.raw_path).read_text(encoding="utf-8", errors="replace").strip()

    overall_explanation = ""
    findings: list[dict[str, Any]]
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict) and "findings" in data:
            findings = _parse_json_findings(data)
            overall_explanation = str(data.get("overall_explanation", ""))
        else:
            findings = _parse_markdown_findings(raw_text)
    except json.JSONDecodeError:
        findings = _parse_markdown_findings(raw_text)
        summary_match = re.match(r"^(.+?)\n\n", raw_text, re.DOTALL)
        if summary_match:
            overall_explanation = summary_match.group(1).strip()

    baseline = _load_baseline(args.baseline)
    baseline_used = bool(baseline)
    if baseline_used:
        _mark_pre_existing(findings, baseline)
        verdict_findings = [f for f in findings if f.get("baseline_status") != "PRE_EXISTING_FAILURE"]
    else:
        verdict_findings = findings

    verdict = _derive_verdict(verdict_findings)

    report = _render_report(verdict, findings, args.raw_path, overall_explanation, baseline_used)
    Path(args.report_path).write_text(report, encoding="utf-8")

    print(f"Veredito derivado: {verdict}")
    print(f"Findings: {len(findings)}")
    print(f"Relatório padronizado: {args.report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
