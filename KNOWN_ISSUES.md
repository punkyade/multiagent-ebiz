# 알려진 이슈

해결되지 않은 알려진 결함을 추적한다. 고쳐지면 해당 항목을 닫고(✅) PR 링크를 단다.
시스템이 깨지는 크리티컬은 즉시 수정 대상, 표시·미관 한정은 보류 가능.

출처: `repo-consistency-audit` (2026-05-19, claude-main·codex-main 병렬 + Orchestrator 교차검증).
상세 근거표(`repo-consistency-audit`)는 공개 배포본에 미포함 — 유지보수자 전용.

---

## KI-1 (audit C3) — 표준 `worker-brief.md`를 쓰면 mat이 워커 목적을 엉뚱한 줄로 표시

- **상태**: ✅ **해소** (3.5.0-ebiz.9, 수정 후보 (a) 채택)
- **심각도**: 낮음 — 시스템·워커 호출·데이터에 영향 없음. mat **모니터 화면 표시만** 오염했다.

### 증상 (해소 전)

mat의 핵심 화면 요소인 "워커 한 줄 목적"이 실제 Objective가 아닌 줄로 표시됐다.

### 근본 원인

| repo | 파일·라인 | 내용 |
|------|-----------|------|
| mat | `internal/parser/task.go:280` | brief 존재 시 무조건 `w.Purpose = firstMeaningfulLine(brief 내용)` |
| mat | `internal/parser/task.go:499–515` | `firstMeaningfulLine`은 **빈 줄·`#`시작·`<!--`시작만 skip**, 그 다음 줄을 그대로 반환 |
| mat | `internal/parser/task.go:71–76` | `w.Purpose == ""`일 때만 `planned_workers.purpose`로 fallback |

> **원 기록 정정 (2026-08-13 실측)**: 이 항목은 표시되는 값이 ` ```yaml ` fence라고 적고 있었으나, 그 뒤 `## Worker 행동 규약` 고정 블록이 템플릿에 삽입되면서 실제 증상이 바뀌었고 문서가 따라오지 않았다. 실측 시점의 값은 규약 블록의 첫 불릿(`- 요청 범위만 최소로…`)이었고, 대상 4벌 전부 동일했다. **증상 기록에 측정 일자를 남기지 않으면 언제 거짓이 됐는지 알 수 없다**는 사례다.

### 해소 방법 (후보 (a))

`## Objective` 섹션을 `## Worker 행동 규약` 블록 **위로 이동**했다. mat이 `#`으로 시작하는 줄을 전부 건너뛰므로 `## Objective` 헤딩도 skip되고 **그 다음 줄인 목적 본문**이 선택된다.

- **추가 글자 0자** — 순수 이동이라 1200자 한도에 영향이 없다. 목적의 정본도 한 곳뿐이라 동기화 대상이 생기지 않는다.
- 자리표시자를 `<한 문장 — 이 worker가 완료해야 하는 것>`으로 바꿔, **안 채운 brief는 mat에서 즉시 드러나게** 했다.
- 적용 범위 **16벌** — 루트 4 + `generator/templates/{claude,codex,antigravity}` 각 4.
- 규약 블록은 문구·순서 그대로이고 뒤따르는 `## Execution Context` 순서도 유지되어 INV12·INV12c 범위가 성립한다.

함께 처리: `worker-brief.md` 스캐폴드 슬림화(가변부 1161→639자). 안내문을 HTML 주석으로 내렸고, **디스패처가 brief의 HTML 주석을 떼고 워커에 전달**하도록 바꿔 측정과 실제 전달량을 일치시켰다.

### 알려진 잔여 취약점 (별건)

INV12c는 `sed -n '/^## Worker 행동 규약/,/^## Execution/p'` 로 종료 앵커가 `## Execution`에 결합돼 있다. 규약 블록 뒤 섹션명을 바꾸면 범위가 EOF까지 늘어나 오탐/미탐이 난다. 종료 앵커를 `/^## /`로 일반화할 것을 권한다.

### 참고

- 공개 흔적: `_shared/learnings.md` [2026-05-19], PR #5 본문.
- 해소 경위: CHANGELOG `3.5.0-ebiz.9`. 작업 폴더(`tasks/mat-purpose-fix/`)는 `.gitignore` 대상이라 저장소에 포함되지 않는다 — claude-main 설계 → codex-critic 검증 → Orchestrator 적용 흐름.

---

## KI-2 — Antigravity 호스트 설치 경로 미확정 (루트 `plugin.json` 미동봉)

