#!/usr/bin/env bash
# call_worker.sh — backends.json 디스패처 (cli/api 전용).
# native/mcp는 오케스트레이터가 직접 호출(디스패처 비경유).
# 사용: call_worker.sh <role> <brief-file> [payload-file]
#   payload-file(선택): brief 한도(1200자)와 별도인 동봉 자료(예: sources/gemini-packet.md).
#   디스패처가 brief 뒤에 결합해 전달 — brief 본문 inline 금지 규칙과 충돌 없이 대용량 자료 전달.
#   미리보기: call_worker.sh --merged-preview <brief-file> <payload-file>  (백엔드 호출 없이 결합 결과 출력)
# 반환: stdout에 result envelope(JSON). exit 0=성공, 비0=실패/거부.
set -euo pipefail

# ── 임시자원 추적 + 강제 정리(die·인터럽트·정상 모두) ──
_TMPS=()
cleanup() { local p; for p in "${_TMPS[@]:-}"; do [ -n "$p" ] && rm -rf -- "$p"; done; return 0; }  # 항상 0: EXIT trap이 종료코드 덮어쓰지 않도록
trap cleanup EXIT INT TERM
mktmp()  { local t; t="$(mktemp)";    _TMPS+=("$t"); printf '%s' "$t"; }
mktmpd() { local t; t="$(mktemp -d)"; _TMPS+=("$t"); printf '%s' "$t"; }

die() { echo "call_worker: $1" >&2; exit "${2:-1}"; }

PREVIEW=0
if [ "${1:-}" = "--merged-preview" ]; then PREVIEW=1; shift; set -- "_preview" "$@"; fi

ROLE="${1:-}"; BRIEF="${2:-}"; PAYLOAD="${3:-}"
[ -n "$ROLE" ] && [ -n "$BRIEF" ] || die "usage: call_worker.sh <role> <brief-file> [payload-file]" 64

SCRIPT_DIR="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${MULTIAGENT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
BACKENDS="$ROOT/_shared/backends.json"

command -v jq >/dev/null 2>&1 || die "jq 필요(JSON 파싱)" 5
[ "$PREVIEW" = 1 ] || [ -f "$BACKENDS" ] || die "backends.json 없음: $BACKENDS" 5

# timeout: coreutils timeout/gtimeout 우선, 없으면 portable bash 폴백(둘 다 유한 보장)
TIMEOUT_BIN=""
command -v timeout  >/dev/null 2>&1 && TIMEOUT_BIN=timeout
[ -z "$TIMEOUT_BIN" ] && command -v gtimeout >/dev/null 2>&1 && TIMEOUT_BIN=gtimeout
run_limited() {  # run_limited <secs> -- <cmd...>
  local t="$1"; shift; [ "$1" = "--" ] && shift
  if [ -n "$TIMEOUT_BIN" ]; then "$TIMEOUT_BIN" -k 5 "$t" "$@"; return $?; fi
  # 폴백: python3 러너(결정적, 프로세스그룹 TERM→KILL). python3은 시스템 필수 의존성.
  command -v python3 >/dev/null 2>&1 || die "timeout 유틸 또는 python3 필요" 5
  python3 "$SCRIPT_DIR/_run.py" "$t" "$@"; return $?
}

# brief 절대경로화 + 검증 ('--'로 옵션 하이재킹 방어)
case "$BRIEF" in *..*) die "brief 경로에 '..' 금지" 6;; esac
[ -f "$BRIEF" ] || die "brief 파일 없음: $BRIEF" 6
BRIEF="$(cd "$(dirname -- "$BRIEF")" && pwd)/$(basename -- "$BRIEF")"

# payload(선택) — brief 한도 밖 동봉 자료. brief 뒤에 결합한 임시 brief로 치환.
if [ -n "$PAYLOAD" ]; then
  case "$PAYLOAD" in *..*) die "payload 경로에 '..' 금지" 6;; esac
  [ -f "$PAYLOAD" ] || die "payload 파일 없음: $PAYLOAD" 6
  MERGED="$(mktmp)"
  { cat -- "$BRIEF"
    printf '\n\n---\n\n# 동봉 자료 (payload — orchestrator가 결합. 이 자료만 사용하고 파일 열지 말 것)\n\n'
    cat -- "$PAYLOAD"
  } >"$MERGED"
  BRIEF="$MERGED"
fi
if [ "$PREVIEW" = 1 ]; then cat -- "$BRIEF"; exit 0; fi

