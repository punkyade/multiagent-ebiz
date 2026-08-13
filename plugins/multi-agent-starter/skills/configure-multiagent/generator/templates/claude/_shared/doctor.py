#!/usr/bin/env python3
"""환경 진단 — 이 시스템이 실제로 돌 수 있는 상태인지 확인한다.

팀이 Windows·macOS 혼재라 "왜 안 돌아요"가 지원 부담의 대부분이 된다. 이 스크립트가
필요한 도구·설정을 한 번에 확인하고, 빠진 것과 그 영향을 구체적으로 알려준다.

검사 항목:
  D1  핵심 도구        python3 · bash · jq  (디스패처가 bash 스크립트 + jq 파싱)
  D2  선택 도구        git  (codex CLI 폴백에서 기본 요구)
  D3  backends.json    파싱 + 워커별 call_type 구조
  D4  워커 백엔드      backends.json이 선언한 cli 명령(agy·codex 등)이 PATH에 있는가
  D5  MCP 설정         mcp 워커가 있으면 .mcp.json 존재 여부
  D6  디스패처 동작    call_worker.sh --merged-preview 드라이런 (모델 호출 없음·무료)

사용:
    python3 _shared/doctor.py
    MULTIAGENT_ROOT=<경로> python3 _shared/doctor.py

종료코드: 0=핵심 이상 없음(경고는 있을 수 있음), 1=핵심 도구/설정 누락.
bash가 아니라 Python인 이유: bash 자체가 없는 Windows에서도 "bash가 없다"를 알려줘야 한다.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

FAIL, WARN, OK = "FAIL", "WARN", "PASS"
results: list[tuple[str, str]] = []


def emit(status: str, msg: str) -> None:
    results.append((status, msg))
    print(f" [{status}] {msg}")


def version_of(cmd: str) -> str:
    # which() 결과를 쓴다 — Windows에서 `codex`는 확장자 없는 셸 스크립트라
    # 이름만으로는 exec되지 않고, which가 PATHEXT를 따라 .cmd를 찾아준다.
    resolved = shutil.which(cmd) or cmd
    for flag in ("--version", "-version", "version"):
        try:
            r = subprocess.run([resolved, flag], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=15)
            line = (r.stdout or r.stderr or "").strip().splitlines()
            if line:
                return line[0][:60]
        except (OSError, subprocess.SubprocessError):
            continue
    return "(버전 확인 불가)"


def main() -> int:
    root = Path(os.environ.get("MULTIAGENT_ROOT")
                or Path(__file__).resolve().parent.parent)
    print(f"MultiAgent doctor — ROOT={root}")
    print(f"  OS={platform.system()} {platform.release()} · "
          f"Python={platform.python_version()} · 기본인코딩={sys.getdefaultencoding()}")
    print("-" * 40)

    backends_path = root / "_shared" / "backends.json"
    dispatcher = root / "_shared" / "adapters" / "call_worker.sh"

    # D3 backends.json 먼저 — 이후 검사의 필요 범위를 여기서 정한다
    workers: dict = {}
    try:
        data = json.loads(backends_path.read_text(encoding="utf-8"))
        workers = data.get("workers") or {}
        emit(OK, f"D3 backends.json 파싱 OK (flavor={data.get('flavor')}, "
                 f"워커 {len(workers)}개: {', '.join(sorted(workers))})")
    except FileNotFoundError:
        emit(FAIL, f"D3 backends.json 없음: {backends_path}")
    except (json.JSONDecodeError, OSError) as e:
        emit(FAIL, f"D3 backends.json 파싱 실패: {e}")

    call_types = {r.get("call_type") for r in workers.values() if isinstance(r, dict)}
    for rec in workers.values():
        for fb in (rec.get("fallbacks") or []) if isinstance(rec, dict) else []:
            call_types.add(fb.get("call_type"))
    needs_dispatcher = bool(call_types & {"cli", "api"})

    # D1 핵심 도구
    if needs_dispatcher:
        for tool, why in (("bash", "디스패처가 bash 스크립트"),
                          ("jq", "디스패처 JSON 파싱")):
            path = shutil.which(tool)
            if path:
                emit(OK, f"D1 {tool} — {version_of(tool)}")
            else:
                emit(FAIL, f"D1 {tool} 없음 — {why}. cli/api 워커를 호출할 수 없다"
                           + (" (Windows: Git Bash 설치 / winget install jqlang.jq)"
                              if platform.system() == "Windows" else ""))
    else:
        emit(OK, "D1 cli/api 워커 없음 — bash·jq 불필요 (native·mcp만 사용)")

    # D2 git (선택)
    if shutil.which("git"):
        emit(OK, f"D2 git — {version_of('git')}")
    else:
        emit(WARN, "D2 git 없음 — codex CLI 폴백이 기본 요구한다"
                   " (우회: MULTIAGENT_CODEX_SKIP_GIT=1). 정상 MCP 경로는 무관")

    # D4 워커 백엔드 실행파일
    for role, rec in sorted(workers.items()):
        if not isinstance(rec, dict):
            continue
        cmds = []
        if rec.get("call_type") == "cli":
            cmds.append(rec.get("cli", {}).get("command"))
        if rec.get("call_type") == "mcp":
            tool = rec.get("mcp", {}).get("tool", "")
            if "codex" in tool:
                cmds.append("codex")     # MCP 서버가 codex 바이너리로 뜬다
        for fb in rec.get("fallbacks") or []:
            if fb.get("call_type") == "cli":
                cmds.append(fb.get("cli", {}).get("command"))
        for cmd in [c for c in dict.fromkeys(cmds) if c]:
            if shutil.which(cmd):
                emit(OK, f"D4 {role} 백엔드 '{cmd}' — {version_of(cmd)}")
            else:
                emit(WARN, f"D4 {role} 백엔드 '{cmd}' 없음 — 이 워커는 호출 불가")

    # D5 MCP 설정
    if "mcp" in call_types:
        mcp = root / ".mcp.json"
        if mcp.is_file():
            emit(OK, "D5 .mcp.json 존재 (mcp 워커용)")
        else:
            emit(WARN, "D5 .mcp.json 없음 — mcp 워커는 호스트 설정에 의존한다")

    # D6 디스패처 드라이런 (모델 호출 없음)
    if not needs_dispatcher:
        pass
    elif not dispatcher.is_file():
        emit(FAIL, f"D6 디스패처 없음: {dispatcher}")
    elif not shutil.which("bash"):
        emit(WARN, "D6 디스패처 드라이런 건너뜀 (bash 없음)")
    else:
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp) / "brief.md"
            p = Path(tmp) / "packet.md"
            b.write_text("# Brief\n\n드라이런.\n", encoding="utf-8", newline="\n")
            p.write_text("동봉 자료 샘플\n", encoding="utf-8", newline="\n")
            # 경로는 POSIX 표기로 넘긴다 — 역슬래시를 그대로 주면 bash가 이스케이프로 먹는다.
            # bash도 which로 고정한다: Windows에서 이름만 쓰면 System32의 WSL bash로
            # 해석될 수 있고, WSL bash는 C:/… 경로를 못 읽어 "No such file"이 된다.
            try:
                r = subprocess.run([shutil.which("bash") or "bash",
                                    dispatcher.as_posix(), "--merged-preview",
                                    b.as_posix(), p.as_posix()],
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=60)
                if r.returncode == 0 and "동봉 자료" in (r.stdout or ""):
                    emit(OK, "D6 디스패처 드라이런 OK (--merged-preview, 모델 호출 없음)")
                else:
                    emit(FAIL, f"D6 디스패처 드라이런 실패 (exit {r.returncode}): "
                               f"{(r.stderr or '').strip()[:120]}")
            except (OSError, subprocess.SubprocessError) as e:
                emit(FAIL, f"D6 디스패처 드라이런 오류: {e}")

    print("-" * 40)
    f = sum(1 for s, _ in results if s == FAIL)
    w = sum(1 for s, _ in results if s == WARN)
    if f:
        print(f"핵심 이상 {f}건 (경고 {w}건) — 위 FAIL 항목을 해결해야 시스템이 돈다.")
        return 1
    print(f"핵심 이상 없음 (경고 {w}건)."
          + (" 경고 항목은 해당 워커만 사용 불가이며 나머지는 정상 동작한다." if w else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
