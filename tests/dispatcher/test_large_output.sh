#!/usr/bin/env bash
# 큰 워커 출력이 envelope 조립에서 유실되지 않아야 한다.
#
# 실측(2026-08-13, codex-critic 실호출): 최종 envelope를 `jq --argjson e "$env"` 로
# **argv에** 실어 넘기다 OS 인자 길이 한계를 넘어 `jq: Argument list too long` 으로 죽었다.
# 워커는 1분 27초를 정상 수행했는데 결과가 통째로 사라졌다 — 유료 호출이 날아간다.
# 수정: add_flag() 가 herestring(stdin)으로 넘긴다.
. "$(dirname "$0")/_lib.sh"
echo "큰 출력 envelope 유실 방지"

ROOT="$(new_root <<'JSON'
{"schema_version":"1","flavor":"claude","workers":{"g":{
  "call_type":"cli","model":"m","approval_class":"worker","result_capture":"envelope",
  "timeout":60,"brief_mode":"content",
  "cli":{"command":"agy","args_template":["--prompt","@brief_content"]},"fallbacks":[]}}}
JSON
)"
echo "BRIEF" > "$ROOT/brief.txt"
# 약 400KB 출력 — Windows argv 한계(~32KB)를 크게 넘는다
{ echo '#!/usr/bin/env bash'
  echo 'for i in $(seq 1 8000); do echo "line $i: 워커 산출물 본문 텍스트"; done'
  echo 'exit 0'; } > "$ROOT/_shared/bin/agy"
chmod +x "$ROOT/_shared/bin/agy"

OUT="$(MULTIAGENT_ROOT="$ROOT" PATH="$ROOT/_shared/bin:$PATH" bash "$DISPATCHER" g "$ROOT/brief.txt" 2>/dev/null)"; RC=$?

assert_eq       "exit 0"                  0       "$RC"
assert_eq       "status=ok"               "ok"    "$(jq -r '.status'        <<<"$OUT")"
assert_eq       "fallback_used=false"     "false" "$(jq -r '.fallback_used' <<<"$OUT")"
# 마지막 줄은 grep으로 확인한다. `tail -1`은 jq가 붙이는 후행 개행 때문에 빈 줄을 집는다.
BODY="$(jq -r '.stdout' <<<"$OUT")"
assert_contains "출력 첫 줄 보존"    "line 1: "    "$BODY"
assert_contains "출력 마지막 줄 보존" "line 8000: " "$BODY"

# 줄 수로 유실 확인 — 중간이 잘리면 여기서 잡힌다
LINES="$(grep -c '^line ' <<<"$BODY")"
assert_eq "8000줄 전부 보존" 8000 "$LINES"

# 길이도 함께 기록(argv 한계 ~32KB를 크게 넘는지)
LEN="$(jq -r '.stdout | length' <<<"$OUT")"
if [ "$LEN" -gt 150000 ]; then echo "  PASS: stdout 길이 $LEN자 (argv 한계 훨씬 초과분 통과)"; PASS=$((PASS+1))
else echo "  FAIL: stdout 길이 부족 ($LEN자)"; FAIL=$((FAIL+1)); fi

rm -rf "$ROOT"
finish
