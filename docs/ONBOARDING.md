# 팀원 온보딩 — multiagent-ebiz

기획 · 디자인 · 퍼블 · 프론트 · 백엔드 · QA 6직군 공용. 처음 한 번만 하면 됩니다.

## 팀 운영 방식 (결정 사항)

| 항목 | 방식 |
|------|------|
| 설치 위치 | **자기 프로젝트 폴더에 직접 얹는다** |
| 교훈·설정 환류 | **포크 repo에 PR** (`punkyade/multiagent-ebiz`) |
| 동시 작업 | 한 프로젝트는 보통 한 명 — 폴더 충돌 걱정 없음 |

각자 담당 프로젝트에서 그대로 씁니다. 대상 코드가 같은 폴더에 있으니 `target_repo`가 단순해집니다.

> **기존 프로젝트에 얹어도 안전합니다** (3.5.0-ebiz.13~). 생성기가
> `README.md`·`.gitignore`·`LICENSE`·`NOTICE`·`CHANGELOG.md`·`KNOWN_ISSUES.md`는 **이미 있으면
> 건드리지 않고**, `CLAUDE.md`는 마커(`<!-- multiagent:start/end -->`) 사이에만 하네스 규칙을
> 넣습니다. `.mcp.json`은 기존 서버를 남기고 병합합니다. 설치 후 **어느 파일을 안 건드렸는지
> 목록으로 알려줍니다.**
>
> 그래도 설치 전 **커밋해 두는 걸 권합니다** — git이면 무엇이 바뀌었는지 `git status`로 즉시 보입니다.

---

## 1. 도구 설치 (30분)

| 도구 | 용도 | 비고 |
|------|------|------|
| **Claude Code** | 오케스트레이터 + claude-main 워커 | 필수 |
| **Python 3** | 생성기·검사 도구 | 필수. Windows는 `python`·`py`일 수 있음 |
| **Git Bash** | 디스패처(bash 스크립트) | **Windows 필수.** cmd·PowerShell 단독 불가 |
| **jq** | 디스패처 JSON 파싱 | 필수. Windows `winget install jqlang.jq` / macOS `brew install jq` |
| **codex CLI** | codex-main · codex-critic 워커 | 정상 경로는 MCP 서버 |
| **agy** | gemini 워커 (멀티모달) | 네이티브 Windows·macOS 빌드 있음 |

### agy 설치 후 반드시 할 것 — 파일 읽기 권한

**이 설정 없이는 이미지·PDF 검수가 조용히 빈 결과로 끝납니다.** agy 헤드리스는 파일 읽기를 자동
거부합니다. `~/.gemini/antigravity-cli/settings.json`에 추가하세요:

```json
{ "permissions": { "allow": ["read_file(*)"] } }
```

> **`~/.gemini/settings.json`이 아닙니다.** 두 파일이 다 존재해서 헷갈립니다. 반드시
> `antigravity-cli/` 쪽입니다.

## 2. 플러그인 설치

1. Claude Code에서 `/plugins`
2. **Add Marketplace** → `punkyade/multiagent-ebiz`
3. 목록에서 **multiagent-ebiz** 설치·활성화

## 3. 자기 프로젝트에 얹기

담당 프로젝트 폴더에서 Claude Code를 띄운 뒤:

```
멀티 에이전트 시스템 구성해줘
```

flavor는 **claude**를 고르고 대상 폴더는 **그 프로젝트 폴더**를 지정합니다.
끝나면 `validate.py`가 자동으로 돌며 PASS를 보여줍니다.

설치 후 출력을 확인하세요 — 이런 줄이 나옵니다:

```
기존 파일 6개는 건드리지 않음(프로젝트 소유): .gitignore, README.md, LICENSE, ...
CLAUDE.md: 기존 지침 보존 + 하네스 블록 추가
기존 원문 백업: CLAUDE.md.multiagent-bak
```