- **상태**: 열림 / **보류** (생성 코어엔 영향 없음. 머지 전 실설치 검증 대상)
- **심각도**: 중간 — `antigravity` flavor **생성·validate(12/12)·ZIP**은 호스트 독립으로 PASS. 영향 범위는 Antigravity를 **오케스트레이터 호스트로 두고 플러그인을 설치**하는 경로 한정.

### 증상

이 repo는 `.claude-plugin/`(Claude Code)·`.codex-plugin/`(Codex) 매니페스트만 동봉한다. 설계서(`design.md` Part A)가 Antigravity 호스트용으로 명시한 **루트 `plugin.json`은 repo에 없다**. 따라서 Antigravity 호스트의 로컬·마켓플레이스 설치 행은 매니페스트 없이 미검증 상태다.

### 실증된 것 / 미확정인 것

- **실증(2026-06-02, agy v1.0.4)**: agy로 플러그인을 로컬 사용 → "구성해줘" → 생성기 → validate PASS, end-to-end 동작. → agy가 플러그인+스킬을 **읽고 트리거**하는 것은 확인됨. (당시 antigravity flavor 추가 전이라 claude flavor로 실증.)
- **미확정**: agy/Antigravity IDE가 실제로 **어떤 매니페스트를 소비**하는지(skills/ 자동탐색 vs 루트 매니페스트 vs `.codex-plugin` 재사용). 루트 `plugin.json`의 정확한 스키마도 미확인.

### 다음 (머지 전)

- 사용자 Antigravity IDE 실설치로 (a)로컬 설치를 먼저 검증. (b)마켓플레이스 설치는 **PR 머지 전 검증 불가**(마켓플레이스는 main을 pull하므로) — 머지 후에만 가능.
- 실제 로딩 경로 확인 후, 필요하면 루트 `plugin.json`을 올바른 스키마로 추가하고 본 항목을 닫는다(✅).
- 그 전까지 매니페스트·README는 Antigravity를 **설치 호스트로 보장하지 않고**(생성 flavor로만 광고) 보수적으로 둔다.

---

## KI-3 — Windows 지원: **조건부 지원**으로 하향 (Git Bash + jq 필요)

- **상태**: **부분 해소** (3.5.0-ebiz.1) / 잔여 항목만 열림
- **심각도**: 낮음–중간 — 차단점이던 CRLF 결함은 해소. 남은 것은 **실호출 스모크 미검증** 한정.

> ebiz 포크 갱신 (2026-08-12, Windows 11 / Git Bash 실측). 원 항목의 전제 두 개가 **사실이 아님**이 확인돼 재작성했다.

### 원 항목에서 뒤집힌 전제

| 원 서술 | 실측 |
|---|---|
| "agy는 맥/리눅스 지향, 네이티브 Windows 빌드 미확인" | **네이티브 Windows 빌드 존재** — `agy` v1.1.12, `PE32+ executable for MS Windows x86-64`. WSL 불필요 |
| "Git Bash는 리눅스 바이너리를 못 돌리므로 더 불확실" | agy·codex·jq 모두 네이티브 Windows 빌드라 Git Bash에서 그대로 실행됨 |

### 실제 차단점이었던 것 (해소됨)

원 항목이 지목한 POSIX 의존(`bash`·`mktemp`·`/dev/null`)은 Git Bash가 전부 제공하므로 차단점이 아니었다.
진짜 원인은 **네이티브 Windows `jq`가 stdout에 CRLF를 쓴다**는 점이었다:

- MSYS bash의 `$()`는 **끝의 CR만** 제거 → 스칼라 읽기는 멀쩡한데 `args_template[]` 같은 **다중행 순회에서만** `\r`이 남았다.
- 그 결과 `cli` 워커 인자가 `"exec\r"`·`"--prompt\r"` 형태로 오염돼 **gemini·codex CLI 폴백이 전량 실패**.
- 수정: `call_worker.sh`의 jq 줄단위 순회 3곳에서 CR 제거. 저장소 개행은 `.gitattributes`(`* text=auto eol=lf`)로 고정.

### 남은 미검증 (사내 검증 대상)

- **gemini 워커 실호출 스모크 1회** — 유료 호출이라 승인 게이트 대상. 미실행.
- **codex CLI 폴백** 실경로(정상 경로인 MCP 서버는 무관).
- macOS에서의 회귀 테스트 재확인 — 오늘 수정분은 Windows에서만 `tests/run.sh` 전량 통과를 확인했다.

### 요구사항 (Windows)

**Git Bash + jq** 필수. cmd·PowerShell 단독 실행은 여전히 불가 — 디스패처가 bash 스크립트인 설계는 그대로다.
OS 독립화(디스패처 Python 이식)는 위 전제가 뒤집힌 이상 **우선순위에서 내린다**.
