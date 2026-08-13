#!/usr/bin/env python3
"""MultiAgent 시스템 생성기 — 결정적(deterministic) 스캐폴더.

flavor 템플릿(claude | codex | antigravity)을 대상 폴더에 복사한다.
- 결정적: 번들된 템플릿 파일을 그대로 복사. LLM 자유작문 없음 → 불변식 보장.
- 안전: 기존 tasks/·_local/ 사용자 데이터를 절대 지우지 않음(update 모드 보존).
  지침파일(CLAUDE.md/AGENTS.md)은 덮어쓰기 전 .multiagent-bak 백업 + loadout store 블록 재부착.
- 호스트 독립: 순수 파이썬. plugin/skill/ZIP은 이 스크립트를 부르는 얇은 front door일 뿐.

사용:
    python3 init.py                         # 대화형(메뉴)
    python3 init.py --flavor codex --target ~/work/my-system --yes
    python3 init.py --flavor claude --target . --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 로케일이 UTF-8이 아닌 환경(예: 한국어 Windows cp949)에서 한글·em dash 출력이
# UnicodeEncodeError로 죽지 않도록 표준 출력 인코딩을 고정한다.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):  # 비-TextIO로 리다이렉트된 경우
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
FLAVORS = ("claude", "codex", "antigravity")
# 사용자 데이터 디렉토리 — 내용물은 절대 덮어쓰거나 지우지 않는다(.gitkeep만 보장).
PRESERVE_DIRS = ("tasks", "_local")

# 프로젝트 소유 파일 — **대상에 이미 있으면 덮지 않는다.**
# 이 시스템은 보통 기존 프로젝트 폴더에 얹어 쓰는데, 템플릿에 같은 이름의 파일이 있다는
# 이유로 프로젝트의 README·.gitignore를 조용히 갈아엎으면 안 된다. 실제 사고 2건:
#   ssaksseuri  — 프로젝트 CLAUDE.md 유실(git 아님 → .multiagent-bak 하나가 유일한 사본)
#   Pipleline   — README.md 교체 + .gitignore 삭제로 빌드 산출물이 git에 노출
# 이 파일들은 생성 시스템 동작에 필수가 아니다(validate C1 필수 목록에 없다).
PROJECT_OWNED = ("README.md", ".gitignore", "LICENSE", "NOTICE",
                 "CHANGELOG.md", "KNOWN_ISSUES.md")
# 병합 대상 — 덮어쓰면 프로젝트가 쓰던 MCP 서버가 사라진다.
MCP_FILE = ".mcp.json"

# flavor별 지침파일(에이전트가 자동 로드) — validate.py FLAVOR['instruction']과 일치해야.
INSTRUCTION_FILE = {"claude": "CLAUDE.md", "codex": "AGENTS.md", "antigravity": "AGENTS.md"}
# loadout store(github.com/netwaif/loadout)가 지침파일에 심는 조각 블록 — update 시 보존 대상.
STORE_BLOCK_RE = re.compile(r"<!-- store:([\w-]+):start -->.*?<!-- store:\1:end -->", re.S)
# knot·요금가드 설치는 v3.0.0부터 loadout 카탈로그 담당(github.com/netwaif/loadout).
# knot 자산(knot_block.md·knot-vault/)과 validate C10(사후 검증)은 존치. knot 능동 스킬은 v3.1.0부터 netwaif/knot 자체 플러그인이 배포.
# 요금가드는 v3.2.0부터 자산(구 guard/)·사후검증(구 C12)까지 전부 loadout guard 품목 소관 — 이 저장소에 가드 파일 없음.


def available_flavors() -> list[str]:
    return [f for f in FLAVORS if (TEMPLATES_DIR / f).is_dir()]


def choose_flavor(arg: str | None, flavors: list[str]) -> str:
    if arg:
        if arg not in flavors:
            sys.exit(f"[error] unknown flavor '{arg}'. available: {', '.join(flavors)}")
        return arg
    print("어떤 멀티에이전트 시스템을 구성할까요?")
    for i, f in enumerate(flavors, 1):
        print(f"  {i}. {f}")
    while True:
        sel = input("선택 [번호]: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(flavors):
            return flavors[int(sel) - 1]
        print("  잘못된 선택")


def choose_target(arg: str | None, flavor: str) -> Path:
    if arg:
        return Path(arg).expanduser().resolve()
    default = str(Path.cwd() / f"multi-agent-{flavor}")
    raw = input(f"설치할 폴더 [{default}]: ").strip() or default
    return Path(raw).expanduser().resolve()


def guard_target(target: Path, template_dir: Path) -> None:
    """installer 자기 자신/템플릿 트리 안에 설치하는 사고 방지."""
    bad = [SCRIPT_DIR, template_dir]
    for b in bad:
        if target == b or b in target.parents or target in b.parents:
            sys.exit(f"[error] installer/template 트리 안에는 설치할 수 없습니다: {target}")


def is_user_data(rel: Path) -> bool:
    """tasks/ · _local/ 하위의 .gitkeep 외 파일 = 사용자 데이터(건드리지 않음)."""
    return len(rel.parts) >= 1 and rel.parts[0] in PRESERVE_DIRS and rel.name != ".gitkeep"


def copy_template(template_dir: Path, target: Path,
                  dry: bool) -> tuple[list[Path], list[Path]]:
    """템플릿 파일을 target에 복사 → (written, skipped).

    target-only 파일(사용자 tasks/ 작업물)은 삭제하지 않으므로 update 모드에서 자동 보존된다.
    PROJECT_OWNED는 **이미 있으면 건너뛴다** — 기존 프로젝트 폴더에 얹을 때 그 프로젝트의
    README·.gitignore를 갈아엎지 않기 위해서다. MCP 설정은 병합으로 따로 처리한다.
    """
    written: list[Path] = []
    skipped: list[Path] = []
    for src in sorted(template_dir.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(template_dir)
        if is_user_data(rel):  # 방어적: 템플릿엔 .gitkeep만 있어 보통 도달 안 함
            continue
        dest = target / rel
        rel_posix = rel.as_posix()
        if rel_posix == MCP_FILE:
            merge_mcp(src, dest, dry)
            written.append(rel)
            continue
        if rel_posix in PROJECT_OWNED and dest.exists():
            skipped.append(rel)
            continue
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        written.append(rel)
    return written, skipped


def merge_mcp(src: Path, dest: Path, dry: bool) -> None:
    """`.mcp.json` 병합 — 프로젝트가 쓰던 mcpServers를 남기고 템플릿 서버만 더한다.

    통째로 덮으면 그 프로젝트의 MCP 서버 설정이 사라진다. 같은 키가 이미 있으면
    프로젝트 값을 존중한다(우리 것으로 갈아치우지 않는다).
    """
    if dry:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tpl = json.loads(src.read_text(encoding="utf-8"))
    if not dest.exists():
        dest.write_text(json.dumps(tpl, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
        return
    try:
        cur = json.loads(dest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # 읽을 수 없으면 손대지 않는다 — 판단 불가 상태에서 덮는 것이 더 나쁘다
        print(f"  [warn] {MCP_FILE} 를 읽을 수 없어 병합을 건너뜁니다 (원본 유지)")
        return
    servers = cur.setdefault("mcpServers", {})
    added = []
    for name, spec in (tpl.get("mcpServers") or {}).items():
        if name not in servers:
            servers[name] = spec
            added.append(name)
    if added:
        dest.write_text(json.dumps(cur, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")


def preserve_instruction(target: Path, flavor: str, old_text: str | None, dry: bool) -> int:
    """update 모드에서 기존 지침파일 보호: 덮어쓰기 전 원문을 .multiagent-bak으로 백업하고,
    loadout store 블록을 새 지침파일 끝에 재부착한다. 반환값 = 재부착한 블록 수."""
    if old_text is None:
        return 0
    instr = target / INSTRUCTION_FILE[flavor]
    if not dry:
        (target / (INSTRUCTION_FILE[flavor] + ".multiagent-bak")).write_text(
            old_text, encoding="utf-8")
    new_text = instr.read_text(encoding="utf-8") if instr.is_file() else ""
    blocks = [m.group(0) for m in STORE_BLOCK_RE.finditer(old_text)
              if m.group(0) not in new_text]
    if blocks and not dry:
        instr.write_text(new_text.rstrip("\n") + "\n\n" + "\n\n".join(blocks) + "\n",
                         encoding="utf-8")
    return len(blocks)


def main() -> None:
    ap = argparse.ArgumentParser(description="MultiAgent 시스템 생성기 (결정적 스캐폴더)")
    ap.add_argument("--flavor", choices=FLAVORS, help="claude | codex | antigravity (생략 시 메뉴)")
    ap.add_argument("--target", help="설치 대상 폴더 (생략 시 질문)")
    ap.add_argument("--yes", action="store_true", help="확인 프롬프트 생략")
    ap.add_argument("--no-validate", action="store_true", help="설치 후 validate 건너뜀")
    ap.add_argument("--dry-run", action="store_true", help="실제 쓰지 않고 미리보기")
    args = ap.parse_args()

    flavors = available_flavors()
    if not flavors:
        sys.exit(f"[error] 템플릿이 없습니다: {TEMPLATES_DIR}")

    flavor = choose_flavor(args.flavor, flavors)
    template_dir = TEMPLATES_DIR / flavor
    target = choose_target(args.target, flavor)
    guard_target(target, template_dir)

    mode = "update" if (target.exists() and any(target.iterdir())) else "init"
    print()
    print(f"  flavor : {flavor}")
    print(f"  target : {target}")
    print(f"  mode   : {mode}  (update=시스템 파일만 갱신, tasks/·_local/ 보존, "
          f"지침파일은 백업 후 store 블록 재부착)")
    if args.dry_run:
        print("  [dry-run] 실제 변경 없음")

    if not args.yes and not args.dry_run:
        if input("\n진행할까요? [y/N]: ").strip().lower() not in ("y", "yes"):
            sys.exit("취소됨")

    instr_path = target / INSTRUCTION_FILE[flavor]
    old_instr = instr_path.read_text(encoding="utf-8") if instr_path.is_file() else None

    written, skipped = copy_template(template_dir, target, dry=args.dry_run)
    prefix = "(dry) " if args.dry_run else ""
    print(f"\n  {prefix}{len(written)}개 파일 {'복사 예정' if args.dry_run else '복사 완료'}.")
    if skipped:
        print(f"  {prefix}기존 파일 {len(skipped)}개는 건드리지 않음(프로젝트 소유): "
              f"{', '.join(p.as_posix() for p in skipped)}")

    kept = preserve_instruction(target, flavor, old_instr, dry=args.dry_run)
    if old_instr is not None:
        print(f"  {prefix}기존 {INSTRUCTION_FILE[flavor]} 백업: "
              f"{INSTRUCTION_FILE[flavor]}.multiagent-bak (store 블록 {kept}개 재부착)")

    validate = SCRIPT_DIR / "validate.py"
    if not args.no_validate and not args.dry_run and validate.exists():
        print("\n  validate.py 실행...")
        rc = subprocess.run(
            [sys.executable, str(validate), "--flavor", flavor, "--target", str(target)]
        ).returncode
        if rc != 0:
            sys.exit(f"[warn] validate가 문제를 보고했습니다 (exit {rc})")

    print(f"\n  완료. 다음: cd {target} 후 해당 도구({flavor}) 실행.")


if __name__ == "__main__":
    main()
