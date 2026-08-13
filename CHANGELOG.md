# Changelog

이 파일은 multi-agent-starter **패키지/배포**의 버전 이력이다.
**설치된 시스템의 동작** 변경 이력은 생성된 폴더의 `CHANGELOG.md`
(정본: `generator/templates/{claude,codex}/CHANGELOG.md`)를 참조한다.
형식은 [Keep a Changelog](https://keepachangelog.com/), 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따른다.

## [3.5.0-ebiz.11] - 2026-08-13

팀 운영 방식 확정(**개인별 폴더 1개 · 포크 repo PR 환류 · 동시 작업 없음**)에 맞춘 온보딩.

### Fixed
- **`_shared/learnings.md`에 쓴 교훈이 update 때 사라지는 것을 지침이 몰랐다** — 생성기
  update 모드는 `_shared/*`를 번들 템플릿으로 덮는다(실측: 추가한 줄 0건 생존, `_local/`은
  1건 생존). 그런데 `CLAUDE.md` 9번은 "시스템 일반 교훈 → `_shared/learnings.md`"로 안내하고
  있어, **지침을 그대로 따르면 다음 갱신에 교훈을 잃는다.** PR 환류 모델의 전제가 깨진다.
  → 9번을 "**먼저 `_local/`에 쓴다** → 일반 교훈이면 배포 저장소에 반영 요청 → 머지 후
  update로 정식 수령"으로 교정(3 flavor. AGENTS.md 동등 항목 포함).

### Added
- **`docs/ONBOARDING.md`** — 팀원 온보딩 1회 절차. 도구 설치표, **agy 파일 읽기 권한**
  (`~/.gemini/antigravity-cli/settings.json` — `~/.gemini/settings.json`이 아님), 개인 폴더 생성,
  doctor 통과, 첫 작업, 승인 게이트, 교훈 PR 환류, 증상별 확인표.
  README에서 팀원용 진입점으로 연결.

## [3.5.0-ebiz.10] - 2026-08-13

### Fixed
- **macOS bash 3.2에서만 터지는 셸 결함** — `echo "길이 $LEN자"` 가
  `LEN자: unbound variable` 로 죽었다. macOS 기본 `/bin/bash`는 3.2이고 **변수명을 바이트
  단위로 읽어 뒤따르는 한글까지 이름에 포함**시킨다. bash 5.x(리눅스·Git Bash)는
  멀티바이트를 인식해 `$LEN`에서 끊으므로 **다른 두 OS에서는 드러나지 않았다.**
  → `${LEN}` 중괄호 명시.

### Added
- **`tests/test_shell_portability.py`** — 셸 스크립트 전수 린트. `$VAR` 뒤에 비-ASCII가
  바로 붙은 곳을 잡는다(주석 줄은 제외). 이 저장소는 셸에 한글 메시지를 많이 써서 재발
  가능성이 높다. 일부러 깨뜨린 줄을 검출하는 것까지 확인했다.

## [3.5.0-ebiz.9] - 2026-08-13

**첫 실전 작업**(`mat-purpose-fix`)을 하네스로 수행하며 나온 결과. 작업 자체(KI-1 해소)보다
**과정에서 드러난 하네스 결함 3건**이 중요하다.

### Fixed
- **디스패처가 유료 호출 결과를 통째로 유실** — 최종 envelope를 `jq --argjson e "$env"` 로
  **argv에** 실어 넘기다 `Argument list too long`(exit 126). codex-critic이 1분 27초 정상
  수행한 결과가 사라졌다. 워커 출력이 argv 한계(Windows ~32KB)를 넘으면 **항상** 발생한다.
  → `add_flag()` 헬퍼로 herestring(stdin) 전달. 회귀 가드 `test_large_output.sh`(7)로
  198,893자·8000줄 보존 실측 고정. **단위 테스트로는 나올 수 없고 실제 워커 호출이 필요했다.**
- **`check-limits` 측정이 실제 전달량과 어긋남** — 주석을 한도에서 제외하면서 디스패처는
  `@brief_content = cat` 으로 **주석 포함 전문**을 워커에 보내고 있었다("주석에 임의 내용을
  숨겨 한도를 무력화할 수 있다" — codex-critic).
  → 디스패처가 brief의 HTML 주석을 **떼고 전달**한다. 측정과 실제가 일치하고 토큰도 실제로
  준다. payload(동봉 자료)는 원본이라 미처리. 회귀 가드 `test_strip_comments.sh`(8).

### Changed
- **KI-1 해소** — `## Objective` 섹션을 `## Worker 행동 규약` 블록 **위로 이동**.
  mat이 `#` 시작 줄을 전부 건너뛰는 성질을 이용해 **줄 추가 없이**(0자) 해결했고, 목적의
  정본도 한 곳뿐이라 동기화 대상이 생기지 않는다. 적용 **16벌**(루트 4 + 3 flavor × 4).
  자리표시자를 `<한 문장 — …>`으로 바꿔 **안 채운 brief가 mat에서 즉시 드러나게** 했다.
- **`worker-brief.md` 스캐폴드 슬림화** — 가변부 1161 → **639자**(여유 39 → 561자).
  안내문을 HTML 주석으로 이동(위 디스패처 변경으로 실제 절감이 된다), `Prior Results`는
  주석 스텁으로 강등. 프리셋 3벌은 이동만 적용(외과수술식).
- `KNOWN_ISSUES.md` KI-1 ✅ 해소 표기 + **낡은 근본 원인 표 교정** — 기록된 증상(` ```yaml `)이
  규약 블록 삽입 이후 바뀌었는데 문서가 따라오지 않았다. 실측 시점 값은 규약 블록 첫 불릿이었다.
- `_shared/learnings.md` [2026-08-13] 기록.

## [3.5.0-ebiz.8] - 2026-08-13

시안 대조 프리셋. 검증 과정에서 **이미지 검수 정본 경로가 조용히 죽어 있던 것**을 발견·수정.

### Added
- **프리셋 `design-diff`** (`_templates/presets/design-diff/`, 3 flavor) —
  `[computer-use]` 캡처 → `[multimodal]` 대조 → `[engineer]` 수정. 디자인·퍼블·QA
  3직군이 공유하는 "눈으로 보고 비교하는 일"을 고정 파이프라인으로.
  ```bash
  python3 _shared/new-task.py <작업명> --preset design-diff
  ```
  - 슬롯 → 워커는 `capability-profile.md`에서 해석하므로 flavor마다 자동으로 달라진다.
    워커가 없는 슬롯(antigravity의 `multimodal`)은 brief를 만들지 않고 "오케스트레이터
    직접"이라 안내한다.
  - 한 워커가 두 단계를 맡으면(claude flavor의 `engineer`·`computer-use` = 둘 다
    codex-main) 뒤 단계는 `brief-<슬롯>.md`로 분리해 충돌을 피한다.
  - 프리셋 파일명은 `<순번>-<슬롯>.md` — 단계 순서가 파이프라인의 의미 그 자체라
    알파벳 정렬에 맡기면 조용히 뒤집힌다.
- **디스패처 빈 출력 판정** — `exit 0` 인데 stdout이 비면 `status: empty` + 폴백 체인
  진입(envelope의 `exit_code`는 자식 실제값 유지). 이 저장소에서만 같은 위장이 2번
  나왔다: 2026-07-03 agy `-p` 제거, 2026-08-13 권한 자동거부. 둘 다 `status: ok` 였다.
  회귀 가드: `tests/dispatcher/test_empty_output.sh`(6).
- **doctor D7** — agy 파일 읽기 권한 사전 검사. 미설정이면 붙여넣을 JSON을 출력한다.
- `tests/test_new_task.py` 프리셋 6케이스 추가 (총 17).

### Fixed
- **agy 헤드리스 파일 읽기 자동 거부로 이미지·PDF 검수가 무력화돼 있었다.**
  `routing.md`가 "단일 정본 경로, 필독"으로 못박고 실측까지 적어둔 경로가 agy 버전업으로
  막혔고, `status: ok`·`exit 0`·빈 출력이라 **실패 신호가 어디에도 없었다.**
  해결: `~/.gemini/antigravity-cli/settings.json` 에
  `{"permissions":{"allow":["read_file(*)"]}}`.
  **`~/.gemini/settings.json`이 아니다** — 두 파일이 다 존재하고 후자는 효과가 없다.
- **`check-limits.py`·`audit-approvals.py`가 `brief-<슬롯>.md`를 검사 대상에서 누락** —
  프리셋이 만드는 파일명이라 글롭을 `brief*.md`로 확장. 누락 시 외부 쓰기 검사에 구멍이 난다.

### 실측 (2026-08-13)
- 이미지 **2장 동시 전달 정상** — 22s, exit 0, 두 스크린샷 각각 정확히 판별.
  프리셋의 캡처↔시안 대조가 1회 호출로 성립한다.

## [3.5.0-ebiz.7] - 2026-08-13

### Added
- **작업 폴더 스캐폴더 `_shared/new-task.py`** (3 flavor) — `tasks/<작업명>/` 한 벌
  (task.md · context.md · log.md · sources/ · artifacts/ · workers/<역할>/brief.md)을
  템플릿에서 결정적으로 생성. 6명이 매일 반복하는 손복사를 없앤다 — 복사가 어긋나면
  mat 파싱·`audit-approvals.py`·`check-limits.py`가 전부 대상을 놓친다.
  ```bash
  python3 _shared/new-task.py <작업명> --workers claude-main,codex-main --goal "한 문장"
  ```
  - **`workers_approved`는 채우지 않는다** — 스캐폴더가 미리 채우면 승인 게이트가
    무의미해진다. `--workers`는 `planned_workers`(계획)만 채운다. 계획 ≠ 승인.
  - 역할은 `backends.json`의 workers 키로 검증(flavor마다 풀이 달라 하드코딩 안 함).
  - 기존 작업 덮어쓰기 거부, 경로 구분자·`..` 이름 거부, `--dry-run` 지원.
- `tests/test_new_task.py`(11) — C3(승인 게이트 미충전)·C2(mat 파싱 형식 유지)가 핵심 가드.
  C7은 생성 직후 `check-limits`·`audit-approvals`가 통과하는지 보는 통합 케이스다.

### Fixed
- **`audit-approvals.py`가 YAML 인라인 주석을 값으로 오독** — 표준 brief 템플릿의
  `write_scope: none    # none | tasks-only | "src/**" 등 패턴` 을 통째로 값으로 읽어
  `INTERNAL_SCOPES`에 안 걸렸고, 결과적으로 **표준 템플릿을 그대로 쓴 모든 brief가
  "외부 쓰기 조건 미충족"으로 오탐**됐다. `target_repo`의 자리표시자
  (`/absolute/path/to/repo`)도 실제 경로로 취급되던 문제 동반 수정.
  위 C7 통합 케이스가 잡았다 — 단위 테스트만으로는 안 보이던 결함이다.
  회귀 가드: `tests/test_audit.py` C7b.

### Changed
- CLAUDE.md Task Lifecycle 1번을 스캐폴더 사용으로 갱신(3 flavor).

## [3.5.0-ebiz.6] - 2026-08-13

CI를 실제로 초록불로 만든 릴리스. 도입 후 4런 연속 실패하고 있었고, 원인 2건 모두
**로컬 1개 OS에서는 원리적으로 재현 불가능한** 결함이었다.

### Fixed
- **ZIP 평탄화 배포에서 `validate.py`가 모듈 로드 단계에서 사망** (CI ubuntu, `package` 잡).
  모듈 상수 `CATALOG_ROOT = SCRIPT_DIR.parents[4]`가 IndexError. `build_zip.py`는
  generator/ 내용을 ZIP 루트로 평탄화하므로 추출 후 경로가 `/tmp/xxx/`처럼 얕아진다.
  ZIP에서 쓰지도 않는 `--repo-check` 상수 하나 때문에 flavor 검사까지 못 돌았다.
  → `_ancestor()` 헬퍼(깊이 부족 시 최상위, 루트 경로도 처리).
  Windows 임시경로·macOS `/var/folders/…`는 깊어서 안 보이고 **리눅스 `/tmp`에서만** 터진다.
- **Python 테스트 5개 전량이 첫 print에서 크래시** (CI windows, `verify` 잡).
  테스트가 결과를 한글로 출력하는데 CI windows-latest는 **영문 로케일(cp1252)** 이라
  `UnicodeEncodeError`. 테스트 내용과 무관하게 스위트가 전멸했다.
  생성기·도구 스크립트 7종에는 UTF-8 고정을 넣었으면서 **테스트 파일 자신들에는
  빠뜨린** 누락. 한국어 Windows(cp949)는 한글을 인코딩할 수 있어 로컬에서 끝내 재현 안 됨.
  → `tests/_utf8.py` 공유 모듈 + 각 테스트 `import _utf8`.
  로컬 재현법: `PYTHONIOENCODING=cp1252 bash tests/run.sh`

### Added
- `tests/test_generate.py::shallow_path_check` — 얕은 경로에서 validate 상수 계산 회귀 가드.
  (이 테스트가 작성 직후 내 첫 수정의 버그 — 루트 경로에서 `parents[-1]` 재-IndexError — 를 잡았다.)

## [3.5.0-ebiz.5] - 2026-08-13

gemini(agy) 워커 **실호출 검증 완료** — 그 과정에서 조용한 결함 1건 발견·수정.

### Fixed
- **envelope의 `model` 라벨이 실제 호출 모델과 달랐다.** 디스패처 정본 경로로 gemini를
  호출하면 envelope는 `gemini-3.1-pro-high`를 보고하는데 실제로는 **Gemini 3.6 Flash**가
  답했다. `status=ok`·`exit 0`이라 어디에도 이상 신호가 없어, `log.md`에 사실과 다른
  모델명이 계속 기록되는 상태였다.
  - 원인: `backends.json`의 `.model`이 **envelope 라벨로만** 쓰이고 agy에 전달되지 않았다.
    `--model` 없이 부르면 agy 전역 설정이 이긴다.
  - 수정: 디스패처에 **`@model` 치환** 추가(레코드 `.model` → 인자) +
    gemini `args_template`을 `["--model","@model","--prompt","@brief_content"]`로
    (claude·codex flavor. antigravity는 gemini 워커가 없어 해당 없음).
    모델명을 args에 직접 적지 않는다 — 정본이 둘이 되면 다시 갈라진다.
  - 회귀 가드: `tests/dispatcher/test_model_pin.sh`(4케이스).
  - 재검증: envelope `gemini-3.1-pro-high` ↔ 실제 응답 "Gemini 3.1 Pro" 일치 확인.

### Changed
- **routing.md의 낡은 전제 교정**(claude·codex). "agy 모델은 전역·계정단위라 per-call 핀
  불가"는 **틀렸음이 실증됐다** — agy 1.1.12에는 `--model` 플래그가 있다(1.0.x 기준 서술이
  남아 있었음). 빠른 경로 모델도 `agy models`로 확인하도록 변경: 문서의 `gemini-3-flash`는
  이미 목록에 없고 `3.6-flash`/`3.5-flash` 세대로 바뀌었다.
- `_shared/learnings.md`에 [2026-08-13] 항목 추가.

### 검증된 것 (KNOWN_ISSUES KI-3 잔여 항목 해소)
- **gemini 워커 Windows 실호출 성공** — `agy` 1.1.12(네이티브 Windows), 디스패처 경유,
  `status=ok`, 9~13초, `fallback_used=false`. 오래 미검증으로 남아 있던 항목이다.
- agy 인증·모델 목록 조회 정상(`gemini-3.1-pro-high` 실재 확인).

## [3.5.0-ebiz.4] - 2026-08-13

팀 배포 전 정합성·온보딩 도구 묶음. 전부 3 flavor 공용이고 외부 호출 0건.

### Added
- **`_shared/check-limits.py`** — brief(≤1200자/240단어)·context(≤1500자/300단어) 한도를
  **실제로** 검사. 지금까지 INV4가 한 일은 "문서에 `1200자`라는 글자가 있는가" 확인뿐이라
  3000자 brief도 전부 PASS했다(강제하지 않는 숫자 = 거짓 안전신호).
  측정은 **오케스트레이터가 쓴 내용**만 — 안내 주석과 고정 규약 블록(175자 상수)은
  줄일 수 없으므로 제외. 한글은 글자수·영문은 단어수 기준.
- **`_shared/doctor.py`** — 환경 진단 6종(핵심 도구·git·backends.json·워커 백엔드·
  MCP 설정·디스패처 드라이런). `backends.json`이 선언한 워커만 검사하므로 flavor 무관.
  드라이런은 `--merged-preview`라 모델 호출 0건.
- **`_templates/smoke-task.md`** — 신규 팀원 온보딩 1회용 절차(무료 doctor → 유료 스모크).
  `tasks/`에 두지 못하는 이유: 생성기가 그 폴더를 사용자 데이터로 보고 복사하지 않는다.
- **`tests/test_limits.py`(7) · `tests/test_doctor.py`(5)** — CI 3-OS에서 상시 검증.

### Fixed
- **doctor 초안의 Windows 경로 결함 2건** (작성 중 발견·수정, CI 매트릭스가 잡을 부류):
  - `bash`를 이름으로 호출하면 Windows에서 **System32의 WSL bash로 해석**될 수 있고,
    WSL bash는 `C:/…` 경로를 못 읽어 디스패처 드라이런이 exit 127로 죽었다.
    `shutil.which("bash")`로 고정 + 경로는 `as_posix()`로 전달.
  - `codex --version`이 이름 호출로는 실패(확장자 없는 셸 스크립트) → `which` 결과 사용.

### Changed
- CLAUDE.md Context Rules에 한도 검사 실행법, AGENTS.md(codex·antigravity)에 doctor·
  check-limits 안내 추가.

### 알려진 긴장 (미해결)
- `_templates/worker-brief.md` **원문은 1455자/256단어로 문서화된 한도를 넘는다.**
  템플릿은 brief가 아니라 스캐폴드(안내 주석·고정 규약 블록·플레이스홀더 포함)이므로
  검사기는 가변부만 잰다. 다만 가변부 기준으로도 빈 스캐폴드가 1162자라 여유가 38자뿐이다.
  codex 계열 brief(Execution Context yaml 필수)는 실사용에서 초과할 가능성이 있다.
  한도 상향이 필요해지면 CLAUDE.md·두 템플릿·INV4·validate C3를 **함께** 고쳐야 한다.

## [3.5.0-ebiz.3] - 2026-08-13

### Added
- **승인 게이트 사후 감사 `_shared/audit-approvals.py`** (3 flavor) — `log.md`의
  `[WORKER_CALL]`을 `task.md`의 `workers_approved`와 대조해 **승인 없이 호출된 워커**를
  찾아낸다. 외부 repo 쓰기 4조건(`target_repo` 명시 + `[APPROVAL]` 기록)도 함께 검사.
  종료코드 0=위반 없음, 1=위반.

  도입 이유: 승인 게이트는 이 시스템의 핵심 안전 속성인데 지금까지 **지켜졌는지 확인할
  수단이 전혀 없었다**(`_shared/`의 유일한 실행 스크립트 `check-invariants.sh`는 문서
  구조만 본다). 혼자 쓸 땐 신뢰로 충분하지만 여러 명이 각자 돌리면 명예 규정이 된다.

  bash가 아니라 Python인 이유: Windows 팀원이 Git Bash 없이 돌릴 수 있어야 하고,
  주석 블록·yaml 목록 파싱은 grep보다 파서가 안전하다.
- **`tests/test_audit.py`** — 7케이스. 그중 C3은 `log.md` 템플릿이 HTML 주석 안에
  `[WORKER_CALL]` 예시를 담고 있어 **주석을 걷어내지 않으면 모든 새 작업이 위반으로
  오탐**되는 것을 막는 회귀 가드다(오탐하는 감사 도구는 즉시 신뢰를 잃는다).
  C4는 승인 목록 2번째 항목 누락(파서 조기종료) 회귀 가드.
- **CLAUDE.md / AGENTS.md** Approval Gate 절에 사후 감사 실행법 추가 (3 flavor).

## [3.5.0-ebiz.2] - 2026-08-13

### Added
- **GitHub Actions CI** (`.github/workflows/ci.yml`) — ubuntu·macOS·windows 3중 매트릭스로
  `tests/run.sh` · `check-invariants.sh`(+`--self-test`) · `validate --repo-check` ·
  sync drift · 개행 LF 고정을 검증. 별도 job에서 ZIP 빌드 자가검증 + 아티팩트 업로드.
  외부·유료 모델 호출 0건. 3 OS인 이유: ebiz.1에서 고친 결함이 전부 한 OS에서만
  터지는 종류(네이티브 jq CRLF, cp949 로케일)였다.
- **README "우리 팀 사용법"** — 3층 라우팅(사내·안정·가변) 진입점, 직군 요청 예시,
  "워커는 직군이 아니라 능력" 원칙. **"업스트림 갱신 받기"** 절차(fetch·merge + 검증 3종).

### Fixed
- **`check-invariants.sh --self-test` 전량 오탐 (비-UTF-8 로케일)** — fixture 변조용 인라인
  Python이 `read_text()`를 인코딩 없이 호출해 한국어 Windows(cp949)에서 죽었다. 치환이
  no-op이 되어 fixture가 무결로 남고, 러너가 정상 PASS하니 self-test는 이를
  "깨뜨렸는데 통과함"으로 읽어 11건 전량 실패했다. `encoding="utf-8"` + `newline="\n"` 명시.
  (macOS·Linux는 로케일이 UTF-8이라 드러나지 않던 결함 — CI 3 OS 매트릭스의 첫 수확.)
- **`sync_claude_template.py`의 `INFRA_PREFIXES`에 `.github/` 추가** — 없으면 CI 워크플로가
  생성물 템플릿(`templates/claude/`)으로 복사된다.

### Changed
- **설치본 README 폴더 트리**(3 flavor)에 `team-routing.md`(사내층)·`capability-profile.md`
  (가변층) 추가 — ebiz.1에서 파일만 넣고 문서화를 빠뜨렸다.
- README의 "v1 → v2 마이그레이션"을 `<details>`로 접음(업스트림 clone 사용자 전용 — 사내 무관).

## [3.5.0-ebiz.1] - 2026-08-12

ebiz 내부 포크의 첫 릴리스. 원작 [netwaif/multi-agent-starter](https://github.com/netwaif/multi-agent-starter) v3.5.0에서 분기.
팀이 **Windows·macOS 혼재**라 Windows를 1급 환경으로 올리는 데 집중했다.

### Fixed
- **디스패처 CRLF 오염 (Windows 차단점)** — 네이티브 Windows `jq`가 stdout에 CRLF를 쓰는데,
  MSYS bash의 `$()`는 끝의 CR만 제거한다. 그 결과 `args_template[]` 등 **다중행 순회에서만**
  `\r`이 남아 cli 워커 인자가 `"exec\r"`·`"--prompt\r"`로 오염 → gemini·codex CLI 폴백이
  전량 실패했다. `call_worker.sh`의 jq 줄단위 순회 3곳에서 CR 제거(3 flavor 동일).
- **`fallback_used` 거짓 보고** — `fallbacks: []` 인 워커(gemini)의 primary 실패가
  "폴백 사용함(true)"으로 기록되던 문제. 폴백이 실제로 envelope를 남겼을 때만 true.
  `[VERIFICATION]` 로그의 사후 진단을 오도하던 값이다.
- **비-UTF-8 로케일에서 생성기 크래시** — 한국어 Windows(cp949)에서 `validate.py`의 em dash
  출력이 `UnicodeEncodeError`로 죽어 `init.py`의 자동 validate가 3 flavor 모두 exit 1이었다.
  `init.py`·`validate.py`·`sync_claude_template.py`의 표준 출력을 UTF-8로 고정하고,
  이를 캡처하는 테스트 2종에 `encoding="utf-8"` 명시(자식·부모가 한 쌍으로만 성립).

### Added
- **`.gitattributes`** (루트 + 3 flavor 템플릿) — `* text=auto eol=lf`. Windows에서 CRLF로
  체크아웃되면 셸 스크립트와 루트↔템플릿 바이트 비교가 깨진다. 워킹트리도 LF로 정규화
  (인덱스가 이미 LF라 내용 diff는 없음).
- **README Windows 팀원 셋업** — Git Bash + jq 요구사항, 도구 확인 스니펫, jq CRLF 함정 주의.

### Changed
- **포크 정체성** — 매니페스트 4종을 `punkyade` / `multiagent-ebiz` / `3.5.0-ebiz.1`로
  (배포처: https://github.com/punkyade/multiagent-ebiz).
  플러그인 디렉토리(`plugins/multi-agent-starter/`)는 그대로 뒀다 — `check-invariants.sh`와
  테스트 2종이 이 경로를 하드코딩하고 있어, 이름만 바꾸는 것으로 충돌 회피 목적은 달성된다.
  `LICENSE`는 원저작권 표시를 유지하고 개변분 표기를 추가(MIT 준수), `NOTICE`에 포크 출처 명시.
- **KI-3 재작성** — "Windows 네이티브 미지원"에서 **"조건부 지원(Git Bash + jq)"** 으로 하향.
  원 항목의 전제("agy는 네이티브 Windows 빌드 미확인")가 실측으로 뒤집혔다 — agy v1.1.12는
  `PE32+ executable for MS Windows x86-64`다. 디스패처 Python 이식은 우선순위에서 내렸다.

### 미검증 (사내 후속)
- gemini 워커 **실호출 스모크** (유료 호출 — 승인 게이트 대상), codex CLI 폴백 실경로.
- macOS에서의 `tests/run.sh` 재확인 — 이번 수정분은 Windows에서만 전량 통과를 확인했다.

## [3.5.0] - 2026-07-24

### Added
- **불변식 자가점검 러너 `_shared/check-invariants.sh`** (3 flavor) — 기존 "grep 출력을 눈으로
  판독"하던 자가점검을 exit-code 판정으로 전환(false PASS 방지). claude flavor는
  `--self-test`(불변식을 하나씩 깨뜨린 fixture가 FAIL하는지 러너 자체 검증) 포함.
  validate C1 필수 파일에 편입.
- **디스패처 payload 동봉** — `call_worker.sh <role> <brief> [payload]` 3번째 인자 +
  `--merged-preview`. gemini 소스 검토의 "brief 인라인 필수"와 brief 불변식(inline 금지·
  1200자)의 모순 해소: 자료는 `sources/gemini-packet.md`로 분리, 디스패처가 결합.

### Fixed
- **backends.json 미소비 선언 제거** — 디스패처가 읽지 않는 `write_policy`·`non_interactive`
  필드를 3 flavor에서 제거(희망사항 config = 거짓 안전신호).
- **claude flavor 1.4.0 / codex flavor 0.5.0 / antigravity flavor 0.3.1** — backends.json 실행계약 모순 교정
  (codex-main sandbox `read-only`→`workspace-write`, CLI 폴백 sandbox·cwd 명시) +
  미구현 gemini api 폴백 비활성(거짓 안전신호 제거) + INV13 신설(claude flavor).
  발견 경위: Fable5∥Sol 이중 독립 시스템 리뷰(공통 검출 C1·C3).

### Changed
- **루트↔claude 템플릿 sync 복원** — v3.3이 템플릿에만 넣은 2층 라우팅
  (capability-profile·슬롯 트리)을 루트(유지보수자 본체)에도 승격하고, 반대로 v1.3.0
  개편 때 템플릿에서 누락된 상세 규칙(gemini 이미지/PDF 검수 정본 경로·작업 폴더 분리
  게이트 상세 등)을 템플릿에 복원. design-basis·learnings는 audience 분기로 sync
  제외 명시(D 번호는 루트가 할당·공유: 2층 D9→D12, backends D10→D11 재정렬).
  `sync_claude_template.py` check 기준 drift 0 회복.

## [3.4.0] - 2026-07-19

### Fixed
- **update 모드 지침파일 유실 결함** — `init.py`가 기존 CLAUDE.md/AGENTS.md를 백업 없이
  덮어써 loadout store 조각(`<!-- store:*:start/end -->` 블록)이 유실되던 문제 수정.
  이제 덮어쓰기 전 원문을 `<지침파일>.multiagent-bak`으로 백업하고, store 블록을 새
  지침파일 끝에 재부착한다(`preserve_instruction`). 마커 밖 사용자 수기 내용은 자동
  병합하지 않음 — 백업에서 수동 복원.
- SKILL.md·init.py의 "보존" 안내 문구를 실제 동작(tasks/·_local/ + 지침파일 백업·재부착)에
  맞게 정정.

### Added
- `tests/test_update_preserve.py`에 store 블록 보존·백업 생성 검사 2건.

## [3.3.0] - 2026-07-13

### Added
- **라우팅 2층 분리 (3 flavor 전부)** — `_shared/capability-profile.md` 신설(가변층:
  능력 슬롯→담당 배정, 근거·날짜 필수·이력 append-only). routing.md는 안정층(작업 유형→
  능력 슬롯 strategist·engineer·computer-use·reviewer·multimodal)으로 재편 — 신모델 출시·
  판정 변경 시 프로필만 갱신하고 시스템 파일은 불변. 초기 배정 근거 = 2026-07-13 외부 리뷰
  10건 종합 판정(설계·디자인·전략·글쓰기 = Claude 우위 / 대규모 구현·테스트·브라우저 조작·
  비용·속도 = GPT 우위). 각 flavor design-basis에 결정 기록(claude D9, codex D8, antigravity D8).
- **computer-use 슬롯 신설** — 브라우저 조작·도구 워크플로우 자동화의 독립 라우팅 분기.
- **validate C5b** — 2층 라우팅 불변식(routing→profile 참조 + 프로필 슬롯 5종), C1에
  `_shared/capability-profile.md` 추가.

### Fixed
- **`.codex-plugin/plugin.json` 버전 방치(3.1.0) 교정** — 3.2.0 릴리스 시 범프 누락으로
  repo-check R2(version 일관)가 FAIL이던 기존 결함 해소. 3종 매니페스트 3.3.0 일괄.

## [3.2.0] - 2026-07-10

### Removed
- **`generator/guard/` 가드 자산 제거** — v3.0.0에 예정했던 이관의 완료.
  [loadout](https://github.com/netwaif/loadout) 0.4.0이 codex점을 열면서(`--flavor codex`)
  codex 워처(`codex_goal_watch.mjs`)·README 정본이 loadout guard 품목(`files.codex/`)으로
  이관됐다(claude Stop 훅 정본은 이미 loadout `hook.json`). 가드 설치·검증은 전부 loadout 소관:
  설치=`store.py --pick guard [--flavor codex]`, 검증=`store.py --doctor`(정본 대조).
- **validate C12(요금가드 배선 사후검증) 제거** — 대조할 정본이 loadout으로 갔으므로
  검증 소관도 loadout doctor로 이관. tests의 가드 기본부재 단언은 유지.

## [3.1.0] - 2026-07-08

### Removed
- **`skills/knot/` 능동 스킬 제거** — knot 능동 스킬(save/ingest/query/lint)은
  [netwaif/knot](https://github.com/netwaif/knot) 자체 플러그인(1.0.0)이 배포한다
  (마켓플레이스에 `netwaif/knot` 추가). v3.0.0 knot 이관의 마무리 — 스킬 정본·배포처 단일화.
  - **존치**: `knot_block.md` 정본 · `knot-vault/` 스캐폴드 · validate C10(관리블록 사후 검증).
  - v2.x 기존 설치자는 영향 없음. 플러그인 업데이트 시에만 스킬이 빠지며, knot 마켓 추가로 대체.

## [3.0.0] - 2026-07-06

### Removed (BREAKING)
- **`--with-knot` / `--with-guard` 옵트인 제거** — knot·요금가드의 *설치*는
  [loadout](https://github.com/netwaif/loadout) 카탈로그("CLAUDE.md 구성 골라 담아줘")
  담당으로 이관. configure-multiagent 절차의 knot·가드 질문/후속 안내 단계도 제거.
  - **존치**: `knot` 능동 스킬(플러그인 스킬, save/ingest/query/lint) ·
    `knot_block.md`/`knot-vault/` 스캐폴드 · `guard/`(codex 워처 + Stop 훅 정본) ·
    validate C10·C12(사후 검증 — loadout 설치물에도 유효).
  - codex 가드 워처 설치는 `generator/guard/README.md`의 수동 복사(loadout codex점 전까지).
  - **기존 설치자 영향 없음** — 기본 생성물 무변경, 이미 주입된 관리블록·훅은 그대로 동작.

## [2.2.2] - 2026-07-04

### Fixed
- **gemini 워커 폴백 실패 사유 유실** — `call_worker.sh`가 api 폴백의 필수 env
  (`GEMINI_API_KEY`) 부재 시 `die`로 죽어 실패 사유가 최종 envelope에 남지 않던 문제.
  에러 envelope(`stderr_sanitized`)로 반환하도록 수정 + 호출 시작 시 폴백 불가 사전 경고 추가.
  템플릿 3종(claude 1.2.2 / codex 0.3.2 / antigravity 0.2.2) 동일 반영.
  기존 설치자는 `_shared/adapters/call_worker.sh`를 새 버전으로 교체하면 된다.

### Changed
- **routing.md gemini 규칙 보강**(claude/codex flavor) — 소스·다중파일 검토는 brief에
  스니펫 **인라인 필수**(디렉토리 순회 시 agy 헤드리스 300s 타임아웃 실측), 폴백 조건
  (`GEMINI_API_KEY`) 명문화, 시간 제한 작업 전 경량 스모크 권장.

## [2.2.1] - 2026-07-03

### Fixed
- **gemini(agy) 워커 프롬프트 미전달** — Antigravity CLI 1.0.16에서 `-p` 단축 플래그 제거로
  backends.json `args_template`의 프롬프트가 조용히 무시되던 문제(모델 미호출·사용량 0).
  템플릿 3종(claude 1.2.1 / codex 0.3.1 / antigravity 0.2.1) 전부 `--prompt`로 교정.
  기존 설치자는 `_shared/backends.json`의 `"-p"`를 `"--prompt"`로 한 줄 수정하면 된다.
- task.md 작성 규칙 명문화(CLAUDE.md) — `## 메타` yaml 펜스 형식 강제(frontmatter 금지),
  mat 모니터 파싱 정본과 일치.

## [2.2.0] - 2026-06-28

### Added
- **opt-in goal 요금가드(`--with-guard`)** — `/goal` 자율 루프가 주간 사용량 한도에 닿으면 자동
  정지하는 벤더중립 안전장치. 기본 미설치. **정책=`coach`(usage-coach, codexbar 의존) 단일정본,
  하네스=배선만**. flavor별 주입: claude=`.claude/settings.json` Stop훅(`coach --hook`, inline
  `command -v coach … || true` fail-open), codex=`_shared/guard/` 워처(loopback WebSocket `ws://127.0.0.1:47931`→
  `thread/loaded/list`→`thread/goal/clear`). antigravity는 `/goal` 자율 루프 부재로 미지원(다음 버전).
  런타임 on/off=`coach guard on/off/status`. 미설치·플래그 off·조회실패는 모두 fail-open. generator
  결정성 불변(init.py 고정 정본 복사·병합만, knot `--with-knot`과 동형). `configure-multiagent` SKILL에
  opt-in 질문(4b)·후속안내(7b) 추가. 회귀보호=validate **C12** + test_generate guard_checks(3 flavor ×
  주입·멱등·기본부재). 설계근거 `_shared/design-basis.md` **D10**. coach 정책층 = 별도 핸드오프
  (usage-coach repo, tasks/harness-quota-guard/workers/handoff-usage-coach.md). (tasks/harness-quota-guard/)

## [2.1.1] - 2026-06-25

### Fixed
- **오케스트레이터가 기존 작업의 후속·핸드오프를 사용자 확인 없이 새 task 폴더로 분리하던 문제.**
  `_shared/orchestrator-rules.md` §3에 "새 작업 폴더 생성 게이트" 추가 — 분리 전 사용자 확인 강제 +
  분리 시 parent·context 필독입력·메모리 포인터 연결고리. CLAUDE.md Task Lifecycle·`_templates/task-folder.md`에
  포인터, generator 템플릿 3종(claude/codex/antigravity)에 전파. codex-critic/gemini 검수 반영
  (확인 절차와 연결고리 분리·예외를 '독립 신규작업'으로 한정·경로 불문). 회귀 GREEN(test_generate all pass, INV8/11a).

## [2.1.0] - 2026-06-17

매뉴얼 v2.1과 정렬. (이전까지 `plugin.json`이 2.0.0에 머물러 배포 매뉴얼 2.1과 버전이 어긋나 있던 것을 동기화.)

### Added
- **knot 배포(P1~P6)** — 벤더중립 standalone 지식 vault. 능동층=플러그인 최상위 스킬(claude·codex·agy
  네이티브 로드), 자동층=opt-in `--with-knot` 관리블록 주입(멱등). vault 경로=env `$KNOT_VAULT` +
  `~/.config/knot/vault` 파일 fallback. `configure-multiagent`에 설치 제안 진입점.

### Fixed
- knot `save` verb가 inbox 파일을 커밋(save↔ingest 갭). vault 게이트 env→포인터파일 fallback
  (GUI 호스트앱 진입장벽 제거). agy 능동 스킬을 플러그인 최상위로 승격(네이티브 로드).

## [2.0.0] - 미배포 (PR 머지 시 태깅)

**Breaking**: 배포 방식을 "clone → 루트 파일 그대로 사용"에서 **생성기 + 플러그인**으로
전환. 이제 repo는 시스템 그 자체가 아니라 시스템을 만들어 주는 도구다.

### Changed
- **지침파일 Task Lifecycle에 워커 산출물 경로 명시 (claude/CLAUDE.md, codex·antigravity/AGENTS.md).**
  기존엔 "brief.md/result.md 작성"이라고만 해 경로가 모호 → 오케스트레이터(특히 Gemini)가
  `tasks/<task>/workers/<role>/` 대신 `<role>_brief.md`처럼 평탄화해서 모니터 도구(mat)가
  워커를 못 읽는 문제. 5·6단계를 `tasks/<task>/workers/<role>/{brief,result}.md`로 못박고,
  8단계에 완료 시 `task.md status → done` 갱신을 추가. (제미나이 자가진단으로 원인 확인.)
- **플러그인 레이아웃: 루트 → `plugins/multi-agent-starter/` 하위 폴더로 이동.**
  루트는 마켓 카탈로그(`.claude-plugin/marketplace.json` + 신규 `.agents/plugins/marketplace.json`)만
  둔다. Codex가 로컬 마켓에서 플러그인 source가 repo 루트(`"./"`)인 걸 거부하기 때문
  ([openai/codex#17066](https://github.com/openai/codex/issues/17066) — Claude는 허용, Codex는 거부).
  이 구조로 Claude·Codex 양쪽에서 마켓 등록·설치가 동작함을 검증(`codex plugin add` → installed/enabled).
- **generator를 `skills/configure-multiagent/generator/` 안으로 이동(스킬 자기완결).**
  Antigravity(`agy`)는 플러그인 설치 시 인식하는 컴포넌트(skills/agents/…)만 복사하고 임의 폴더
  (`generator/`)는 버린다 → 설치돼도 스킬이 부를 생성기가 없어 동작 불가였음. 스킬 폴더 안에 두면
  스킬과 함께 복사된다. **3호스트 검증 완료**: `agy plugin install <경로>` / `codex plugin add` 모두
  설치 위치에 skill+generator 동거 확인, `tests/run.sh`·`build_zip` 3-flavor 자가검증 PASS.

### Added
- `generator/init.py` — flavor·대상 지정 결정적 생성기 (tasks/·_local/ 보존, dry-run, `--yes`, guard).
- `generator/validate.py` — flavor별 불변식 자가점검 (claude 10 / codex 11 / antigravity 12), `init`이 설치 후 자동 호출.
- `generator/build_zip.py` — 플러그인 없이 쓰는 자립형 ZIP(run.command/run.bat + 한글 README), 재현가능 빌드.
- `generator/templates/{claude,codex,antigravity}/` — 세 flavor 정본 템플릿.
- **Antigravity flavor** — Antigravity(Gemini 3.1 Pro High)를 오케스트레이터로, claude-main·codex-main·codex-critic을 워커로. 멀티모달·긴 문서는 오케스트레이터가 직접(동일 벤더 gemini 워커 없음).
- **연결 어댑터 레이어** (vendor/model-free 하네스의 토대):
  - `_shared/backends.json` — 역할→모델→연결방식(native·mcp·cli·api) 레지스트리(머신 검증되는 단일 진실원).
  - `_shared/adapters/call_worker.sh` — cli/api 디스패처(allowlist·옵션인젝션 방어·결과 envelope JSON·폴백·타임아웃). native/mcp는 오케스트레이터 직접 호출.
  - `_shared/adapters/_run.py` — 결정적 타임아웃 러너(coreutils timeout 부재 시 폴백, 프로세스그룹 TERM→KILL, 초과 시 124).
- gemini 백엔드를 폐기된 프록시에서 **Antigravity CLI `agy`**(gemini-3.1-pro-high)로 이전. API 연결은 슬롯으로 예약.
- `tests/` — 외부·유료 모델 호출 없는 결정적 회귀 테스트(`run.sh`): 3 flavor 생성·update 보존·디스패처 폴백/타임아웃/가드.
- `docs/ACCEPTANCE.md` — 3호스트(claude·codex·antigravity) 수용 체크리스트 + 4층 신뢰모델 + 테스트 시나리오 S1~S10 + 사인오프 표.
- `generator/sync_claude_template.py` — 루트(Claude 정본)에서 `templates/claude` 재생성 + drift 가드.
- `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json` — Claude Code·Codex 플러그인 매니페스트.
- `skills/configure-multiagent/` — "멀티 에이전트 시스템 구성해줘" front door.
- `LICENSE` — MIT.
- **카파시 4원칙(운영 원칙) 도입** — 3 flavor 지침파일(claude/CLAUDE.md, codex·antigravity/AGENTS.md)에
  "운영 원칙 (Operating Principles)" 섹션(verbatim 차용), `_templates/worker-brief.md`에 워커 번역형
  고정 블록("Worker 행동 규약"). 층별 적용 근거는 각 flavor design-basis(D8/D7/D7)·invariant(INV12/INV11/INV11).
  출처: multica-ai/andrej-karpathy-skills (MIT) — 표기 정본 `NOTICE`(루트 + 3 flavor).

### Changed
- 배포: clone → 플러그인(`/plugins` 마켓플레이스) / ZIP fallback.
- 루트 문서(README/CHANGELOG/KNOWN_ISSUES)를 repo front-page·패키지 이력으로 분리. 설치된 타깃용 동명 문서는 `templates/` 에 독립 정본으로 둔다.

### Fixed
- 디스패처 타임아웃이 자식 SIGTERM 사망코드(-15)를 반환해 timeout을 error로 오분류하던 버그 — 타임아웃 시 항상 124 반환(`_run.py`, root+템플릿 3벌).

### Note
- 이번 2.0.0은 *배포/패키징* 변경이지 시스템 규칙 변경이 아니다. 설치되는 시스템의 **동작** 버전은 flavor별로 다른 축을 잇는다:
  - `claude` flavor — **1.0.1 라인 계승** (기존 실사용 시스템의 연장; `generator/templates/claude/CHANGELOG.md`).
  - `codex` flavor — **0.1.0 신규 파생** (multi-agent-starter의 Codex orchestrator 버전; `generator/templates/codex/CHANGELOG.md`).
  - `antigravity` flavor — **0.1.0 신규 파생** (Antigravity orchestrator 버전; `generator/templates/antigravity/CHANGELOG.md`).

---

> 아래 1.0.x는 generator 전환 이전, **repo가 곧 시스템**이던 시기의 릴리스 이력이다.
> 설치 시스템 동작 이력은 이후 템플릿 CHANGELOG에서 이어진다.

## [1.0.1] - 2026-06-01

모델·추론 정책 표기 정리(문서 patch). 동작 변경 없음.

### Changed
- **모델 식별자 별칭화** (`_shared/routing.md`): claude-main을 버전 문자열(`claude-opus-4-7` 등) 대신 별칭 `opus`로 표기 — 모델이 올라가도 문서 갱신 불필요. codex 예시 일반화, gemini는 `gemini-3.1-pro-low` 핀 유지 + "프록시 업그레이드 시에만 갱신" 노트.
- **claude-main 추론 강도(effort) 명문화**: `effort` 핀 없음 → 세션 `/effort` 상속(현 기본). 고정하려면 frontmatter `effort:`.

### Added
- **design-basis D7**: 모델 식별자 표기 정책(별칭 원칙 / gemini 핀 예외·세부는 D4 정본 / effort 비대칭 근거).

### Verification
- codex-critic adversarial 검수: 치명 0, 권장 3 반영(잔존 핀 제거 포함). INV9/INV10/INV11 PASS, 회귀 없음.

## [1.0.0] - 2026-06-01

첫 버전 태깅. 기존 실사용 시스템을 1.0.0 기준선으로 고정하고, harness(revfactory) 참고 버전 업그레이드를 함께 반영한다.

### Added
- **작업 재진입 프로토콜** (`_shared/orchestrator-rules.md` §3): 콜드세션이 끝난 작업에 다시 들어갈 때 재정박(re-anchor) → 6분기 판단 → 에러 후 진행. `status↔log 불일치`는 다른 분기보다 먼저 적용하는 정규화 단계로 명시.
- **토폴로지 4패턴표** (`_shared/routing.md`): Pipeline / Fan-out·Fan-in / Expert Pool / Producer-Reviewer + Fan-in 규칙.
- **CLAUDE.md** Task Lifecycle에 재진입 프로토콜 포인터.
- **불변식 INV11** (`_shared/system-invariants.md`): 재진입·토폴로지 규정 자동 자가점검(11a/b/c).
- **design-basis D6**: 4패턴 채택 + Supervisor·Hierarchical Delegation 배제 근거.

### Excluded (설계 결정)
- Supervisor·Hierarchical Delegation 패턴: 단일 orchestrator·worker간 무통신·file-as-memory와 충돌하여 미채택 (근거 D6).

### Baseline (1.0.0 시점 핵심 구조)
- 고정 4-worker pool (claude-main / codex-main / codex-critic / gemini), Claude Code 세션 = orchestrator.
- file-as-memory (런타임 상태 0): task / context / log / brief / result.
- 승인 게이트(`workers_approved`), 외부 쓰기 4조건, progressive disclosure(게이트 로드), 권위 우선순위(CLAUDE.md > routing/approval/orchestrator-rules > 매뉴얼).

### Verification
- 배선(INV11a/b/c) PASS · 회귀 없음, 탁상 분기 커버리지, 실전 콜드세션 3/3 PASS, codex-critic adversarial 리뷰 5 ISSUE 반영.

[2.1.1]: https://github.com/netwaif/multi-agent-starter/releases/tag/v2.1.1
[2.1.0]: https://github.com/netwaif/multi-agent-starter/releases/tag/v2.1.0
[2.0.0]: https://github.com/netwaif/multi-agent-starter/releases/tag/v2.0.0
[1.0.1]: https://github.com/netwaif/multi-agent-starter/releases/tag/v1.0.1
[1.0.0]: https://github.com/netwaif/multi-agent-starter/releases/tag/v1.0.0
