#!/usr/bin/env python3
"""S9/A1: update 모드가 tasks/·_local/ 사용자 데이터를 보존하고
시스템 파일은 갱신하는지. 순수 파일시스템, 외부 호출 없음.
"""
from __future__ import annotations

import _utf8  # noqa: F401  (출력 인코딩 UTF-8 고정 — 반드시 print보다 먼저)

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "plugins" / "multi-agent-starter" / "skills" / "configure-multiagent" / "generator"
FLAVOR = "claude"  # update 동작은 flavor 무관 — 대표로 claude


def init(tgt: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GEN / "init.py"),
         "--flavor", FLAVOR, "--target", str(tgt), "--yes", "--no-validate"],
        capture_output=True, text=True, encoding="utf-8",
    )


def main() -> None:
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        tgt = Path(d) / "sys"
        if init(tgt).returncode != 0:
            print("  FAIL 초기 init")
            sys.exit(1)

        # 사용자 데이터 심기
        ut = tgt / "tasks" / "my-task"
        ut.mkdir(parents=True)
        (ut / "task.md").write_text("USER DATA", encoding="utf-8")
        ul = tgt / "_local"
        ul.mkdir(parents=True, exist_ok=True)
        (ul / "learnings.md").write_text("LOCAL", encoding="utf-8")

        # 시스템 파일 변조(update가 되돌리는지)
        (tgt / "_shared" / "routing.md").write_text("STALE", encoding="utf-8")

        # 지침파일에 loadout store 블록 심기(update가 보존하는지 — v3.4 결함 수정)
        block = ("<!-- store:no-yesman:start -->\n"
                 "예스맨 금지 규칙 본문\n"
                 "<!-- store:no-yesman:end -->")
        instr = tgt / "CLAUDE.md"
        before = instr.read_text(encoding="utf-8")
        instr.write_text(before + "\n" + block + "\n", encoding="utf-8")

        if init(tgt).returncode != 0:  # update 모드
            print("  FAIL update init")
            sys.exit(1)

        bak = tgt / "CLAUDE.md.multiagent-bak"
        checks = [
            ("tasks/my-task/task.md 보존",
             (ut / "task.md").read_text(encoding="utf-8") == "USER DATA"),
            ("_local/learnings.md 보존",
             (ul / "learnings.md").read_text(encoding="utf-8") == "LOCAL"),
            ("_shared/routing.md 갱신",
             (tgt / "_shared" / "routing.md").read_text(encoding="utf-8") != "STALE"),
            ("CLAUDE.md store 블록 보존",
             block in instr.read_text(encoding="utf-8")),
            ("CLAUDE.md 덮어쓰기 전 백업 생성",
             bak.is_file() and block in bak.read_text(encoding="utf-8")),
        ]
        for desc, ok in checks:
            print(f"  {'PASS' if ok else 'FAIL'} {desc}")
            fails += not ok

    fails += existing_project_checks()
    print(f"test_update_preserve: {'all pass' if not fails else f'{fails} fail'}")
    sys.exit(1 if fails else 0)


def existing_project_checks() -> int:
    """기존 프로젝트 폴더에 얹을 때 프로젝트 파일을 갈아엎지 않아야 한다.

    이게 정상 경로다 — 팀원은 각자 자기 프로젝트 폴더에 시스템을 얹는다.
    실제 사고 2건(ssaksseuri: CLAUDE.md 유실 / Pipleline: README 교체 + .gitignore 삭제로
    빌드 산출물이 git에 노출)이 이 테스트가 없어서 났다.
    """
    import json
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        tgt = Path(d) / "proj"
        tgt.mkdir()
        # 프로젝트가 이미 갖고 있던 파일들
        (tgt / "README.md").write_text("# 내 프로젝트\n", encoding="utf-8", newline="\n")
        (tgt / ".gitignore").write_text("*.exe\nlogs/\n", encoding="utf-8", newline="\n")
        (tgt / "LICENSE").write_text("내 라이선스\n", encoding="utf-8", newline="\n")
        (tgt / ".mcp.json").write_text(
            json.dumps({"mcpServers": {"my-server": {"command": "mine"}}}, ensure_ascii=False),
            encoding="utf-8", newline="\n")

        if init(tgt).returncode != 0:
            print("  FAIL 기존 프로젝트 폴더 init")
            return 1

        checks = [
            ("기존 README.md 보존",
             (tgt / "README.md").read_text(encoding="utf-8") == "# 내 프로젝트\n"),
            ("기존 .gitignore 보존",
             "*.exe" in (tgt / ".gitignore").read_text(encoding="utf-8")),
            ("기존 LICENSE 보존",
             (tgt / "LICENSE").read_text(encoding="utf-8") == "내 라이선스\n"),
            ("시스템 파일은 정상 설치",
             (tgt / "_shared" / "routing.md").is_file() and (tgt / "CLAUDE.md").is_file()),
        ]
        mcp = json.loads((tgt / ".mcp.json").read_text(encoding="utf-8"))
        checks += [
            ("기존 MCP 서버 보존", "my-server" in mcp.get("mcpServers", {})),
            ("템플릿 MCP 서버 추가", "codex" in mcp.get("mcpServers", {})),
        ]
        for desc, ok in checks:
            print(f"  {'PASS' if ok else 'FAIL'} {desc}")
            fails += not ok
    return fails


if __name__ == "__main__":
    main()
