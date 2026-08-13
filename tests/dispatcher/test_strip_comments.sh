#!/usr/bin/env bash
# brief의 HTML 주석은 워커에게 전달되지 않아야 한다.
#
# 근거: 주석은 "템플릿을 어떻게 채우는가" 안내이지 워커 지시가 아니다. 떼고 보내야
# check-limits(주석 제외 측정)가 **실제 전달량과 일치**한다. 그 전에는 안내문을 주석으로
# 옮기는 것이 "측정상 절감"에 불과했다(codex-critic 지적, 2026-08-13).
# payload(동봉 자료)는 원본이므로 그대로 전달한다.
. "$(dirname "$0")/_lib.sh"
echo "brief 주석 제거 (워커 입력 = 측정 대상 일치)"

ROOT="$(new_root <<'JSON'
{"schema_version":"1","flavor":"claude","workers":{"g":{
  "call_type":"cli","model":"m","approval_class":"worker","result_capture":"envelope",
  "timeout":20,"brief_mode":"content",
  "cli":{"command":"agy","args_template":["--prompt","@brief_content"]},"fallbacks":[]}}}
JSON
)"
cat > "$ROOT/brief.txt" <<'MD'
# Brief — r / t

<!-- 한줄주석은사라져야함 -->

## Objective

목적본문은남아야함

<!-- 여러줄주석
     이어지는줄도사라져야함
     끝 -->

본문2 <!-- 인라인주석 --> 뒤
MD
cat > "$ROOT/packet.md" <<'MD'
동봉자료본문
<!-- 페이로드주석은보존 -->
MD
# 받은 프롬프트를 그대로 출력하는 가짜 백엔드
{ echo '#!/usr/bin/env bash'; echo 'shift; printf "%s" "$1"'; } > "$ROOT/_shared/bin/agy"
chmod +x "$ROOT/_shared/bin/agy"

OUT="$(MULTIAGENT_ROOT="$ROOT" PATH="$ROOT/_shared/bin:$PATH" \
       bash "$DISPATCHER" g "$ROOT/brief.txt" "$ROOT/packet.md" 2>/dev/null)"
SENT="$(jq -r '.stdout' <<<"$OUT")"

case "$SENT" in *한줄주석은사라져야함*)  echo "  FAIL: 한 줄 주석이 전달됨";      FAIL=$((FAIL+1));;
                *) echo "  PASS: 한 줄 주석 제거";        PASS=$((PASS+1));; esac
case "$SENT" in *이어지는줄도사라져야함*) echo "  FAIL: 여러 줄 주석이 전달됨";    FAIL=$((FAIL+1));;
                *) echo "  PASS: 여러 줄 주석 제거";      PASS=$((PASS+1));; esac
case "$SENT" in *인라인주석*)            echo "  FAIL: 인라인 주석이 전달됨";    FAIL=$((FAIL+1));;
                *) echo "  PASS: 인라인 주석 제거";       PASS=$((PASS+1));; esac

assert_contains "본문 보존"            "목적본문은남아야함" "$SENT"
assert_contains "인라인 주변 본문 보존" "본문2"             "$SENT"
assert_contains "payload 본문 동봉"    "동봉자료본문"       "$SENT"
assert_contains "payload 주석은 보존"  "페이로드주석은보존" "$SENT"

# 원본 brief 파일은 건드리지 않는다
assert_contains "원본 brief 파일 무변경" "한줄주석은사라져야함" "$(cat "$ROOT/brief.txt")"

rm -rf "$ROOT"
finish
