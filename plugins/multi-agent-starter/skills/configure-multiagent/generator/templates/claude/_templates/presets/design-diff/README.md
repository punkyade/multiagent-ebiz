# 프리셋: design-diff — 시안 ↔ 구현 대조

디자인 · 퍼블 · QA 3개 직군이 공유하는 **"눈으로 보고 비교하는 일"** 을 고정 파이프라인으로.
사람이 가장 많이 반복하고 가장 자주 놓치는 구간이다.

```
[computer-use] 구현 화면 캡처  →  [multimodal] 시안과 대조  →  [engineer] 수정
```

## 사용

```bash
python3 _shared/new-task.py <작업명> --preset design-diff
```

슬롯 → 워커 배정은 `_shared/capability-profile.md`가 정본이라 flavor마다 자동으로 달라진다.
셀에 워커명이 없으면(예: antigravity의 `multimodal`) **오케스트레이터가 직접 수행**하므로
그 brief는 만들지 않고 안내만 한다.

## 만들어진 뒤 채워야 하는 것

각 brief의 `<...>` 자리표시자다. 이걸 안 채우면 워커가 대상을 못 찾는다:

| 파일 | 채울 것 |
|------|---------|
| `computer-use/brief.md` | 대상 URL·로컬 경로, 뷰포트 폭, 캡처할 화면 목록 |
| `multimodal/brief.md` | **시안 이미지 절대경로**, **캡처 이미지 절대경로** |
| `engineer/brief.md` | `target_repo`, `write_scope`, 수정 대상 파일 |

## 슬롯별 주의

- **`[multimodal]`(gemini)**: 이미지는 **brief 본문에 절대경로를 직접 적는다.**
  `--add-dir`·`--dangerously-skip-permissions` 금지(stdin hang·classifier 차단).
  디렉토리를 가리키거나 다중 파일 순회를 시키면 300s 타임아웃으로 전멸한다 — 경로는 콕 집어서.
- **`[computer-use]`**: 캡처물은 `tasks/<작업>/artifacts/` 에 남긴다. 절대경로를 log에 기록해야
  다음 단계가 그 경로를 brief에 적을 수 있다.
- **`[engineer]`**: 외부 repo 수정이면 4조건(`target_repo`·`write_scope`·승인·`[APPROVAL]` 기록)
  을 모두 채운다. `python3 _shared/audit-approvals.py tasks/<작업>` 이 사후 검사한다.

## 검증

```bash
python3 _shared/check-limits.py tasks/<작업>      # brief 한도
python3 _shared/audit-approvals.py tasks/<작업>   # 승인 게이트
```

## 선결 조건 — agy 파일 읽기 권한 (필독)

**이 설정 없이는 `[multimodal]` 단계가 빈 결과로 끝난다.** agy 1.1.12 헤드리스는
`read_file` 권한을 자동 거부한다. `~/.gemini/antigravity-cli/settings.json`에 추가:

```json
{ "permissions": { "allow": ["read_file(*)"] } }
```

**`~/.gemini/settings.json`이 아니다** — 두 파일이 다 존재해서 헷갈린다.
`python3 _shared/doctor.py` 의 D7이 검사하고, 미설정이면 붙여넣을 JSON을 알려준다.

## 실측 (2026-08-13)

- 이미지 **2장 동시 전달 정상** — 22s, exit 0, 두 스크린샷을 각각 정확히 판별
- 권한 미설정 시: `exit 0` + 빈 출력(= 조용한 실패). 디스패처가 `status: empty` 로 잡아
  성공으로 오인되지는 않는다