`CLAUDE.md`는 **프로젝트 지침이 위, 하네스 규칙이 마커 안**에 들어갑니다. 프로젝트 규칙을 고칠 땐
마커 **바깥**을 고치세요 — 마커 안은 다음 갱신 때 덮입니다.

### 3-1. 버전 확인 — 반드시 하세요

플러그인 캐시가 낡으면 **구버전이 설치됩니다.** 겉보기엔 정상이고 `validate`도 전부 PASS라
알아채기 어렵습니다(실제로 겪은 일입니다).

```bash
ls _shared/new-task.py _shared/usage-report.py _templates/presets
```

**셋 다 있어야 최신입니다.** 하나라도 없으면:

1. `/plugins` → 마켓플레이스 **갱신** → 재설치
2. 같은 폴더에 다시 `멀티 에이전트 시스템 구성해줘` (마커 병합이라 기존 내용 안 깨집니다)

> 어느 버전이 캐시에 있는지는 `~/.claude/plugins/cache/multiagent-ebiz-marketplace/multiagent-ebiz/`
> 폴더 이름으로 확인합니다. 버전별로 쌓입니다.

> **이미 다른 에이전트 하네스가 도는 폴더**(예: `.claude/agents/`에 도메인 에이전트가 있는
> 프로젝트)라면 먼저 팀 리드와 상의하세요. 파일은 안 깨지지만 **두 체계의 작업 모델이 경쟁**합니다.

## 4. 환경 진단 — 무료, 반드시 통과시킬 것

```bash
python3 _shared/doctor.py
```

`핵심 이상 없음`이 나와야 합니다. **D7이 WARN이면 위 agy 권한 설정을 안 한 것**이고, 붙여넣을
JSON을 그대로 알려줍니다. WARN인 워커는 그 워커만 못 씁니다.

---

## 5. 첫 작업 해보기

```bash
python3 _shared/new-task.py 연습-작업 --workers claude-main --goal "한 문장으로 목표"
```

만들어진 `tasks/연습-작업/task.md`의 Goal·Constraints를 채우고, `workers/claude-main/brief.md`를
작성한 뒤 한도를 확인합니다:

```bash
python3 _shared/check-limits.py tasks/연습-작업
```

**워커를 부르기 전에 반드시 사용자 승인을 받고 `task.md`의 `workers_approved`에 기록합니다.**
계획(`planned_workers`)과 승인(`workers_approved`)은 다른 칸입니다. 승인 없이 부르면:

```bash
python3 _shared/audit-approvals.py tasks/연습-작업   # 위반이 잡힙니다
```

### 직군별로 어떤 워커를 쓰나

`_shared/team-routing.md`를 보세요. 직군 언어로 요청하면 오케스트레이터가 거기부터 봅니다:

```
> 결제 페이지 퍼블 끝났는데 시안이랑 맞는지 봐줘
```

시안 대조는 프리셋이 있습니다:

```bash
python3 _shared/new-task.py 결제-시안대조 --preset design-diff
```

---

## 5-1. 모니터 (선택) — mat

작업 진행을 터미널에서 지켜봅니다. 워커 상태(대기·실행 중·완료·에러)·목적·로그를 한 화면에서
보여주고, **시스템을 읽기만** 하므로 켜두거나 꺼도 진행에 영향이 없습니다.

```bash
# macOS
brew install netwaif/tap/mat

# Windows — 사전 빌드 바이너리가 없어 Go로 직접 빌드한다 (실측 확인: go 1.25.5)
go install github.com/netwaif/mat@latest      # → %USERPROFILE%\go\bin\mat.exe
```

실행 — **작업 이름을 인자로** 줍니다:

```bash
MAT_ROOT=<프로젝트 폴더> mat <작업명>
```

```
│ Workers                                        │
│   [ ⏳ ] claude-main    설계 문서 초안을 작성한다  │
│   [ ⏳ ] gemini         시안 이미지를 대조한다     │
```

