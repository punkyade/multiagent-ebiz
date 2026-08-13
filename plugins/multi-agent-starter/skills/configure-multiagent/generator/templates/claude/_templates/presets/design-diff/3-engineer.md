# Brief — [worker-role] / [작업명]

<!-- HARD LIMIT: 1200자 한글 / 240단어 영문 (wc -m / wc -w). 파일 내용 inline 금지. 경로만 전달. -->
<!-- 프리셋 design-diff 3/3 — 수정 단계. 외부 repo 쓰기는 4조건 충족 필수. -->

## Worker 행동 규약 (고정 — 모든 brief에 그대로 유지, 삭제 금지)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: <수정 대상 repo 절대경로>
write_scope: tasks-only
# 외부 repo 직접 수정이 필요하면 패턴으로 바꾸고(예: "src/**") task.md 승인 + log.md
# [APPROVAL] 기록까지 4조건을 채운다. 미충족 시 diff·patch 산출만 할 것.
```

## Objective

대조 결과의 차이 항목을 수정한다. **심각도 `높음`·`보통`만** 대상이다.

## Input

```
대조 결과: tasks/<task-name>/workers/<multimodal-role>/result.md
수정 대상: <파일 경로 목록>
```

## Output Format

- 파일 위치: `tasks/<task-name>/workers/<role>/result.md`
- 형식: Markdown. 수정 항목별로 `대조표의 위치 → 변경 파일·라인 → 변경 내용` 한 줄씩
- `write_scope`가 `tasks-only`면 코드는 **diff 형식**으로만 산출 (사용자가 직접 적용)

## Constraints

- 대조표에 없는 것은 고치지 않는다. 눈에 띄는 다른 문제는 Issues에 적기만 할 것
- 심각도 `낮음`(1~2px·미세 색차)은 건드리지 않는다 — 비용 대비 효과가 낮고 회귀 위험만 는다
- 기존 클래스·변수 명명과 파일 구조를 따른다

## Do NOT

- 리팩토링·구조 개선·의존성 추가
- 시안에 없는 요소를 임의 추가
