# Team Routing — 직군별 작업 유형 → 능력 슬롯 (ebiz 사내층)

`routing.md`(안정층)의 decision tree를 **우리 팀 직군 언어로 들어가는 입구**다.
기획 · 디자인 · 퍼블 · 프론트 · 백엔드 · QA 6개 직군이 실제로 가져오는 작업을
어떤 **능력 슬롯** 조합과 **토폴로지**로 처리할지 미리 정해 둔 것.

**이 파일은 사내 전용이다.** 업스트림(netwaif/multi-agent-starter)에 없는 파일이라
업스트림 갱신을 병합할 때 충돌이 나지 않는다. 사내 판단이 바뀌면 여기만 고친다.

## 읽는 법 — 3층 구조

| 층 | 파일 | 답하는 질문 | 바뀌는 빈도 |
|----|------|------------|-----------|
| 사내층 | **이 파일** | "퍼블 직군의 이 일은 어떤 슬롯 조합인가?" | 팀 운영 방식이 바뀔 때 |
| 안정층 | `routing.md` | "이 작업 성격은 어떤 슬롯인가?" | 거의 안 바뀜 |
| 가변층 | `capability-profile.md` | "그 슬롯은 지금 어떤 워커가 맡나?" | 신모델 출시 때 |

**슬롯 이름만 쓴다** — 워커명(claude-main 등)은 여기 적지 않는다. 슬롯→워커 배정의 정본은
`capability-profile.md`이고, flavor에 따라 워커 풀이 다르기 때문이다(이 파일은 3 flavor 공용).

## 직군별 매핑

### 기획

| 작업 | 슬롯 | 토폴로지 |
|------|------|---------|
| 요구사항 정의 · 기획서 · 유저스토리 · 정책 문서 | `[strategist]` | Pipeline |
| 기획서 리스크·구멍 점검 | `[strategist]` → `[reviewer]` | Producer-Reviewer |
| 경쟁사·레퍼런스 대량 문서 분석 (50p+) | `[multimodal]` | Pipeline |
| 기존 서비스 동작 조사 (실제 화면 확인 필요) | `[computer-use]` | Pipeline |

### 디자인

| 작업 | 슬롯 | 토폴로지 |
|------|------|---------|
| 디자인 방향 · 컨셉 · UX 흐름 · 카피 톤 | `[strategist]` | Pipeline |
| 시안 이미지 리뷰 (일관성 · 접근성 · 가독성) | `[multimodal]` | Pipeline |
| **시안 ↔ 구현 픽셀 대조** | `[computer-use]`(캡처) → `[multimodal]`(대조) | Pipeline |
| 아이콘 · 에셋 생성 | `[engineer]` | Pipeline |

### 퍼블

| 작업 | 슬롯 | 토폴로지 |
|------|------|---------|
| HTML/CSS 마크업 구현 | `[engineer]` | Pipeline |
| 렌더 확인 · 크로스브라우저 · 반응형 검증 | `[computer-use]` | Pipeline |
| **시안 대조 후 수정** | `[computer-use]` → `[multimodal]` → `[engineer]` | Pipeline |
| 시맨틱 · 접근성 마크업 리뷰 | `[reviewer]` | Producer-Reviewer |

### 프론트

| 작업 | 슬롯 | 토폴로지 |
|------|------|---------|
| 컴포넌트 · 상태 구조 설계 | `[strategist]` → `[engineer]` | Pipeline |
| 대규모 구현 · 리팩토링 · 테스트 | `[engineer]` | Pipeline |
| 실제 동작 검증 (E2E · 인터랙션) | `[computer-use]` | Pipeline |
| 코드 리뷰 (사이드이펙트 · 성능) | `[reviewer]` | Producer-Reviewer |
| 버그 원인 분석 | `[strategist]` | Pipeline |

### 백엔드

| 작업 | 슬롯 | 토폴로지 |
|------|------|---------|
| API · 스키마 · 아키텍처 설계 | `[strategist]` → `[engineer]` | Pipeline |
| 구현 · 테스트 작성 · 마이그레이션 | `[engineer]` | Pipeline |
| 성능 · 보안 · 사이드이펙트 리뷰 | `[reviewer]` | Producer-Reviewer |
| 장애 원인 분석 (로그·트레이스 기반) | `[strategist]` | Pipeline |
| 대용량 로그·스펙 문서 분석 | `[multimodal]` | Pipeline |

### QA

| 작업 | 슬롯 | 토폴로지 |
|------|------|---------|
| 테스트 케이스 · 시나리오 설계 | `[strategist]` | Pipeline |
| E2E 자동화 작성 · 실행 | `[computer-use]` | Pipeline |
| **결함 재현 + 스크린샷 분석** | `[computer-use]` ∥ `[multimodal]` | Fan-out/Fan-in |
| 회귀 범위 판정 · 릴리스 게이트 | `[reviewer]` | Producer-Reviewer |

## 이 팀에서 레버리지가 가장 큰 조합

**`[computer-use]` → `[multimodal]` (캡처 → 대조)** — 디자인 · 퍼블 · QA 3개 직군이 공유하는
"눈으로 보고 비교하는 일"을 자동화한다. 사람이 가장 많이 반복하고 가장 자주 놓치는 구간이다.

주의: `[multimodal]`에 이미지를 넘길 땐 **brief 본문에 절대경로를 직접 적는다**.
소스 코드·다중 파일은 경로 나열 대신 `sources/` packet + 디스패처 3번째 인자로 동봉한다
(`routing.md`의 gemini 항목 — 디렉토리 순회를 시키면 타임아웃으로 전멸한다).

## 직군 공통 규칙

1. **직군 ≠ 워커.** 위 표는 "누가 요청했나"가 아니라 "작업 성격이 무엇인가"로 슬롯을 고른 것이다.
   백엔드 담당자의 기획성 작업은 `[strategist]`로 간다.
2. **최소 set 유지.** 표에 슬롯이 둘 적혀 있어도 앞 단계로 충분하면 뒤는 부르지 않는다.
   `routing.md`의 「최소 Worker Set 원칙」·「Worker 추가 조건」이 그대로 적용된다.
3. **승인 게이트는 예외 없다.** 이 표는 *권장 조합*이지 사전 승인이 아니다.
   워커 호출 전 `task.md`의 `workers_approved` 기록은 그대로 필요하다.
4. **직군 파이프라인을 한 작업 폴더에 몰지 말 것.** 기획→디자인→퍼블→프론트/백엔드→QA를
   한 폴더에서 통째로 돌리면 context.md 한도가 무너진다. 단계마다 폴더를 나누되,
   생성 전 `orchestrator-rules.md` §3 「새 작업 폴더 생성 게이트」를 먼저 적용한다.
5. **외부 repo 쓰기는 4조건.** 구현 작업이 많은 직군(퍼블·프론트·백엔드)일수록 자주 걸린다.
   기본값은 `write_scope: tasks-only`이고, 외부 repo 직접 쓰기는 `CLAUDE.md`의 4조건을 모두 충족해야 한다.

## 갱신 이력 (append-only)

- **2026-08-13** 초기 작성. 팀 6직군(기획·디자인·퍼블·프론트·백엔드·QA) 기준 매핑.
  슬롯 용어로만 기술해 3 flavor 공용으로 둠. 근거: 팀 업무 구성 확인(사내).
