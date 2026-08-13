# Brief — [worker-role] / [작업명]

<!-- HARD LIMIT: 1200자 한글 / 240단어 영문 (wc -m / wc -w). 파일 내용 inline 금지. 경로만 전달. -->
<!-- 프리셋 design-diff 1/3 — 캡처 단계. <...> 자리표시자를 채운 뒤 호출할 것. -->

## Worker 행동 규약 (고정 — 모든 brief에 그대로 유지, 삭제 금지)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: <구현 코드 절대경로 또는 N/A>
write_scope: tasks-only
```

## Objective

구현 화면을 캡처해 `tasks/<task-name>/artifacts/` 에 저장하고, 각 파일의 절대경로를 반환한다.

## Input

```
대상:     <URL 또는 로컬 HTML 절대경로>
화면 목록: <예: 상품목록 / 상세 / 장바구니>
뷰포트:   <예: 1440 / 768 / 375>
```

## Output Format

- 파일 위치: `tasks/<task-name>/workers/<role>/result.md`
- 형식: Markdown. 아래 표를 반드시 포함한다(다음 단계가 이 절대경로를 그대로 쓴다):

```
| 화면 | 뷰포트 | 캡처 절대경로 |
|------|--------|--------------|
```

- 캡처 파일명: `<화면>-<뷰포트>.png`, 저장 위치는 `artifacts/`

## Constraints

- 뷰포트마다 **전체 페이지**(full-page) 캡처. 접힌 영역 누락 금지
- 로딩·애니메이션이 끝난 뒤 캡처. 스켈레톤·플레이스홀더 상태 금지
- 캡처만 한다. 코드 수정은 이 단계 범위가 아니다

## Do NOT

- 구현 코드 수정
- 캡처 실패를 성공으로 보고 — 실패 화면은 Issues에 사유와 함께 남긴다
