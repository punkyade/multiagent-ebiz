#!/usr/bin/env python3
"""환경 진단(_shared/doctor.py) 회귀 테스트. 외부·유료 모델 호출 없음.

환경 의존 도구라 "무엇이 설치됐는가"는 단언할 수 없다. 대신 **어떤 OS에서도 죽지 않고
구조적으로 올바른 판정을 내는지**를 본다 — CI 3-OS 매트릭스에서 이게 진짜 값이다.
(Windows 경로를 bash에 넘기다 깨지는 부류의 결함이 여기서 잡힌다.)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOCTOR = REPO / "_shared" / "doctor.py"


def run(root: Path) -> subprocess.CompletedProcess:
    import os
    env = dict(os.environ, MULTIAGENT_ROOT=str(root), PYTHONUTF8="1")
    return subprocess.run([sys.executable, str(DOCTOR)], capture_output=True,
                          text=True, encoding="utf-8", env=env, timeout=300)


def main() -> None:
    fails = 0

    # C1 실제 저장소에서 크래시 없이 판정 (rc 0 또는 1, 트레이스백 없음)
    r = run(REPO)
    ok = r.returncode in (0, 1) and "Traceback" not in (r.stderr or "")
    print(f"  {'PASS' if ok else 'FAIL'} C1 저장소 루트에서 크래시 없이 실행 (rc={r.returncode})")
    if not ok:
        print("        " + (r.stderr or "").strip()[:400])
    fails += not ok

    # C2 핵심 검사 항목이 모두 보고되는가
    out = r.stdout or ""
    missing = [t for t in ("D1", "D3", "D4") if f"[{t}" not in out.replace("] ", "] ")
               and t not in out]
    ok2 = not missing
    print(f"  {'PASS' if ok2 else 'FAIL'} C2 핵심 항목 보고 (누락: {missing or '-'})")
    fails += not ok2

    # C3 디스패처가 있고 bash가 있으면 드라이런이 통과해야 (경로 처리 회귀 가드)
    if shutil.which("bash"):
        ok3 = "D6 디스패처 드라이런 OK" in out
        print(f"  {'PASS' if ok3 else 'FAIL'} C3 디스패처 드라이런 통과")
        if not ok3:
            print("        " + "\n        ".join(
                l for l in out.splitlines() if "D6" in l))
        fails += not ok3
    else:
        print("  SKIP C3 (bash 없음)")

    # C4 backends.json이 깨진 루트 → FAIL 판정 + 크래시 없음
    with tempfile.TemporaryDirectory() as tmp:
        broken = Path(tmp) / "sys"
        (broken / "_shared").mkdir(parents=True)
        (broken / "_shared" / "backends.json").write_text("{ not json",
                                                          encoding="utf-8", newline="\n")
        rb = run(broken)
        ok4 = rb.returncode == 1 and "Traceback" not in (rb.stderr or "")
        print(f"  {'PASS' if ok4 else 'FAIL'} C4 깨진 backends.json → FAIL 판정 (rc={rb.returncode})")
        fails += not ok4

    # C5 워커 0개인 정상 JSON → 크래시 없이 처리
    with tempfile.TemporaryDirectory() as tmp:
        empty = Path(tmp) / "sys"
        (empty / "_shared").mkdir(parents=True)
        (empty / "_shared" / "backends.json").write_text(
            json.dumps({"schema_version": "1", "flavor": "claude", "workers": {}}),
            encoding="utf-8", newline="\n")
        re_ = run(empty)
        ok5 = re_.returncode in (0, 1) and "Traceback" not in (re_.stderr or "")
        print(f"  {'PASS' if ok5 else 'FAIL'} C5 워커 0개 → 크래시 없음 (rc={re_.returncode})")
        fails += not ok5

    print(f"test_doctor: {'all pass' if not fails else f'{fails} fail'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
