# 온보딩 스모크 작업 — 신규 팀원 1회용 (ebiz 추가)

새 팀원이 시스템을 만든 직후, **각 워커를 최소 비용으로 한 번씩 호출해 체인 전체가
도는지** 확인하는 절차다. 실패는 대개 여기서 다 드러나고, 실제 업무 중에 터지는 것보다
훨씬 싸다.

> 순서: `doctor.py`(무료·필수) → 스모크 작업(유료·승인 필요).
> doctor가 FAIL이면 스모크로 넘어가지 말 것 — 원인이 도구 부재로 이미 밝혀진 상태다.

## 0단계 — 환경 진단 (무료)

```bash
python3 _shared/doctor.py
```

`핵심 이상 없음`이 나와야 다음으로 간다. WARN은 해당 워커만 못 쓰는 것이므로,
그 워커는 아래 스모크에서 빼면 된다.

## 1단계 — 작업 폴더 만들기

`tasks/smoke/` 를 만들고 `_templates/task.md`·`log.md`·`context.md`를 복사한다.
`task.md`의 `## Worker Plan` 을 아래로 채운다 — **승인은 사용자가 직접 확인한 뒤 적는다**
(`workers_approved`가 비어 있으면 호출 금지가 규칙이다).

```yaml
workers_approved:
  - worker: <역할명>
    approved_at: <YYYY-MM-DD>
    purpose: 온보딩 스모크 — 응답 가능 여부만 확인
    approved_by: user

planned_workers: []
```

역할명은 flavor마다 다르다. 정본은 `_shared/backends.json`의 `workers` 키다:

```bash
python3 -c "import json;print(list(json.load(open('_shared/backends.json',encoding='utf-8'))['workers']))"
```

## 2단계 — 워커별 최소 brief

`tasks/smoke/workers/<역할>/brief.md`. **최소 토큰**이 목적이므로 짧게 유지한다.
고정 규약 블록은 `_templates/worker-brief.md`에서 그대로 가져온다.

| 슬롯 | 스모크 지시 | 성공 판정 |
|------|------------|----------|
| `[strategist]` | "이 문장을 그대로 반향하고, 한 줄로 자기 역할을 설명하라." | 반향 정확 + 역할 서술 |
| `[engineer]` | "`tasks/smoke/artifacts/ok.txt` 에 `ok` 한 줄을 쓰라." | 파일 생성됨 |
| `[computer-use]` | "현재 작업 디렉토리 목록을 출력하라." | 목록 반환 |
| `[reviewer]` | "이 brief 자체의 모호한 점 1개만 지적하라." | 지적 1건 |
| `[multimodal]` | "이 문장의 글자 수를 세어 답하라." | 숫자 반환 |

`[multimodal]`(gemini)은 디스패처 경유라 별도 확인 가치가 가장 크다:

```bash
bash _shared/adapters/call_worker.sh gemini tasks/smoke/workers/gemini/brief.md
```

envelope의 `status`·`exit_code`·`duration_s`를 `log.md`에 남긴다. 실패 시
`stderr_sanitized`가 원인을 가리킨다. **`fallback_used`가 `true`면 primary가 죽은 것**이므로
그대로 넘기지 말고 원인을 확인한다.

## 3단계 — 검증

```bash
python3 _shared/audit-approvals.py tasks/smoke   # 승인 없이 호출된 워커 0건이어야
python3 _shared/check-limits.py    tasks/smoke   # 한도 초과 0건이어야
```

`log.md`에 `[WORKER_CALL]`·`[VERIFICATION]`을 남기고 `task.md`의 `status`를 `done`으로.

## 4단계 — 결과 기록

호출된 워커·소요시간·실패 항목을 팀 채널에 공유한다. 특히 **최초 1회는 OS별로**
(Windows·macOS 각 1명) 돌려 결과를 비교한다 — 지금까지 잡힌 결함은 대부분
"한쪽 OS에서만 터지는" 종류였다.

시스템 일반 교훈은 `_shared/learnings.md`, 사내·프로젝트 한정은 `_local/learnings.md`.
