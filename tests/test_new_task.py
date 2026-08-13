#!/usr/bin/env python3
"""작업 폴더 스캐폴더(_shared/new-task.py) 회귀 테스트. 외부 호출 없음.

핵심 가드 둘:
  C3 — `workers_approved`는 절대 채워지지 않아야 한다. 스캐폴더가 미리 채우면
       승인 게이트가 무의미해진다(계획 ≠ 승인).
  C2 — task.md 형식(`## 메타` yaml 펜스 + `## Goal`, 선두 `---` 금지)이 유지돼야 한다.
       mat이 이 형식을 파싱하므로 깨지면 모니터가 작업을 못 읽는다.
"""
from __future__ import annotations

import _utf8  # noqa: F401  (출력 인코딩 UTF-8 고정 — 반드시 print보다 먼저)

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NEW_TASK = REPO / "_shared" / "new-task.py"
CHECK_LIMITS = REPO / "_shared" / "check-limits.py"
AUDIT = REPO / "_shared" / "audit-approvals.py"


def fake_root(base: Path) -> Path:
    """_templates/ + _shared/backends.json 만 갖춘 최소 루트."""
    root = base / "sys"
    (root / "tasks").mkdir(parents=True)
    (root / "_shared").mkdir(parents=True)
    shutil.copytree(REPO / "_templates", root / "_templates")
    shutil.copy2(REPO / "_shared" / "backends.json", root / "_shared" / "backends.json")
    return root


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, MULTIAGENT_ROOT=str(root), PYTHONUTF8="1")
    return subprocess.run([sys.executable, str(NEW_TASK), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def run_tool(tool: Path, target: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONUTF8="1")
    return subprocess.run([sys.executable, str(tool), str(target)],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def check(name: str, ok: bool, detail: str = "") -> int:
    print(f"  {'PASS' if ok else 'FAIL'} {name}")
    if not ok and detail:
        print("        " + detail.replace("\n", "\n        ").strip())
    return 0 if ok else 1


def main() -> None:
    fails = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = fake_root(Path(tmp))

        # C1 생성
        r = run(root, "결제개선", "--workers", "claude-main,codex-main",
                "--goal", "결제 API 명세 정리")
        t = root / "tasks" / "결제개선"
        made = [t / "task.md", t / "context.md", t / "log.md",
                t / "workers" / "claude-main" / "brief.md",
                t / "workers" / "codex-main" / "brief.md",
                t / "sources", t / "artifacts"]
        fails += check("C1 폴더·파일 일습 생성",
                       r.returncode == 0 and all(p.exists() for p in made),
                       (r.stdout or "") + (r.stderr or ""))

        task_md = (t / "task.md").read_text(encoding="utf-8") if (t / "task.md").is_file() else ""

        # C2 task.md 형식 (mat 파싱)
        shape = (not task_md.startswith("---")
                 and "## 메타" in task_md
                 and "```yaml" in task_md
                 and "## Goal" in task_md)
        fails += check("C2 task.md 형식 유지 (## 메타 yaml + ## Goal, 선두 --- 없음)", shape)

        # C3 (핵심) 승인 게이트 — workers_approved 는 비어 있어야
        fails += check("C3 workers_approved 는 비어 있음 (계획 ≠ 승인)",
                       "workers_approved: []" in task_md,
                       task_md[:400])

        # C4 planned_workers 는 채워져야
        fails += check("C4 planned_workers 채워짐",
                       "- role: claude-main" in task_md and "- role: codex-main" in task_md)

        # C5 날짜·작업명·Goal 치환.
        # `## 메타` 블록의 created/updated 만 본다 — workers_approved 예시 주석의
        # `approved_at: <YYYY-MM-DD>` 는 승인 서식 안내라 남아 있는 게 맞다.
        today = re.search(r"^created: (\d{4}-\d{2}-\d{2})$", task_md, re.M)
        subbed = (bool(today)
                  and re.search(r"^updated: \d{4}-\d{2}-\d{2}$", task_md, re.M)
                  and task_md.startswith("# 결제개선")
                  and "결제 API 명세 정리" in task_md)
        fails += check("C5 작업명·날짜·Goal 치환", subbed, task_md[:300])

        # C6 brief 치환 + 고정 규약 블록 유지
        brief = (t / "workers" / "codex-main" / "brief.md").read_text(encoding="utf-8")
        fails += check("C6 brief 역할·경로 치환 + 고정 규약 블록 유지",
                       brief.startswith("# Brief — codex-main / 결제개선")
                       and "## Worker 행동 규약" in brief
                       and "tasks/결제개선/" in brief
                       and "<task-name>" not in brief)

        # C7 통합 — 생성 직후 한도·승인 검사가 통과해야 (도구끼리 물려 돌아가는지)
        rl = run_tool(CHECK_LIMITS, t)
        ra = run_tool(AUDIT, t)
        fails += check("C7 생성 직후 check-limits·audit-approvals 통과",
                       rl.returncode == 0 and ra.returncode == 0,
                       (rl.stdout or "") + (ra.stdout or ""))

        # C8 중복 생성 거부
        r2 = run(root, "결제개선")
        fails += check("C8 기존 작업 덮어쓰기 거부 (exit 2)", r2.returncode == 2)

        # C9 미정의 역할 거부 + 유효 목록 안내
        r3 = run(root, "다른작업", "--workers", "nonexistent-worker")
        fails += check("C9 미정의 역할 거부 + 유효 목록 안내",
                       r3.returncode == 2 and "gemini" in (r3.stderr or ""),
                       r3.stderr or "")

        # C10 경로 구분자·상대참조 차단
        bad = run(root, "../탈출")
        fails += check("C10 경로 구분자 포함 이름 거부", bad.returncode == 2)

        # C11 dry-run 은 아무것도 만들지 않음
        run(root, "가상작업", "--dry-run")
        fails += check("C11 dry-run 은 생성 안 함",
                       not (root / "tasks" / "가상작업").exists())

    print(f"test_new_task: {'all pass' if not fails else f'{fails} fail'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
