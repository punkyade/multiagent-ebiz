#!/usr/bin/env python3
"""L1/A2: 각 flavor를 임시폴더에 생성 → validate가 전부 PASS인지.

외부 호출 없음, 결정적. validate 체크 *개수*는 하드코딩하지 않는다
(F4 등으로 체크가 늘어도 안 깨지도록 — "전부 PASS"와 exit 0만 단언).

knot·요금가드 설치는 v3.0.0부터 loadout 담당 — 주입 테스트는 제거했고,
기본 생성물에 그 잔재(관리블록·가드 배선)가 없다는 부재 단언만 남긴다.
"""
from __future__ import annotations

import _utf8  # noqa: F401  (출력 인코딩 UTF-8 고정 — 반드시 print보다 먼저)

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "plugins" / "multi-agent-starter" / "skills" / "configure-multiagent" / "generator"
FLAVORS = sorted(p.name for p in (GEN / "templates").iterdir() if p.is_dir())
INSTRUCTION_FILE = {"claude": "CLAUDE.md", "codex": "AGENTS.md", "antigravity": "AGENTS.md"}
KNOT_START, KNOT_END = "<!-- knot:start -->", "<!-- knot:end -->"


def run(args: list[str]) -> subprocess.CompletedProcess:
    # encoding 명시: 생성기 스크립트는 UTF-8로 출력한다. 미지정 시 부모가 로케일
    # 인코딩(예: 한국어 Windows cp949)으로 디코딩해 한글 출력에서 깨진다.
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


def init(tgt: Path, f: str) -> subprocess.CompletedProcess:
    return run([sys.executable, str(GEN / "init.py"),
                "--flavor", f, "--target", str(tgt), "--yes", "--no-validate"])


def _guard_artifact(tgt: Path, f: str) -> Path:
    """flavor별 가드 배선 산출물 경로(부재 단언용). antigravity는 산출물 없음(None)."""
    return {"claude": tgt / ".claude" / "settings.json",
            "codex": tgt / "_shared" / "guard" / "codex_goal_watch.mjs"}.get(f)


def validate_all_pass() -> int:
    fails = 0
    for f in FLAVORS:
        with tempfile.TemporaryDirectory() as d:
            tgt = Path(d) / f"sys-{f}"
            if init(tgt, f).returncode != 0:
                print(f"  FAIL [{f}] init exit nonzero"); fails += 1; continue
            v = run([sys.executable, str(GEN / "validate.py"),
                     "--flavor", f, "--target", str(tgt)])
            ok = v.returncode == 0 and "전부 PASS" in v.stdout
            print(f"  {'PASS' if ok else 'FAIL'} [{f}] validate exit {v.returncode}")
            if not ok:
                print(v.stdout); fails += 1
    return fails


def slim_checks() -> int:
    """기본 생성물에 knot 관리블록·가드 배선 잔재가 없는지 (v3 슬림화 회귀 방지)."""
    fails = 0
    for f in FLAVORS:
        with tempfile.TemporaryDirectory() as d:
            tgt = Path(d) / f"plain-{f}"
            init(tgt, f)
            txt = (tgt / INSTRUCTION_FILE[f]).read_text(encoding="utf-8")
            no_knot = KNOT_START not in txt and KNOT_END not in txt
            print(f"  {'PASS' if no_knot else 'FAIL'} [{f}] 기본 init 관리블록 부재")
            fails += not no_knot
            art = _guard_artifact(tgt, f)
            no_guard = art is None or not art.is_file()
            print(f"  {'PASS' if no_guard else 'FAIL'} [{f}] 기본 init 가드 산출물 부재")
            fails += not no_guard
    return fails


def shallow_path_check() -> int:
    """validate.py가 얕은 경로에서도 모듈 로드되는지 (ZIP 평탄화 배포 회귀 가드).

    ZIP은 generator/ 내용을 루트로 평탄화하므로 SCRIPT_DIR가 `/tmp/xxx/`처럼 얕아진다.
    모듈 상수가 `parents[4]`를 무조건 인덱싱하면 IndexError로 **validate 전체가 죽는다**
    (2026-08-13 CI ubuntu에서 검출 — 로컬 임시경로는 깊어서 안 보였다).
    """
    import importlib.util
    from pathlib import PurePosixPath

    spec = importlib.util.spec_from_file_location("_v", GEN / "validate.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001
        print(f"  FAIL validate.py 모듈 로드 ({type(e).__name__}: {e})")
        return 1
    ok = True
    for depth, n in ((PurePosixPath("/tmp/x"), 4), (PurePosixPath("/"), 2)):
        try:
            mod._ancestor(type(GEN)(str(depth)), n)
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL _ancestor({depth}, {n}) → {type(e).__name__}")
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} 얕은 경로에서 validate 상수 계산 (ZIP 평탄화)")
    return 0 if ok else 1


def main() -> None:
    fails = validate_all_pass() + slim_checks() + shallow_path_check()
    print(f"test_generate: {'all pass' if not fails else f'{fails} fail'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
