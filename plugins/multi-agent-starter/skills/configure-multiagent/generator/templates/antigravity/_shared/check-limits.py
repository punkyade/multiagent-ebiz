#!/usr/bin/env python3
"""컨텍스트 한도 실측 검사 — brief.md / context.md 가 문서화된 한도 안에 있는지.

지금까지 한도(brief ≤1200자·240단어, context ≤1500자·300단어)는 **문서에만** 있었다.
`check-invariants.sh`의 INV4가 하는 일은 "문서에 `1200자`라는 글자가 존재하는가" 확인뿐이라
실제 brief가 3000자여도 모든 검사가 PASS한다. 강제하지 않는 숫자는 거짓 안전신호다.

측정 대상 — "오케스트레이터가 쓴 내용"만:
  · HTML 주석 제거        — 템플릿의 안내문(`<!-- HARD LIMIT … -->`)은 브리핑 내용이 아니다
  · 고정 규약 블록 제거    — `## Worker 행동 규약`은 모든 brief에 강제되는 175자 상수라
                            오케스트레이터가 줄일 수 없다. 한도의 취지는 가변부를 묶는 것.
판정: 한글 문서는 **글자수**, 영문 문서는 **단어수** 기준(문서화된 "1200자 한글 /
240단어 영문"을 그대로 옮긴 것). 둘 중 느슨한 쪽을 고르는 OR 판정은 쓰지 않는다 —
공백 없는 한글 3000자가 "1단어"로 세어져 통과해 버린다.

사용:
    python3 _shared/check-limits.py                # tasks/ 전체
    python3 _shared/check-limits.py tasks/<작업>    # 한 작업만
    python3 _shared/check-limits.py --verbose      # 통과 항목의 실측치도 출력

종료코드: 0=위반 없음, 1=초과 있음, 2=대상 없음.

한도 초과 시 답은 "줄이기" 아니면 "packet 분리"다 — 자료는 brief에 인라인하지 말고
`sources/`에 두고 디스패처 3번째 인자로 동봉한다(`call_worker.sh <role> <brief> <packet>`).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
# `## Worker 행동 규약 …` ~ 다음 `## ` 직전까지 (문서 끝까지인 경우도 포함)
FIXED_BLOCK = re.compile(r"##\s*Worker 행동 규약.*?(?=\n##\s|\Z)", re.S)

# (파일명, 글자 한도, 단어 한도) — CLAUDE.md "Context Rules" 표와 같은 값
LIMITS = {
    "brief.md": (1200, 240),
    "context.md": (1500, 300),
}


def measure(text: str) -> tuple[int, int, int, int]:
    """→ (raw_chars, raw_words, content_chars, content_words)"""
    content = FIXED_BLOCK.sub("", HTML_COMMENT.sub("", text))
    return len(text), len(text.split()), len(content.strip()), len(content.split())


def is_korean(text: str) -> bool:
    """한글 비중으로 판정 기준을 고른다. 한글이 공백 아닌 글자의 10% 이상이면 한글 문서.
    이 팀 문서는 코드 식별자가 섞인 한글이 기본이라 낮은 임계로 충분하다."""
    hangul = sum(1 for ch in text
                 if "가" <= ch <= "힣" or "㄰" <= ch <= "㆏")
    dense = sum(1 for ch in text if not ch.isspace())
    return hangul >= 0.10 * max(1, dense)


def targets(task_dir: Path) -> list[Path]:
    out = [task_dir / "context.md"]
    out += sorted((task_dir / "workers").glob("*/brief.md"))
    return [p for p in out if p.is_file()]


def check_task(task_dir: Path, verbose: bool) -> tuple[int, list[str]]:
    lines: list[str] = []
    violations = 0
    files = targets(task_dir)
    if not files:
        return 0, [f" [SKIP] {task_dir.name} (brief·context 없음)"]

    for p in files:
        limit_c, limit_w = LIMITS[p.name]
        text = p.read_text(encoding="utf-8")
        raw_c, raw_w, con_c, con_w = measure(text)
        ko = is_korean(text)
        actual, limit, unit = (con_c, limit_c, "자") if ko else (con_w, limit_w, "단어")
        rel = p.relative_to(task_dir)
        if actual > limit:
            violations += 1
            lines.append(f"        ✗ {rel} — {actual}{unit} "
                         f"(한도 {limit}{unit}, {actual - limit}{unit} 초과)")
            lines.append(f"          → 줄이거나, 자료는 sources/ packet으로 분리해 "
                         f"디스패처 3번째 인자로 동봉")
        elif verbose:
            lines.append(f"        · {rel} — {actual}/{limit}{unit} "
                         f"({'한글' if ko else '영문'} 기준, 원문 {raw_c}자/{raw_w}단어)")
    return violations, lines


def main() -> int:
    argv = [a for a in sys.argv[1:] if a not in ("-v", "--verbose")]
    verbose = len(argv) != len(sys.argv[1:])
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    if argv:
        dirs = [Path(argv[0]).expanduser().resolve()]
        if not dirs[0].is_dir():
            print(f"[error] 작업 폴더 없음: {dirs[0]}", file=sys.stderr)
            return 2
    else:
        root = Path(os.environ.get("MULTIAGENT_ROOT")
                    or Path(__file__).resolve().parent.parent)
        tasks = root / "tasks"
        if not tasks.is_dir():
            print(f"[error] tasks 폴더 없음: {tasks}", file=sys.stderr)
            return 2
        dirs = sorted(d for d in tasks.iterdir()
                      if d.is_dir() and not d.name.startswith("."))

    if not dirs:
        print("검사할 작업 폴더가 없습니다 (tasks/ 비어 있음).")
        return 0

    total = 0
    print(f"컨텍스트 한도 검사 — 작업 {len(dirs)}개")
    for d in dirs:
        v, lines = check_task(d, verbose)
        total += v
        if not lines:
            print(f" [PASS] {d.name}")
        else:
            head = "SKIP" if lines[0].startswith(" [SKIP]") else ("FAIL" if v else "PASS")
            if lines[0].startswith(" [SKIP]"):
                print(lines[0])
                continue
            print(f" [{head}] {d.name}")
            for ln in lines:
                print(ln)

    print("-" * 40)
    if total:
        print(f"한도 초과 {total}건 — brief는 실행에 필요한 것만, 자료는 경로로 전달한다.")
        return 1
    print("한도 초과 0건.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
