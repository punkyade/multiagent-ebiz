#!/usr/bin/env python3
"""셸 스크립트 이식성 린트 — macOS 기본 bash 3.2에서만 터지는 패턴을 막는다.

배경(2026-08-13 CI macOS 실패): `echo "길이 $LEN자"` 를 썼더니
`line 41: LEN자: unbound variable` 로 죽었다. macOS 기본 `/bin/bash`는 3.2이고
**변수명을 바이트 단위로 읽어 뒤따르는 한글까지 이름에 포함**시킨다. bash 5.x(리눅스·
Git Bash)는 멀티바이트를 인식해 `$LEN`에서 끊으므로 **다른 두 OS에서는 드러나지 않는다.**

이 저장소는 셸 스크립트에 한글 메시지를 많이 쓰므로 재발 가능성이 높다.
해결은 항상 같다: `${VAR}` 로 중괄호를 명시한다.
"""
from __future__ import annotations

import _utf8  # noqa: F401  (출력 인코딩 UTF-8 고정 — 반드시 print보다 먼저)

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# `$VAR` 바로 뒤에 한글(또는 다른 비-ASCII 문자)이 붙은 경우. `${VAR}` 형태는 안전하다.
UNBRACED = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*[^\x00-\x7f]")


def main() -> None:
    hits: list[str] = []
    for p in sorted(REPO.rglob("*.sh")):
        if any(part in (".git", "dist", "node_modules") for part in p.parts):
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue          # 주석은 실행되지 않는다 (이 결함을 설명하는 주석 포함)
            if UNBRACED.search(line):
                hits.append(f"{p.relative_to(REPO).as_posix()}:{i}: {line.strip()[:90]}")

    ok = not hits
    print(f"  {'PASS' if ok else 'FAIL'} 중괄호 없는 $VAR 뒤 비-ASCII 부재 "
          f"(macOS bash 3.2 unbound variable)")
    for h in hits:
        print(f"        ✗ {h}")
    if hits:
        print("        → `${VAR}` 로 중괄호를 명시할 것")

    print(f"test_shell_portability: {'all pass' if ok else f'{len(hits)} fail'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
