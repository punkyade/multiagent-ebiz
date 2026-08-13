#!/usr/bin/env bash
# 빈 출력 = 조용한 실패. exit 0 이어도 stdout이 비면 status=empty 로 판정해야 한다.
#
# 실측 2건 모두 exit 0으로 위장했다:
#   2026-07-03  agy가 `-p` 플래그 제거로 프롬프트를 무시 → 온보딩 인사만 반환
#   2026-08-13  agy 헤드리스가 read_file 권한을 자동 거부 → 완전한 빈 출력
# 둘 다 status=ok 로 기록됐고, 오케스트레이터는 성공으로 읽었다.
. "$(dirname "$0")/_lib.sh"
echo "빈 출력 판정 (exit 0 + stdout 없음 → empty)"

ROOT="$(new_root <<'JSON'
{"schema_version":"1","flavor":"claude","workers":{"g":{
  "call_type":"cli","model":"m","approval_class":"worker","result_capture":"envelope",
  "timeout":10,"brief_mode":"content",
  "cli":{"command":"agy","args_template":["--prompt","@brief_content"]},"fallbacks":[]}}}
JSON
)"
echo "BRIEF" > "$ROOT/brief.txt"
# exit 0 이지만 stdout 없음. stderr에만 사유를 남긴다(실제 agy 동작과 동일).
{ echo '#!/usr/bin/env bash'
  echo 'echo "권한 거부로 출력 없음" >&2'
  echo 'exit 0'; } > "$ROOT/_shared/bin/agy"
chmod +x "$ROOT/_shared/bin/agy"

OUT="$(MULTIAGENT_ROOT="$ROOT" PATH="$ROOT/_shared/bin:$PATH" bash "$DISPATCHER" g "$ROOT/brief.txt" 2>/dev/null)"; RC=$?

assert_eq       "status=empty (ok 아님)"        "empty"  "$(jq -r '.status'          <<<"$OUT")"
assert_eq       "exit_code는 자식 실제값 0 유지"  "0"      "$(jq -r '.exit_code'       <<<"$OUT")"
assert_eq       "디스패처 종료코드 비0"           "1"      "$RC"
assert_contains "사유가 stderr에 보존"            "권한 거부" "$(jq -r '.stderr_sanitized' <<<"$OUT")"
assert_eq       "폴백 없음 → fallback_used=false" "false"  "$(jq -r '.fallback_used'   <<<"$OUT")"

# 정상 출력이면 여전히 ok 여야 (회귀 방지)
{ echo '#!/usr/bin/env bash'; echo 'echo real-output'; echo 'exit 0'; } > "$ROOT/_shared/bin/agy"
chmod +x "$ROOT/_shared/bin/agy"
OUT2="$(MULTIAGENT_ROOT="$ROOT" PATH="$ROOT/_shared/bin:$PATH" bash "$DISPATCHER" g "$ROOT/brief.txt" 2>/dev/null)"
assert_eq "정상 출력은 그대로 ok" "ok" "$(jq -r '.status' <<<"$OUT2")"

rm -rf "$ROOT"
finish
