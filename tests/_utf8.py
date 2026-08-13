"""표준 출력 인코딩을 UTF-8로 고정 — import 하는 것만으로 적용된다.

테스트는 결과를 한글로 출력한다. 로케일이 UTF-8이 아닌 환경에서는 그 print 한 줄이
`UnicodeEncodeError`로 죽어 **테스트 내용과 무관하게 스위트가 전멸한다.**

실제 사례(2026-08-13): CI windows-latest는 영문 로케일(cp1252)이라 Python 테스트 5개가
전부 첫 print에서 크래시했다. 한국어 Windows(cp949)는 한글을 인코딩할 수 있어 로컬에서는
끝내 재현되지 않았다 — "로컬 통과"가 안전을 보장하지 못한 대표 사례.

재현: `PYTHONIOENCODING=cp1252 python3 tests/test_audit.py`

사용: 각 테스트 파일 상단에 `import _utf8  # noqa: F401`
(테스트를 직접 실행하든 run.sh로 돌리든 동일하게 적용되도록 코드 쪽에 둔다.)
"""
from __future__ import annotations

import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):  # 비-TextIO로 리다이렉트된 경우
        pass
