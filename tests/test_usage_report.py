#!/usr/bin/env python3
"""사용량 리포트(_shared/usage-report.py) 회귀 테스트. 외부 호출 없음.

핵심 가드:
  C4 — log.md 의 HTML 주석 예시 블록을 [WORKER_CALL] 로 세면 안 된다.
       템플릿이 주석 안에 예시를 담고 있어, 세면 모든 새 작업이 "디스패처 미경유 호출"로
       부풀려진다(audit-approvals 가 같은 함정에 빠졌던 것과 동일한 계열).
  C5 — 깨진 원장 줄이 있어도 죽지 않고 개수만 보고해야 한다. 원장은 best-effort append라
       중간에 잘린 줄이 생길 수 있다.
"""
from __future__ import annotations

import _utf8  # noqa: F401  (출력 인코딩 UTF-8 고정 — 반드시 print보다 먼저)

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "_shared" / "usage-report.py"
LOG_TEMPLATE = REPO / "_templates" / "log.md"

ROWS = [
    {"ts": "2026-08-13T10:00:00", "task": "t1", "role": "gemini", "backend": "cli",
     "model": "pro", "status": "ok", "exit_code": 0, "duration_s": 10},
    {"ts": "2026-08-13T10:05:00", "task": "t1", "role": "gemini", "backend": "cli",
     "model": "pro", "status": "empty", "exit_code": 0, "duration_s": 12},
    {"ts": "2026-08-13T10:10:00", "task": "t1", "role": "codex-critic", "backend": "cli",
     "model": "gpt", "status": "ok", "exit_code": 0, "duration_s": 90},
]


def make_root(base: Path, *, broken_line: bool = False,
              log_body: str | None = None) -> Path:
    root = base / "sys"
    (root / "_local").mkdir(parents=True)
    (root / "tasks" / "t1").mkdir(parents=True)
    lines = [json.dumps(r, ensure_ascii=False) for r in ROWS]
    if broken_line:
        lines.insert(1, "{ 깨진 줄")
    (root / "_local" / "calls.jsonl").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    if log_body is not None:
        (root / "tasks" / "t1" / "log.md").write_text(
            log_body, encoding="utf-8", newline="\n")
    return root


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, MULTIAGENT_ROOT=str(root), PYTHONUTF8="1")
    return subprocess.run([sys.executable, str(REPORT), *args], capture_output=True,
                          text=True, encoding="utf-8", env=env, timeout=120)


def check(name: str, ok: bool, detail: str = "") -> int:
    print(f"  {'PASS' if ok else 'FAIL'} {name}")
    if not ok and detail:
        print("        " + detail.replace("\n", "\n        ").strip()[:600])
    return 0 if ok else 1


def main() -> None:
    fails = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = make_root(Path(tmp))
        r = run(root)
        out = r.stdout or ""

        fails += check("C1 집계 요약 (총 3회 · 성공 2 · 빈출력 1)",
                       r.returncode == 0 and "총 3회" in out
                       and "성공 2" in out and "빈출력 1" in out, out + (r.stderr or ""))
        fails += check("C2 워커별·모델별 표",
                       "gemini" in out and "codex-critic" in out and "모델별" in out, out)

        # C3 기간 필터 — 아주 짧은 기간이면 과거 데이터가 빠진다
        r2 = run(root, "--days", "1")
        fails += check("C3 --days 필터 동작",
                       r2.returncode == 0
                       and ("기록된 호출이 없습니다" in (r2.stdout or "")
                            or "최근 1일" in (r2.stdout or "")), r2.stdout or "")

    # C4 (핵심) log.md 템플릿의 주석 예시를 호출로 세면 안 된다
    with tempfile.TemporaryDirectory() as tmp:
        root = make_root(Path(tmp), log_body=LOG_TEMPLATE.read_text(encoding="utf-8"))
        out = (run(root).stdout or "")
        fails += check("C4 log 템플릿 주석 예시 → 호출로 세지 않음",
                       "log.md 기준" not in out, out)

    # C4b 실제 기록된 호출은 센다
    with tempfile.TemporaryDirectory() as tmp:
        body = ("<!-- 형식 예시\n[2026-01-01 00:00] [WORKER_CALL] 예시 -->\n"
                "[2026-08-13 10:00] [WORKER_CALL] claude-main brief 전달\n")
        root = make_root(Path(tmp), log_body=body)
        out = (run(root).stdout or "")
        fails += check("C4b 실제 [WORKER_CALL] 은 집계", "log.md 기준 총 워커 호출: 1회" in out, out)

    # C5 깨진 줄이 있어도 죽지 않는다
    with tempfile.TemporaryDirectory() as tmp:
        root = make_root(Path(tmp), broken_line=True)
        r = run(root)
        fails += check("C5 깨진 원장 줄 → 크래시 없이 보고",
                       r.returncode == 0 and "깨진 줄 1개" in (r.stdout or "")
                       and "Traceback" not in (r.stderr or ""),
                       (r.stdout or "") + (r.stderr or ""))

    # C6 원장 없음 → exit 2 + 안내
    with tempfile.TemporaryDirectory() as tmp:
        empty = Path(tmp) / "none"
        empty.mkdir()
        r = run(empty)
        fails += check("C6 원장 없음 → exit 2 + 경로 안내",
                       r.returncode == 2 and "calls.jsonl" in (r.stderr or ""), r.stderr or "")

    print(f"test_usage_report: {'all pass' if not fails else f'{fails} fail'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
