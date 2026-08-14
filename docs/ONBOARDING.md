# 팀원 온보딩

처음 한 번만 하면 됩니다. **30분** 정도 걸립니다.

---

## 1. 도구 설치

| 도구 | 필수 | 비고 |
|------|------|------|
| Claude Code | ✅ | |
| Python 3 | ✅ | Windows는 `python`·`py`일 수 있음 |
| Git Bash | ✅ (Windows) | cmd·PowerShell로는 안 됩니다 |
| jq | ✅ | Windows `winget install jqlang.jq` · macOS `brew install jq` |
| codex CLI | 워커용 | |
| agy | 워커용 | |

### agy 설치했으면 이것도

`~/.gemini/antigravity-cli/settings.json` 파일에 추가:

```json
{ "permissions": { "allow": ["read_file(*)"] } }
```

없으면 이미지 검수가 **빈 결과**로 끝납니다. (`~/.gemini/settings.json`이 아닙니다)

---

## 2. 플러그인 설치

```
/plugins  →  Add Marketplace  →  punkyade/multiagent-ebiz  →  설치
```

---

## 3. 자기 프로젝트에 설치

담당 프로젝트 폴더에서 Claude Code를 띄우고:

```
멀티 에이전트 시스템 구성해줘
```

flavor는 **claude**, 대상은 **그 프로젝트 폴더**입니다.

**기존 파일은 안 건드립니다.** `README.md`·`.gitignore` 같은 건 이미 있으면 건너뛰고,
`CLAUDE.md`는 마커(`<!-- multiagent:start/end -->`) 안쪽에만 하네스 규칙이 들어갑니다.
프로젝트 규칙을 고칠 땐 **마커 바깥**을 고치세요.

### 설치되면 확인

```bash
ls _shared/new-task.py _shared/usage-report.py
```

**없으면 구버전입니다.** `/plugins`에서 마켓플레이스 갱신 후 다시 설치하세요.

---

## 4. 진단 (무료)

```bash
python3 _shared/doctor.py
```

**`핵심 이상 없음`** 이 나와야 합니다. 안 나오면 무엇이 빠졌는지 알려줍니다.

---

## 5. 첫 작업

```bash
python3 _shared/new-task.py <작업명> --workers claude-main --goal "한 문장"
```

만들어진 `tasks/<작업명>/`에서:

1. `task.md` — Goal·Constraints 작성
2. **사용자 승인 받고** `task.md`의 `workers_approved`에 기록
3. `workers/<역할>/brief.md` 작성
4. 워커 호출 → `result.md` 저장 → 검증

> `planned_workers`(계획)와 `workers_approved`(승인)는 **다른 칸**입니다.
> 승인 없이 부르면 `audit-approvals.py`가 잡아냅니다.

### 어떤 워커를 쓰나

`_shared/team-routing.md`를 보세요. 직군 언어로 말하면 알아서 고릅니다:

```
> 결제 페이지 퍼블 끝났는데 시안이랑 맞는지 봐줘
```

시안 대조는 프리셋이 있습니다:

```bash
python3 _shared/new-task.py <작업명> --preset design-diff
```

---

## 6. 확인용 명령 3개

```bash
python3 _shared/audit-approvals.py   # 승인 없이 부른 워커 있나
python3 _shared/check-limits.py      # brief가 너무 길지 않나
python3 _shared/usage-report.py      # 얼마나 썼나
```

---

## 7. 진행 상황 보기 (선택) — mat

터미널을 하나 더 열고:

```bash
cd <프로젝트 폴더>
mat
```

2초마다 갱신됩니다. 종료는 `q`.

**설치**: macOS `brew install netwaif/tap/mat` · Windows `go install github.com/netwaif/mat@latest`

| 키 | |
|---|---|
| `r` | 새로고침 |
| `t` | 작업 전환 |
| `L` | 로그 전체 |
| `q` | 종료 |

> `u`(사용량)는 빈 화면이 정상입니다. 사용량은 위 6번의 `usage-report.py`를 쓰세요.

---

## 8. 교훈 남기기

작업이 끝나면 **`_local/learnings.md`** 에 씁니다.

> `_shared/learnings.md`에 쓰면 시스템 갱신 때 **사라집니다.** `_local/`만 남습니다.

팀 전체에 해당하는 교훈이면 포크 repo에 PR을 올립니다:

```bash
git clone https://github.com/punkyade/multiagent-ebiz
# _shared/learnings.md 에 추가 → PR
```

머지되면 다음 갱신 때 모두에게 들어옵니다.

### 시스템 갱신

같은 폴더에서 `멀티 에이전트 시스템 구성해줘`를 다시 하면 됩니다.
`tasks/`·`_local/`은 보존됩니다.

---

## 막혔을 때

| 증상 | 확인 |
|------|------|
| 뭐가 안 됨 | `python3 _shared/doctor.py` 먼저 |
| 이미지 검수가 빈 결과 | 위 1번의 agy 권한 |
| `call_worker: jq 필요` | jq 설치 |
| Windows에서 디스패처 안 됨 | **Git Bash**에서 실행 |
| `status: empty` | 워커가 아무것도 못 냈다는 뜻. `stderr_sanitized`에 이유가 있음 |

`KNOWN_ISSUES.md`와 `_shared/learnings.md`를 한 번 훑어보고 시작하면 이미 밟은 지뢰를 피할 수 있습니다.
