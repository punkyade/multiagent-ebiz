#!/usr/bin/env python3
"""승인 게이트 감사(_shared/audit-approvals.py) 회귀 테스트.

외부 호출 없음, 결정적. fixture 작업 폴더를 임시로 만들어 종료코드를 단언한다.

가장 중요한 케이스는 C3 — log.md 템플릿이 HTML 주석 안에 [WORKER_CALL] 예시를
담고 있어, 주석을 걷어내지 않으면 **모든 새 작업이 위반으로 오탐**된다.
그러면 감사 도구는 즉시 신뢰를 잃고 아무도 안 쓰게 된다.
"""
from __future__ import annotations

import _utf8  # noqa: F401  (출력 인코딩 UTF-8 고정 — 반드시 print보다 먼저)

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "_shared" / "audit-approvals.py"
LOG_TEMPLATE = REPO / "_templates" / "log.md"

APPROVED_ONE = """# 테스트 작업

## Worker Plan

```yaml
workers_approved:
  - worker: claude-main
    approved_at: 2026-08-13
    purpose: 설계
    approved_by: user

planned_workers: []
```
"""

APPROVED_TWO = """# 테스트 작업

## Worker Plan

```yaml
workers_approved:
  - worker: claude-main
    approved_at: 2026-08-13
    purpose: 설계
    approved_by: user
  - worker: codex-main
    approved_at: 2026-08-13
    purpose: 구현
    approved_by: user

planned_workers: []
```
"""

APPROVED_NONE = """# 테스트 작업

## Worker Plan

```yaml
workers_approved: []
planned_workers: []
```
"""


def make_task(base: Path, task_md: str, log_body: str,
              briefs: dict[str, str] | None = None) -> Path:
    d = base / "t"
    (d / "workers").mkdir(parents=True, exist_ok=True)
    (d / "task.md").write_text(task_md, encoding="utf-8", newline="\n")
    (d / "log.md").write_text(log_body, encoding="utf-8", newline="\n")
    for role, brief in (briefs or {}).items():
        (d / "workers" / role).mkdir(parents=True, exist_ok=True)
        (d / "workers" / role / "brief.md").write_text(brief, encoding="utf-8", newline="\n")
    return d


def run_audit(task_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(AUDIT), str(task_dir)],
                          capture_output=True, text=True, encoding="utf-8")


def case(name: str, task_md: str, log_body: str, expect_rc: int,
         briefs: dict[str, str] | None = None, expect_in_out: str | None = None) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        d = make_task(Path(tmp), task_md, log_body, briefs)
        r = run_audit(d)
        ok = r.returncode == expect_rc
        if ok and expect_in_out:
            ok = expect_in_out in (r.stdout or "")
        print(f"  {'PASS' if ok else 'FAIL'} {name}")
        if not ok:
            print(f"        기대 rc={expect_rc} 실제 rc={r.returncode}")
            print("        " + (r.stdout or "").replace("\n", "\n        ").strip())
        return 0 if ok else 1


def main() -> None:
    fails = 0

    # C1 승인된 워커만 호출 → 통과
    fails += case(
        "C1 승인된 워커 호출 → 위반 0",
        APPROVED_ONE,
        "[2026-08-13 10:00] [WORKER_CALL] claude-main brief 전달\n",
        0)

    # C2 승인 없이 호출 → 위반
    fails += case(
        "C2 미승인 워커 호출 → 위반 검출",
        APPROVED_ONE,
        "[2026-08-13 10:00] [WORKER_CALL] claude-main brief 전달\n"
        "[2026-08-13 10:30] [WORKER_CALL] codex-main brief 전달\n",
        1, expect_in_out="codex-main")

    # C3 (핵심) log.md 템플릿의 주석 예시 블록을 위반으로 오탐하지 않아야
    fails += case(
        "C3 log 템플릿 주석 예시 → 오탐 없음",
        APPROVED_NONE,
        LOG_TEMPLATE.read_text(encoding="utf-8"),
        0)

    # C4 승인 목록 2번째 항목도 인식해야 (파서 조기종료 회귀 가드)
    fails += case(
        "C4 승인 목록 2번째 워커 인식",
        APPROVED_TWO,
        "[2026-08-13 10:00] [WORKER_CALL] claude-main brief 전달\n"
        "[2026-08-13 10:30] [WORKER_CALL] codex-main brief 전달\n",
        0)

    # C5 외부 repo 쓰기인데 [APPROVAL] 기록 없음 → 위반
    fails += case(
        "C5 외부 쓰기 + APPROVAL 없음 → 위반 검출",
        APPROVED_TWO,
        "[2026-08-13 10:00] [WORKER_CALL] codex-main brief 전달\n",
        1,
        briefs={"codex-main": "target_repo: /abs/repo\nwrite_scope: src/**\n"},
        expect_in_out="APPROVAL")

    # C6 외부 repo 쓰기 4조건 충족 → 통과
    fails += case(
        "C6 외부 쓰기 4조건 충족 → 위반 0",
        APPROVED_TWO,
        "[2026-08-13 09:50] [APPROVAL] codex-main 외부 쓰기 승인 write_scope: src/**\n"
        "[2026-08-13 10:00] [WORKER_CALL] codex-main brief 전달\n",
        0,
        briefs={"codex-main": "target_repo: /abs/repo\nwrite_scope: src/**\n"})

    # C7 tasks-only 는 외부 쓰기가 아니므로 APPROVAL 불필요
    fails += case(
        "C7 tasks-only 는 외부 쓰기 아님",
        APPROVED_TWO,
        "[2026-08-13 10:00] [WORKER_CALL] codex-main brief 전달\n",
        0,
        briefs={"codex-main": "target_repo: N/A\nwrite_scope: tasks-only\n"})

    print(f"test_audit: {'all pass' if not fails else f'{fails} fail'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
