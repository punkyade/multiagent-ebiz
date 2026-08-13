#!/usr/bin/env python3
"""작업 폴더 스캐폴더 — `tasks/<작업명>/` 한 벌을 템플릿에서 결정적으로 만든다.

지금까지 새 작업을 시작하려면 `_templates/`에서 3개 파일을 손으로 복사하고
`workers/<역할>/` 폴더를 만들어야 했다. 6명이 매일 반복하는 일이고, 복사가 어긋나면
mat 파싱·`audit-approvals.py`·`check-limits.py`가 전부 대상을 못 찾는다.

사용:
    python3 _shared/new-task.py <작업명>
    python3 _shared/new-task.py <작업명> --workers claude-main,codex-main
    python3 _shared/new-task.py <작업명> --goal "결제 API 명세 정리" --dry-run

만드는 것:
    tasks/<작업명>/
    ├── task.md      # `## 메타` yaml + `## Goal` (mat이 파싱하는 형식 그대로)
    ├── context.md
    ├── log.md
    ├── sources/     # 원본 자료
    ├── artifacts/   # 산출물 원본
    └── workers/<역할>/brief.md

**`workers_approved`는 비워 둔다.** 승인 게이트는 사람이 통과시키는 것이고,
스캐폴더가 미리 채우면 게이트가 무의미해진다. `--workers`는 `planned_workers`(계획)만
채운다 — 계획과 승인은 다른 칸이다.

종료코드: 0=생성, 2=이미 존재/잘못된 이름/미정의 역할.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

# 경로 구분자·상대참조 차단. 한글·영숫자·-·_ 만 허용(mat이 폴더명을 그대로 표시한다).
NAME_OK = re.compile(r"^[\w가-힣][\w가-힣.-]*$", re.U)


def die(msg: str) -> None:
    print(f"[error] {msg}", file=sys.stderr)
    raise SystemExit(2)


def known_roles(root: Path) -> list[str]:
    """backends.json이 워커 정본 — flavor마다 풀이 달라 하드코딩하지 않는다."""
    try:
        data = json.loads((root / "_shared" / "backends.json").read_text(encoding="utf-8"))
        return sorted((data.get("workers") or {}).keys())
    except (OSError, json.JSONDecodeError):
        return []


def render(template: Path, subs: list[tuple[str, str]]) -> str:
    text = template.read_text(encoding="utf-8")
    for old, new in subs:
        text = text.replace(old, new)
    return text


def fill_planned(task_md: str, roles: list[str]) -> str:
    """`planned_workers: []` 를 채우고, 바로 뒤의 예시 주석 블록을 걷어낸다."""
    if not roles:
        return task_md
    block = "planned_workers:\n" + "".join(
        f"  - role: {r}\n    purpose:\n" for r in roles)
    task_md = task_md.replace("planned_workers: []\n", block, 1)
    # 예시 주석(`# 예시 (필요한 것만 주석 해제):` ~ 연속된 `#` 줄)은 채운 뒤엔 소음이다
    return re.sub(r"# 예시 \(필요한 것만 주석 해제\):\n(?:#.*\n)*", "", task_md, count=1)


def main() -> int:
    ap = argparse.ArgumentParser(description="MultiAgent 작업 폴더 스캐폴더")
    ap.add_argument("name", help="작업명 (tasks/<이름>/ 으로 생성)")
    ap.add_argument("--workers", default="",
                    help="planned_workers 에 넣을 역할 (쉼표 구분). 승인은 별개")
    ap.add_argument("--goal", default="", help="## Goal 한 문장")
    ap.add_argument("--dry-run", action="store_true", help="만들지 않고 계획만 출력")
    args = ap.parse_args()

    root = Path(os.environ.get("MULTIAGENT_ROOT")
                or Path(__file__).resolve().parent.parent)
    tpl = root / "_templates"
    if not tpl.is_dir():
        die(f"_templates 없음: {tpl} (MULTIAGENT_ROOT 확인)")

    name = args.name.strip()
    if not NAME_OK.match(name):
        die(f"작업명에 쓸 수 없는 문자: '{name}' (한글·영숫자·-·_ 만, 경로 구분자 금지)")

    roles = [r.strip() for r in args.workers.split(",") if r.strip()]
    if roles:
        valid = known_roles(root)
        unknown = [r for r in roles if valid and r not in valid]
        if unknown:
            die(f"미정의 역할 {unknown} — backends.json 기준 유효 역할: {valid}")

    task_dir = root / "tasks" / name
    if task_dir.exists():
        die(f"이미 존재: {task_dir}  (기존 작업 재개는 orchestrator-rules §3 재진입 프로토콜)")

    today = datetime.date.today().isoformat()
    task_md = render(tpl / "task.md", [
        ("# [작업명]", f"# {name}"),
        ("created: <YYYY-MM-DD>", f"created: {today}"),
        ("updated: <YYYY-MM-DD>", f"updated: {today}"),
    ])
    task_md = fill_planned(task_md, roles)
    if args.goal:
        task_md = task_md.replace(
            "한 문장으로. 무엇을 완료 상태로 볼 것인가.", args.goal, 1)

    files: dict[Path, str] = {
        task_dir / "task.md": task_md,
        task_dir / "context.md": render(tpl / "context.md",
                                        [("# Context — [작업명]", f"# Context — {name}")]),
        task_dir / "log.md": render(tpl / "log.md",
                                    [("# Log — [작업명]", f"# Log — {name}")]),
    }
    for role in roles:
        files[task_dir / "workers" / role / "brief.md"] = render(
            tpl / "worker-brief.md",
            [("# Brief — [worker-role] / [작업명]", f"# Brief — {role} / {name}"),
             ("tasks/<task-name>/", f"tasks/{name}/"),
             ("<role>", role)])

    dirs = [task_dir / "sources", task_dir / "artifacts"]

    if args.dry_run:
        print(f"  [dry-run] {task_dir} 에 생성 예정:")
        for p in list(files) + dirs:
            print(f"    {p.relative_to(root)}")
        return 0

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    for p, text in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")

    print(f"  생성 완료: tasks/{name}/  (파일 {len(files)}개)")
    if roles:
        print(f"  planned_workers: {', '.join(roles)}")
    print()
    print("  다음:")
    print(f"    1. tasks/{name}/task.md 의 Goal·Constraints 작성")
    print("    2. 워커 호출 전 사용자 승인 → task.md 의 workers_approved 에 기록")
    print(f"       (승인 없이 호출하면 `python3 _shared/audit-approvals.py tasks/{name}` 가 잡는다)")
    if roles:
        print(f"    3. workers/<역할>/brief.md 작성 후 "
              f"`python3 _shared/check-limits.py tasks/{name}` 로 한도 확인")
    return 0


if __name__ == "__main__":
    sys.exit(main())
