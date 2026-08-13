#!/usr/bin/env python3
"""컨텍스트 한도 검사(_shared/check-limits.py) 회귀 테스트. 외부 호출 없음.

핵심 가드는 C3 — 표준 `worker-brief.md` 템플릿을 그대로 채운 brief가 위반으로
잡히면 안 된다. 템플릿(원문 1455자)은 안내 주석과 고정 규약 블록을 포함하므로
원문 기준으로 재면 빈 스캐폴드조차 한도를 넘는다. 그 상태로 배포하면 검사기가
첫날부터 전량 오탐하고 아무도 안 쓰게 된다.
"""
from __future__ import annotations

import _utf8  # noqa: F401  (출력 인코딩 UTF-8 고정 — 반드시 print보다 먼저)

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHECK = REPO / "_shared" / "check-limits.py"
BRIEF_TEMPLATE = REPO / "_templates" / "worker-brief.md"
CONTEXT_TEMPLATE = REPO / "_templates" / "context.md"


def make_task(base: Path, context: str | None = None,
              briefs: dict[str, str] | None = None) -> Path:
    d = base / "t"
    d.mkdir(parents=True, exist_ok=True)
    if context is not None:
        (d / "context.md").write_text(context, encoding="utf-8", newline="\n")
    for role, text in (briefs or {}).items():
        (d / "workers" / role).mkdir(parents=True, exist_ok=True)
        (d / "workers" / role / "brief.md").write_text(text, encoding="utf-8", newline="\n")
    return d


def run(task_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CHECK), str(task_dir)],
                          capture_output=True, text=True, encoding="utf-8")


def case(name: str, expect_rc: int, context=None, briefs=None,
         expect_in_out: str | None = None) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        d = make_task(Path(tmp), context, briefs)
        r = run(d)
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

    # C1 짧은 brief·context → 통과
    fails += case("C1 짧은 brief·context → 통과", 0,
                  context="# Context\n\n짧은 스냅샷.\n",
                  briefs={"claude-main": "# Brief\n\n목적 한 줄.\n"})

    # C2 명백한 초과 → 검출
    fails += case("C2 3000자 brief → 초과 검출", 1,
                  briefs={"codex-main": "# Brief\n\n" + ("가" * 3000) + "\n"},
                  expect_in_out="초과")

    # C3 (핵심) 표준 템플릿 그대로 → 오탐 없음
    fails += case("C3 표준 brief 템플릿 → 오탐 없음", 0,
                  briefs={"codex-main": BRIEF_TEMPLATE.read_text(encoding="utf-8")})

    # C3b 표준 context 템플릿 그대로 → 오탐 없음
    fails += case("C3b 표준 context 템플릿 → 오탐 없음", 0,
                  context=CONTEXT_TEMPLATE.read_text(encoding="utf-8"))

    # C4 고정 규약 블록·주석은 한도에서 제외돼야 (그것만으로는 초과 불가)
    fixed_only = BRIEF_TEMPLATE.read_text(encoding="utf-8")
    fails += case("C4 주석·고정블록은 한도 계산 제외", 0,
                  briefs={"gemini": fixed_only})

    # C5 영문 brief는 단어수로 판정 (240단어 이하면 글자수 초과여도 통과)
    english = "# Brief\n\n" + ("word " * 200) + "\n"
    fails += case("C5 영문 200단어 → 통과(단어 기준)", 0,
                  briefs={"claude-main": english})

    # C6 context 한도(1500)도 적용
    fails += case("C6 context 4000자 → 초과 검출", 1,
                  context="# Context\n\n" + ("나" * 4000) + "\n",
                  expect_in_out="context.md")

    print(f"test_limits: {'all pass' if not fails else f'{fails} fail'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