rec="$(jq -c --arg r "$ROLE" '.workers[$r] // empty' "$BACKENDS")"
[ -n "$rec" ] || die "role 미정의: $ROLE" 2

# 폴백 가용성 사전 점검(경고만): primary가 죽고 나서야 폴백 불가를 아는 것을 방지
# CR 제거: 윈도우 네이티브 jq는 stdout을 텍스트 모드로 써 CRLF를 뱉는다. $()는 끝의 CR만
# 지우므로 줄 단위로 읽는 지점에선 매 줄 직접 떼어내야 값이 오염되지 않는다(이하 동일).
while IFS= read -r _fe; do
  _fe="${_fe%$'\r'}"
  [ -n "$_fe" ] && [ -z "${!_fe:-}" ] && \
    echo "call_worker: 경고 — 폴백 필수 env 미설정: $_fe (primary 실패 시 폴백 불가)" >&2
done < <(jq -r '.fallbacks[]?.api.required_env[]? // empty' <<<"$rec")

redact() { sed -E 's/[A-Za-z0-9_-]{32,}/[REDACTED]/g'; }

# 단일 backend 실행 → envelope(JSON)을 stdout, exit code 반환
run_backend() {
  local spec="$1" ctype bmode tmo cwdp model wd out err errd rc start dur
  ctype="$(jq -r '.call_type' <<<"$spec")"
  model="$(jq -r '.model // "?"' <<<"$spec")"
  case "$ctype" in
    native|mcp) die "native/mcp는 오케스트레이터 직접 호출(디스패처 비경유)" 3 ;;
    cli|api) ;;
    *) die "잘못된 call_type: $ctype" 7 ;;
  esac
  bmode="$(jq -r '.brief_mode // "content"' <<<"$spec")"
  tmo="$(jq -r '.timeout // 300' <<<"$spec")"
  cwdp="$(jq -r '.cwd_policy // "repo_root"' <<<"$spec")"

  case "$cwdp" in
    isolated_tmp) wd="$(mktmpd)";;
    target)       wd="${TARGET_REPO:-$ROOT}";;
    *)            wd="$ROOT";;
  esac

  local -a cmd=()
  if [ "$ctype" = "cli" ]; then
    local command_bin args_json a
    command_bin="$(jq -r '.cli.command' <<<"$spec")"
    case "$command_bin" in agy|codex|claude) ;; *) die "command allowlist 위반: $command_bin" 7;; esac
    cmd+=("$command_bin")
    args_json="$(jq -r '.cli.args_template[]' <<<"$spec")"   # jq 실패 시 set -e 트리거
    while IFS= read -r a; do
      a="${a%$'\r'}"   # jq CRLF 제거(위 참조) — 없으면 "exec\r" 같은 인자로 호출 자체가 실패
      case "$a" in
        "@brief")         cmd+=("$BRIEF");;
        "@brief_content") cmd+=("$(cat -- "$BRIEF")");;
        # @model: 레코드의 .model을 그대로 인자로. 모델명을 args_template에 또 적으면
        # envelope의 model 라벨과 실제 호출 모델이 갈라진다(거짓 기록) — 정본은 .model 하나.
        "@model")         cmd+=("$model");;
        *)                cmd+=("$a");;
      esac
    done <<<"$args_json"
    # codex 워커: 기본은 git 요구(안전망). git 없으면 명확히 실패. 옵트아웃 시에만 우회.
    if [ "$command_bin" = "codex" ]; then
      if [ "${MULTIAGENT_CODEX_SKIP_GIT:-0}" = "1" ]; then
        local -a _nc=(); local _ins=0 _x
        for _x in "${cmd[@]}"; do
          _nc+=("$_x")
          if [ "$_ins" = 0 ] && [ "$_x" = "exec" ]; then _nc+=("--skip-git-repo-check"); _ins=1; fi
        done
        cmd=("${_nc[@]}")
      elif ! command -v git >/dev/null 2>&1; then
        die "codex 워커는 git이 필요합니다. git 설치 후 재시도하거나, 위험을 감수하면 MULTIAGENT_CODEX_SKIP_GIT=1 로 우회하세요." 8
      fi
    fi
  else
    local ref reqenv brief_pass
    ref="$(jq -r '.api.ref' <<<"$spec")"
    case "$ref" in adapters/*) ;; *) die "api.ref는 adapters/ 내부만" 7;; esac
    case "$ref" in *..*) die "api.ref에 '..' 금지" 7;; esac
    [ -f "$ROOT/_shared/$ref" ] || die "api 스크립트 없음: $ref" 4
    while IFS= read -r reqenv; do
      reqenv="${reqenv%$'\r'}"   # jq CRLF 제거(위 참조) — env명 오염 시 간접확장이 깨진다
      [ -n "$reqenv" ] || continue
      if [ -z "${!reqenv:-}" ]; then
        # die 대신 에러 envelope 반환: 폴백 체인에서 실패 사유가 최종 envelope에 남도록
        jq -n --arg model "$model" --arg e "$reqenv" \
          '{status:"error", exit_code:4, backend:"api", model:$model,
            duration_s:0, stdout:"", stderr_sanitized:("필수 env 없음: " + $e + " — 폴백 사용 불가")}'
        return 4
      fi
    done < <(jq -r '.api.required_env[]? // empty' <<<"$spec")
    brief_pass="$(jq -r '.api.brief_pass // "arg1"' <<<"$spec")"
    cmd+=("bash" "$ROOT/_shared/$ref")
    [ "$brief_pass" = "arg1" ] && cmd+=("$BRIEF")
    [ "$brief_pass" = "stdin" ] && bmode="stdin"
  fi

  out="$(mktmp)"; err="$(mktmp)"; errd="$(mktmp)"
  start=$(date +%s)
  rc=0
  (
    cd "$wd" || exit 70
    export CI=1 DEBIAN_FRONTEND=noninteractive
    if [ "$bmode" = "stdin" ]; then
      run_limited "$tmo" -- "${cmd[@]}" <"$BRIEF"
    else
      run_limited "$tmo" -- "${cmd[@]}" </dev/null
    fi
  ) >"$out" 2>"$err" || rc=$?
  dur=$(( $(date +%s) - start ))

  local status="ok"
  [ "$rc" -ne 0 ] && status="error"
  [ "$rc" -eq 124 ] && status="timeout"
  # exit 0인데 stdout이 비었으면 성공이 아니다. 외부 CLI가 권한 거부·플래그 미인식 등으로
  # 조용히 아무것도 안 한 경우가 정확히 여기 걸린다 — 실측 2건 모두 exit 0으로 위장했다:
  #   2026-07-03 agy가 `-p` 제거로 프롬프트를 무시(온보딩 인사만 반환)
  #   2026-08-13 agy 헤드리스가 read_file 권한을 자동 거부(빈 출력)
  # 사유는 stderr_sanitized에 남으므로 그것과 함께 읽는다.
  [ "$status" = "ok" ] && [ ! -s "$out" ] && status="empty"

  redact <"$err" >"$errd"
  jq -n --arg status "$status" --argjson exit "$rc" \
        --rawfile stdout "$out" --rawfile stderr "$errd" \
        --argjson dur "$dur" --arg backend "$ctype" --arg model "$model" \
        '{status:$status, exit_code:$exit, backend:$backend, model:$model,
          duration_s:$dur, stdout:$stdout, stderr_sanitized:$stderr}'
  # empty도 실패로 취급해 폴백 체인이 돌게 한다. envelope의 exit_code는 자식의 실제
  # 종료코드를 그대로 유지하고(진단 정보), 판정은 status로 한다.
  [ "$status" = "empty" ] && return 65
  return "$rc"
}

# primary → 실패 시 fallbacks 순차 (set -e 우회: || prc=$?)
prc=0; env_primary="$(run_backend "$rec")" || prc=$?
if [ "$prc" -eq 0 ]; then
  jq -n --argjson e "$env_primary" '$e + {fallback_used:false}'
  exit 0
fi
nf="$(jq '.fallbacks | length' <<<"$rec")"
env_fb=""; i=0
while [ "$i" -lt "${nf:-0}" ]; do
  fb="$(jq -c --argjson i "$i" '.fallbacks[$i]' <<<"$rec")"
  frc=0; env_fb="$(run_backend "$fb")" || frc=$?
  if [ "$frc" -eq 0 ]; then
    jq -n --argjson e "$env_fb" '$e + {fallback_used:true}'
    exit 0
  fi
  i=$((i+1))
done
# 폴백이 실제로 실행돼 envelope를 남겼을 때만 true. fallbacks:[] 인 워커(예: gemini)의
# primary 실패를 "폴백 사용함"으로 잘못 보고하지 않도록 한다.
if [ -n "$env_fb" ]; then
  jq -n --argjson e "$env_fb"      '$e + {fallback_used:true}'
else
  jq -n --argjson e "$env_primary" '$e + {fallback_used:false}'
fi
exit 1
