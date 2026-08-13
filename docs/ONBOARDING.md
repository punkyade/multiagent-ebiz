# 팀원 온보딩 — multiagent-ebiz

기획 · 디자인 · 퍼블 · 프론트 · 백엔드 · QA 6직군 공용. 처음 한 번만 하면 됩니다.

## 팀 운영 방식 (결정 사항)

| 항목 | 방식 |
|------|------|
| 시스템 폴더 | **개인당 1개.** 대상 프로젝트는 `target_repo`로 가리킨다 |
| 교훈·설정 환류 | **포크 repo에 PR** (`punkyade/multiagent-ebiz`) |
| 동시 작업 | 한 프로젝트는 보통 한 명 — 폴더 충돌 걱정 없음 |

개인 폴더 1개로 모든 프로젝트를 처리합니다. 프로젝트마다 폴더를 만들지 마세요 — 교훈이 흩어지고,
`log.md`가 쪼개져 나중에 되짚기 어려워집니다.

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

## 3. 개인 시스템 폴더 만들기

빈 폴더를 하나 정하고(예: `~/multiagent`), 그 폴더에서 Claude Code를 띄운 뒤:

```
멀티 에이전트 시스템 구성해줘
```

flavor는 **claude**를 고릅니다. 끝나면 `validate.py`가 자동으로 돌며 PASS를 보여줍니다.

> ⚠️ **이미 다른 하네스나 `CLAUDE.md`가 있는 폴더에 만들지 마세요.** 생성기는 `CLAUDE.md`와
> `.mcp.json`을 덮어씁니다(`CLAUDE.md`는 `.multiagent-bak`으로 백업되지만 `.mcp.json`은 안 됩니다).

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