> 워커 줄에 **brief의 Objective 첫 문장**이 뜹니다(3.5.0-ebiz.9~). 옛 템플릿으로 만든 brief는
> 엉뚱한 줄이 뜨니, 그러면 `python3 _shared/new-task.py`로 새로 만드세요.
> Windows에서 `mat`이 안 잡히면 `%USERPROFILE%\go\bin`을 PATH에 추가하세요.

## 5-2. 사용량 확인

디스패처가 호출마다 `_local/calls.jsonl`에 기록을 남깁니다(자동, 별도 조작 없음).

```bash
python3 _shared/usage-report.py            # 전체 기간
python3 _shared/usage-report.py --days 7   # 최근 7일
python3 _shared/usage-report.py --failures # 실패 건 상세
```

```
총 5회 · 성공 3 · 실패 2(빈출력 1 · 타임아웃 0) · 총 2.2분

워커별            호출  성공  실패  빈출력   총시간   평균
  gemini            3     2     1      1      43초   14초
  codex-critic      2     1     1      0     1.5분   45초
```

**비용만 보는 게 아닙니다.** 실패·빈출력·폴백 비율이 함께 보이므로 품질 이상이 집계에서 먼저
드러납니다 — "gemini 빈출력이 갑자기 늘었다"면 권한 설정이나 백엔드 쪽 문제입니다.

> `claude-main`은 native 호출이라 디스패처를 안 거쳐 원장에 안 남습니다. 리포트가 `log.md`
> 기준 호출 수를 함께 보여주며, 두 숫자의 차이가 원장의 사각지대입니다.

## 6. 교훈 환류 — 이게 팀이 같이 나아지는 방법

**작업이 끝나면 교훈을 `_local/learnings.md`에 씁니다.** 여기가 먼저인 이유가 있습니다:

> ⚠️ `_shared/learnings.md`에 **직접 쓴 내용은 시스템을 갱신할 때 사라집니다**(번들 템플릿으로
> 덮임). `_local/`은 보존 대상이라 살아남습니다.

그중 **나만이 아니라 팀 전체에 해당하는 교훈**이면 포크 repo에 PR을 올립니다:

```bash
git clone https://github.com/punkyade/multiagent-ebiz
# _shared/learnings.md 에 항목 추가 → PR
```

PR 대상 파일은 셋입니다:

| 파일 | 언제 |
|------|------|
| `_shared/learnings.md` | 시스템 운영 일반 교훈 (도구 함정, 실패 패턴) |
| `_shared/capability-profile.md` | 슬롯↔워커 배정을 바꿔야 할 실측 근거가 생겼을 때 |
| `_shared/team-routing.md` | 직군별 작업 매핑이 실제와 다를 때 |

머지되면 다음에 시스템을 갱신할 때 자동으로 들어옵니다.

### 시스템 갱신 받기

```
멀티 에이전트 시스템 구성해줘   # 같은 폴더를 대상으로 다시 실행 (update 모드)
```

`tasks/`·`_local/`은 보존되고 시스템 파일만 최신화됩니다.

---

## 7. 막혔을 때

| 증상 | 확인 |
|------|------|
| 뭔가 안 돌아감 | `python3 _shared/doctor.py` 먼저 |
| 이미지 검수가 빈 결과 | agy 권한(위 1번). doctor D7이 잡습니다 |
| `call_worker: jq 필요` | jq 설치 |
| Windows에서 디스패처 실행 안 됨 | **Git Bash에서** 실행하세요 |
| envelope `status: empty` | 워커가 아무것도 못 냈다는 뜻. `stderr_sanitized`에 사유가 있습니다 |
| 워커 결과가 이상함 | `log.md`에 남기고, 재현되면 교훈으로 PR |

알려진 결함은 `KNOWN_ISSUES.md`, 도구 함정 사례는 `_shared/learnings.md`에 쌓여 있습니다.
**둘 다 한 번 훑어보고 시작하면 이미 밟은 지뢰를 다시 밟지 않습니다.**
