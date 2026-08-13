#!/usr/bin/env bash
# @model 치환 — 레코드의 .model이 그대로 인자로 전달되는지.
# 이게 깨지면 envelope의 model 라벨과 실제 호출 모델이 갈라진다(로그에 거짓 기록).
# 실증: agy를 --model 없이 부르면 전역 설정이 이겨, envelope는 pro-high라고 하면서
#       실제로는 Flash가 답했다 (2026-08-13).
. "$(dirname "$0")/_lib.sh"
echo "@model 치환 (envelope 라벨 = 실제 호출 모델)"

ROOT="$(new_root <<'JSON'
{"schema_version":"1","flavor":"claude","workers":{"g":{
  "call_type":"cli","model":"m-pin","approval_class":"worker","result_capture":"envelope",
  "timeout":10,"brief_mode":"content",
  "cli":{"command":"agy","args_template":["--model","@model","--prompt","@brief_content"]}}}}
JSON
)"
echo "BRIEF-TEXT" > "$ROOT/brief.txt"
{ echo '#!/usr/bin/env bash'; echo 'echo "ARGS: $*"'; echo 'exit 0'; } > "$ROOT/_shared/bin/agy"
chmod +x "$ROOT/_shared/bin/agy"

OUT="$(MULTIAGENT_ROOT="$ROOT" PATH="$ROOT/_shared/bin:$PATH" bash "$DISPATCHER" g "$ROOT/brief.txt" 2>/dev/null)"; RC=$?
so="$(jq -r '.stdout' <<<"$OUT")"
lbl="$(jq -r '.model' <<<"$OUT")"

assert_eq       "exit 0"                         0                            "$RC"
assert_contains "인자에 --model <모델> 전달"        "--model m-pin"              "$so"
assert_contains "brief 내용도 함께 전달"           "BRIEF-TEXT"                 "$so"
assert_eq       "envelope 라벨 = 레코드 .model"    "m-pin"                      "$lbl"

rm -rf "$ROOT"
finish
