<p align="center">
  <img src="./assets/brand/harness-multiagent-banner.png" alt="Harness MultiAgent" width="100%">
</p>

# multiagent-ebiz

Claude·Codex·Gemini를 **역할별 워커로 나눠 쓰는** 파일 기반 멀티에이전트 시스템.
프로젝트 폴더에 얹으면 작업 폴더·승인 게이트·검증 도구가 한 벌 생깁니다.

> **팀원이라면 → [`docs/ONBOARDING.md`](./docs/ONBOARDING.md)** (30분, 한 번만)

ebiz 내부 포크입니다. 원작: [netwaif/multi-agent-starter](https://github.com/netwaif/multi-agent-starter) (MIT).

---

## 왜 쓰나

혼자 물어보는 것과 다른 점은 세 가지입니다.

- **역할 분리** — 설계는 Claude, 대규모 구현·브라우저 조작은 Codex, 이미지·대용량 문서는 Gemini
- **승인 게이트** — 유료 워커를 부르기 전에 사람이 승인. 나중에 감사로 지켜졌는지 확인
- **파일로 남음** — 목표·결정·브리프·결과·검증이 전부 파일. 세션이 끊겨도 이어집니다

## 설치

```
/plugins  →  Add Marketplace  →  punkyade/multiagent-ebiz  →  설치
```

담당 프로젝트 폴더에서 Claude Code를 띄우고 `멀티 에이전트 시스템 구성해줘`.

**기존 프로젝트에 얹어도 안전합니다.** `README.md`·`.gitignore` 등은 이미 있으면 건너뛰고,
`CLAUDE.md`는 마커(`<!-- multiagent:start/end -->`) 안쪽만 갱신합니다.

## 쓰는 법

```bash
python3 _shared/new-task.py <작업명> --workers claude-main --goal "한 문장"
```

작업 폴더가 생기면 `task.md`에 목표를 적고, **승인을 받은 뒤** 워커를 부릅니다.

직군(기획·디자인·퍼블·프론트·백엔드·QA) 언어로 말하면 알아서 워커를 고릅니다:

```
> 결제 페이지 퍼블 끝났는데 시안이랑 맞는지 봐줘
```

### 도구

| 명령 | 하는 일 |
|------|---------|
| `_shared/doctor.py` | 환경 진단 (제일 먼저) |
| `_shared/new-task.py` | 작업 폴더 만들기 |
| `_shared/audit-approvals.py` | 승인 없이 부른 워커 검출 |
| `_shared/check-limits.py` | brief 길이 검사 |
| `_shared/usage-report.py` | 호출·소요시간 집계 |

진행 상황은 [mat](https://github.com/netwaif/mat)으로 봅니다 — `cd <폴더> && mat`.

## 라우팅 3층

**워커는 직군이 아니라 능력입니다.** "디자이너 워커"는 없고, 작업 성격으로 슬롯을 고릅니다.

| 층 | 파일 | 답하는 질문 |
|----|------|------------|
| 사내 | `_shared/team-routing.md` | 퍼블 직군의 이 일은 어떤 슬롯인가 |
| 안정 | `_shared/routing.md` | 이 작업은 어떤 슬롯인가 |
| 가변 | `_shared/capability-profile.md` | 그 슬롯은 지금 어떤 워커가 맡나 |

사내 판단이 바뀌면 `team-routing.md`만 고칩니다 — 업스트림 갱신과 충돌하지 않습니다.

## 필요한 것

- **Python 3** · **jq** — 필수
- **Git Bash** — Windows 필수 (cmd·PowerShell 불가)
- **codex CLI** · **agy** — 해당 워커를 쓸 때
- **git** — 권장

> agy를 쓰면 `~/.gemini/antigravity-cli/settings.json`에
> `{"permissions":{"allow":["read_file(*)"]}}` 를 넣어야 이미지 검수가 됩니다.

문제가 생기면 `python3 _shared/doctor.py`가 무엇이 빠졌는지 알려줍니다.

---

## 유지보수

<details>
<summary>저장소 구조 · 테스트 · 업스트림 갱신</summary>

### 구조

```
multiagent-ebiz/
├── .claude-plugin/marketplace.json   # Claude Code 마켓 카탈로그
├── .agents/plugins/marketplace.json  # Codex 마켓 카탈로그
├── plugins/multi-agent-starter/      # 플러그인 본체
│   └── skills/configure-multiagent/
│       ├── SKILL.md
│       └── generator/                # init.py · validate.py · build_zip.py · templates/
├── tests/                            # 오프라인 회귀 테스트 (run.sh)
└── docs/ONBOARDING.md                # 팀원 온보딩
```

플러그인 디렉토리 이름이 `multi-agent-starter`인 이유: 테스트·불변식 스크립트가 이 경로를
하드코딩합니다. 호스트에 표시되는 이름은 매니페스트의 `name`(`multiagent-ebiz`)입니다.

### 테스트

```bash
bash tests/run.sh                    # 16개 스위트, 외부 호출 0
bash _shared/check-invariants.sh     # 불변식
```

CI가 ubuntu·macOS·windows 3중으로 돌립니다. 세 OS에서만 드러나는 결함이 실제로 여러 건
있었으므로(로케일·경로 깊이·bash 버전) 매트릭스를 줄이지 마세요.

### 업스트림 갱신

```bash
git fetch upstream && git merge upstream/main
```

병합 후 위 테스트 2종과 `sync_claude_template.py`를 돌려 정합성을 확인합니다.

</details>

알려진 이슈는 [`KNOWN_ISSUES.md`](./KNOWN_ISSUES.md), 변경 이력은 [`CHANGELOG.md`](./CHANGELOG.md).

## 라이선스

[MIT](./LICENSE) — 원작 저작권 표시는 `LICENSE`·`NOTICE`에 유지됩니다.
