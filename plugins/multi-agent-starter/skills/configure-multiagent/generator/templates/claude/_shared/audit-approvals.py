#!/usr/bin/env python3
"""승인 게이트 사후 감사 — log.md의 실제 워커 호출이 task.md 승인과 일치하는지 검사.

승인 게이트는 이 시스템의 핵심 안전 속성이지만, 지금까지 **지켜졌는지 확인할 수단이
없었다**(오케스트레이터가 지시를 따를 것이라는 신뢰에만 의존). 혼자 쓸 땐 괜찮지만
여러 명이 각자 돌리면 명예 규정이 된다. 이 스크립트가 사후 증거를 대조한다.

검사 항목 (작업 폴더별):
  A1  log.md의 [WORKER_CALL] 워커가 task.md의 workers_approved에 있는가  → 없으면 FAIL
  A2  brief의 write_scope가 외부 경로 패턴이면 4조건이 충족됐는가         → 미충족 FAIL
        (target_repo 명시 + log.md에 [APPROVAL] 외부 쓰기 기록)
  A3  승인됐지만 호출되지 않은 워커                                        → INFO(위반 아님)

사용:
    python3 _shared/audit-approvals.py              # <root>/tasks 전체
    python3 _shared/audit-approvals.py <작업폴더>    # 한 작업만
    MULTIAGENT_ROOT=<경로> python3 _shared/audit-approvals.py

종료코드: 0=위반 없음, 1=위반 있음, 2=검사 대상 없음/구조 오류.

bash가 아니라 Python인 이유: Windows 팀원이 Git Bash 없이도 돌릴 수 있어야 하고,
주석 블록·yaml 목록 파싱은 grep보다 파서가 안전하기 때문이다.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# 로케일이 UTF-8이 아닌 환경(예: 한국어 Windows cp949)에서 한글 출력이
# UnicodeEncodeError로 죽지 않도록 표준 출력 인코딩을 고정한다.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
# [2026-05-11 14:45] [WORKER_CALL] claude-main brief 전달 …  → 태그 뒤 첫 토큰이 역할명
WORKER_CALL = re.compile(r"^\s*\[[^\]]+\]\s*\[WORKER_CALL\]\s*([^\s,.:;]+)", re.M)
APPROVAL_LINE = re.compile(r"^\s*\[[^\]]+\]\s*\[APPROVAL\]\s*(.+)$", re.M)
# write_scope: none | tasks-only | "src/**, tests/**"
WRITE_SCOPE = re.compile(r"^\s*write_scope:\s*(.+?)\s*$", re.M)
TARGET_REPO = re.compile(r"^\s*target_repo:\s*(.+?)\s*$", re.M)

INTERNAL_SCOPES = {"none", "tasks-only"}


def strip_comments(text: str) -> str:
    """HTML 주석 제거. log.md 템플릿은 주석 안에 [WORKER_CALL] 예시를 담고 있어
    이걸 걷어내지 않으면 모든 새 작업이 위반으로 오탐된다."""
    return HTML_COMMENT.sub("", text)


def read(p: Path) -> str | None:
    return p.read_text(encoding="utf-8") if p.is_file() else None


def approved_workers(task_md: str) -> set[str]:
    """task.md의 `workers_approved:` 목록에서 worker 이름 집합을 뽑는다.

    yaml 파서를 쓰지 않는 이유: 템플릿이 승인 예시를 `#` 주석으로 담고 있어
    (`# - worker: claude-main`) 주석을 살려둔 채 구조만 읽어야 하고, PyYAML을
    이 저장소의 런타임 의존성으로 추가하고 싶지 않다.
    """
    approved: set[str] = set()
    in_block = False
    for raw in task_md.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue                      # yaml 주석·빈 줄 무시
        if re.match(r"^workers_approved\s*:", stripped):
            # `workers_approved: []` 인라인 빈 목록이면 블록을 열지 않는다
            in_block = stripped.split(":", 1)[1].strip() != "[]"
            continue
        if in_block:
            # 블록은 "들여쓰기된 줄" 또는 "목록 항목"이 이어지는 동안만 유효하다.
            # 최상위 키(예: planned_workers:)를 만나면 종료.
            # 주의: approved_at 같은 하위 키에서 끊지 말 것 — 끊으면 두 번째
            # 승인 워커부터 통째로 누락돼 감사가 조용히 무력화된다.
            if not line.startswith((" ", "\t")) and not stripped.startswith("- "):
                in_block = False
                continue
            m = re.match(r"^-\s*worker\s*:\s*(\S+)", stripped)
            if m:
                approved.add(m.group(1).strip("\"'"))
    return approved


def called_workers(log_md: str) -> list[str]:
    return WORKER_CALL.findall(strip_comments(log_md))


def external_write_briefs(task_dir: Path) -> list[tuple[str, str, str | None]]:
    """(role, write_scope, target_repo) — write_scope가 외부 경로 패턴인 brief만."""
    out: list[tuple[str, str, str | None]] = []
    workers = task_dir / "workers"
    if not workers.is_dir():
        return out
    for brief in sorted(workers.glob("*/brief.md")):
        text = strip_comments(read(brief) or "")
        m = WRITE_SCOPE.search(text)
        if not m:
            continue
        scope = m.group(1).strip().strip("\"'")
        if scope in INTERNAL_SCOPES or not scope:
            continue
        tr = TARGET_REPO.search(text)
        target = tr.group(1).strip().strip("\"'") if tr else None
        if target in ("N/A", "<absolute-path>", ""):
            target = None
        out.append((brief.parent.name, scope, target))
    return out


def audit_task(task_dir: Path) -> tuple[list[str], list[str], list[str]]:
    """→ (violations, infos, structure_notes)"""
    viol: list[str] = []
    info: list[str] = []
    note: list[str] = []

    task_md = read(task_dir / "task.md")
    log_md = read(task_dir / "log.md")
    if task_md is None:
        note.append("task.md 없음 — 감사 불가")
        return viol, info, note
    if log_md is None:
        note.append("log.md 없음 — 호출 기록이 없어 감사 생략")
        return viol, info, note

    approved = approved_workers(task_md)
    called = called_workers(log_md)
    called_set = dict.fromkeys(called)  # 순서 보존 + 중복 제거

    # A1 승인 없이 호출된 워커
    for role in called_set:
        if role not in approved:
            n = called.count(role)
            viol.append(f"A1 승인 없이 호출됨: '{role}' ({n}회) — "
                        f"task.md workers_approved에 항목 없음")

    # A2 외부 repo 쓰기 4조건
    ext = external_write_briefs(task_dir)
    if ext:
        appr_text = "\n".join(APPROVAL_LINE.findall(strip_comments(log_md)))
        has_ext_approval = ("외부" in appr_text) or ("write_scope" in appr_text)
        for role, scope, target in ext:
            if target is None:
                viol.append(f"A2 외부 쓰기 조건 미충족: '{role}' write_scope={scope} 인데 "
                            f"brief에 target_repo 절대경로가 없음")
            if not has_ext_approval:
                viol.append(f"A2 외부 쓰기 조건 미충족: '{role}' write_scope={scope} 인데 "
                            f"log.md에 [APPROVAL] 외부 쓰기 기록 없음")

    # A3 승인만 되고 미호출 (위반 아님 — 최소 set 원칙상 오히려 정상일 수 있음)
    for role in sorted(approved - set(called_set)):
        info.append(f"A3 승인됐지만 호출되지 않음: '{role}'")

    if not called_set:
        note.append("워커 호출 기록 없음")
    return viol, info, note


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    if argv:
        targets = [Path(argv[0]).expanduser().resolve()]
        if not targets[0].is_dir():
            print(f"[error] 작업 폴더 없음: {targets[0]}", file=sys.stderr)
            return 2
    else:
        root = Path(os.environ.get("MULTIAGENT_ROOT")
                    or Path(__file__).resolve().parent.parent)
        tasks = root / "tasks"
        if not tasks.is_dir():
            print(f"[error] tasks 폴더 없음: {tasks}", file=sys.stderr)
            return 2
        targets = sorted(d for d in tasks.iterdir()
                         if d.is_dir() and not d.name.startswith("."))

    if not targets:
        print("감사할 작업 폴더가 없습니다 (tasks/ 비어 있음).")
        return 0

    total_v = total_i = 0
    print(f"승인 게이트 감사 — 작업 {len(targets)}개")
    for d in targets:
        viol, info, note = audit_task(d)
        total_v += len(viol)
        total_i += len(info)
        status = "FAIL" if viol else "PASS"
        detail = f" ({note[0]})" if note and not viol else ""
        print(f" [{status}] {d.name}{detail}")
        for v in viol:
            print(f"        ✗ {v}")
        for i in info:
            print(f"        · {i}")

    print("-" * 40)
    if total_v:
        print(f"위반 {total_v}건 — 승인 없이 호출된 워커가 있습니다. "
              f"task.md의 workers_approved와 log.md를 대조해 원인을 확인하세요.")
        return 1
    print(f"위반 0건 (참고 {total_i}건). 모든 워커 호출이 승인 기록과 일치합니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
