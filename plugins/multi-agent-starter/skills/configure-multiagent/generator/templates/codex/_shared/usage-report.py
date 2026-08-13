#!/usr/bin/env python3
"""워커 호출 사용량 리포트 — 누가·무엇을·얼마나 썼는지.

디스패처가 호출마다 `_local/calls.jsonl` 에 1줄씩 남긴다(model·backend·duration·status·
exit_code). 이 스크립트는 그걸 집계한다.

**비용만 보는 도구가 아니다.** 실패·빈출력·폴백 비율이 함께 보이므로 품질 회귀가 집계에서
먼저 드러난다 — 개별 호출을 눈으로 봐야 잡히던 결함들(모델 라벨 거짓, 권한 거부로 인한 빈
출력, 폴백 유실)이 여기서는 비율 변화로 보인다.

**한계(정직하게)**: `claude-main`은 native 호출이라 디스패처를 거치지 않아 원장에 안 잡힌다.
그래서 `tasks/*/log.md` 의 `[WORKER_CALL]` 태그도 함께 세어 **디스패처 미경유 호출 수**를
따로 보고한다. 두 숫자의 차이가 곧 원장의 사각지대다.

사용:
    python3 _shared/usage-report.py              # 전체 기간
    python3 _shared/usage-report.py --days 7     # 최근 7일
    python3 _shared/usage-report.py --failures   # 실패 건 상세

종료코드: 0=정상(집계 결과와 무관), 2=원장 없음.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

WORKER_CALL = re.compile(r"^\s*\[[^\]]+\]\s*\[WORKER_CALL\]", re.M)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
OK_STATUS = "ok"


def load_ledger(root: Path, days: int | None) -> tuple[list[dict], int]:
    """→ (기간 내 레코드, 깨진 줄 수). 깨진 줄은 버리되 개수는 보고한다."""
    path = root / "_local" / "calls.jsonl"
    if not path.is_file():
        return [], 0
    cutoff = None
    if days:
        cutoff = (dt.datetime.now() - dt.timedelta(days=days)).isoformat(timespec="seconds")
    rows, bad = [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        if cutoff and str(r.get("ts", "")) < cutoff:
            continue
        rows.append(r)
    return rows, bad


def count_log_calls(root: Path) -> int:
    """tasks/*/log.md 의 [WORKER_CALL] 총합 (주석 예시 블록 제외)."""
    tasks = root / "tasks"
    if not tasks.is_dir():
        return 0
    total = 0
    for log in tasks.glob("*/log.md"):
        try:
            text = HTML_COMMENT.sub("", log.read_text(encoding="utf-8"))
        except OSError:
            continue
        total += len(WORKER_CALL.findall(text))
    return total


def fmt_dur(sec: float) -> str:
    if sec < 60:
        return f"{sec:.0f}초"
    if sec < 3600:
        return f"{sec/60:.1f}분"
    return f"{sec/3600:.1f}시간"


def table(title: str, key: str, rows: list[dict]) -> None:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[str(r.get(key, "-"))].append(r)
    if not groups:
        return
    print(f"\n  {title}")
    print(f"    {'':<16}{'호출':>5}{'성공':>5}{'실패':>5}{'빈출력':>7}{'총시간':>9}{'평균':>8}")
    for name, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        ok = sum(1 for r in rs if r.get("status") == OK_STATUS)
        empty = sum(1 for r in rs if r.get("status") == "empty")
        fail = len(rs) - ok
        tot = sum(float(r.get("duration_s") or 0) for r in rs)
        print(f"    {name[:15]:<16}{len(rs):>5}{ok:>5}{fail:>5}{empty:>7}"
              f"{fmt_dur(tot):>9}{fmt_dur(tot/len(rs)):>8}")


def main() -> int:
    ap = argparse.ArgumentParser(description="워커 호출 사용량 리포트")
    ap.add_argument("--days", type=int, help="최근 N일만 집계")
    ap.add_argument("--failures", action="store_true", help="실패 건 상세 출력")
    args = ap.parse_args()

    root = Path(os.environ.get("MULTIAGENT_ROOT")
                or Path(__file__).resolve().parent.parent)
    rows, bad = load_ledger(root, args.days)
    if not (root / "_local" / "calls.jsonl").is_file():
        print("원장이 없습니다 — 디스패처(cli/api) 워커를 아직 호출하지 않았거나,"
              " 이 폴더가 시스템 루트가 아닙니다.", file=sys.stderr)
        print(f"  기대 경로: {root / '_local' / 'calls.jsonl'}", file=sys.stderr)
        return 2

    period = f"최근 {args.days}일" if args.days else "전체 기간"
    print(f"워커 호출 리포트 — {period}  (원장: _local/calls.jsonl)")
    if not rows:
        print("  해당 기간에 기록된 호출이 없습니다.")
        return 0

    ok = sum(1 for r in rows if r.get("status") == OK_STATUS)
    empty = sum(1 for r in rows if r.get("status") == "empty")
    timeout = sum(1 for r in rows if r.get("status") == "timeout")
    tot = sum(float(r.get("duration_s") or 0) for r in rows)
    print(f"  총 {len(rows)}회 · 성공 {ok} · 실패 {len(rows)-ok}"
          f"(빈출력 {empty} · 타임아웃 {timeout}) · 총 {fmt_dur(tot)}")
    if bad:
        print(f"  ⚠ 원장에 깨진 줄 {bad}개 (건너뜀)")

    table("워커별", "role", rows)
    table("모델별", "model", rows)

    # 디스패처 미경유(native·mcp) 호출 — 원장의 사각지대를 정직하게 드러낸다
    logged = count_log_calls(root)
    if logged:
        gap = logged - len(rows)
        note = f" → 디스패처 미경유 약 {gap}회(native·mcp)" if gap > 0 else ""
        print(f"\n  log.md 기준 총 워커 호출: {logged}회{note}")
        print("    (claude-main 등 native 워커는 디스패처를 거치지 않아 원장에 안 남는다)")

    fails = [r for r in rows if r.get("status") != OK_STATUS]
    if fails and args.failures:
        print(f"\n  실패 상세 ({len(fails)}건)")
        for r in fails[-20:]:
            print(f"    {r.get('ts','?')}  {r.get('role','?'):<14}"
                  f"{r.get('status','?'):<8} exit={r.get('exit_code','?')}"
                  f"  {r.get('task','-')}")
    elif fails:
        print(f"\n  실패 {len(fails)}건 — 상세는 --failures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
