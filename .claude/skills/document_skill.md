# document_skill

> **트리거**: 사용자가 코드/개념을 **재현 가능한 상태**에 도달했을 때 Claude가 실행.
> 비실시간. 학습 워크플로우 step 7에서 호출.

---

## 1. 상태 판단

| 상태 | 정의 | 처리 |
|------|------|------|
| `unknown` | 개념 처음 접함 | 문서화 X, 설명부터 |
| `shaky` | 설명 들었으나 스스로 못 씀 | 문서화 X, 연습 더 |
| `understood` | 힌트 있으면 구현 가능 | **study 작성** |
| `explainable` | 힌트 없이 구현 + 자기 말로 설명 | **study 확정 + 완료 체크** |

재현 가능성 게이트:
> "이 파일을 닫고 이 코드를 빈 화면에 다시 쓸 수 있나?" → Yes면 문서화.

---

## 2. study 파일 생성/업데이트

### 위치
`study/projects/{project_name}/개념명.md`

### 필수 포함
- **한 줄 요약** — 이게 하는 일
- **왜 필요한가** — "없으면 어떻게 되나?"
- **사용자 코드 인용 + 줄 단위 해설** (교수님 코드 아님)
- **왜 이렇게 작성했는가** — 대안과의 비교
- **다른 코드와의 관계** — 호출/리턴/의존
- **연관 개념 `[[링크]]`** — 최소 2개

### 기존 파일 처리 (재현가능성 체크 우선)
1. 사용자에게: "이 파일만 보고 이 코드 다시 쓸 수 있어?"
2. Yes → 그대로 유지
3. No → 사용자 코드 기반으로 재작성
4. 전부 재작성 금지. 필요한 것만 손댐.

---

## 3. weakness 파일 (조건부)

### 생성 조건 (하나라도 해당)
- 힌트가 2번 이상 필요했다
- 틀린 답을 먼저 말했다
- 같은 개념을 두 번째 막혔다

### 전제
**study 파일이 반드시 존재해야 한다.** 없으면 study 먼저.

### 위치
`study/약점노트/active/w_개념명.md`  ← FLAT (L 서브폴더 없음, level은 frontmatter 소유)

### frontmatter (SM-2 유지)
```yaml
---
concept: "개념 이름"
subject: "{project_name}"
level: 3
current_streak: 0
last_reviewed: YYYY-MM-DD
next_review: YYYY-MM-DD
review_count: 0
history: []                  # perfect / hint1 / hint2 / hint3 / fail
mastered: false
---
```

### 본문 구조 (새 포맷)
```markdown
# 개념 이름

## 한 줄 요약

## 내 답변
> 사용자가 처음 답한 내용

## 실제 정답
> 자세한 설명은 [[개념명]] 참조

## 차이 (핵심)
- 틀린 부분
- 빠진 부분
- 잘못 이해한 부분

## 피드백
- 왜 틀렸는지
- 어떤 사고 방식으로 접근해야 하는지

## 트리거
> 이 상황이 나오면 이 개념을 떠올려라

## 내 말로 다시 설명
> (복습 시 작성)
```

---

## 4. SM-2 복습 로직

### 기본 간격

| 레벨 | 1회 | 2회 | 3회 | 4회 | 5회 |
|------|-----|-----|-----|-----|-----|
| L4 완전모름 | 1일 | 3일 | 7일 | 14일 | 30일 |
| L3 어려움 | 2일 | 5일 | 12일 | 25일 | 50일 |
| L2 보통 | 3일 | 7일 | 16일 | 35일 | — |
| L1 쉬움 | 5일 | 12일 | 28일 | — | — |

### 정답 품질 조정

| 결과 | 배율 |
|------|------|
| 힌트 없이 정답 (perfect) | × 2.5 |
| 힌트 1번 후 정답 | × 1.5 |
| 힌트 2번 후 정답 | × 1.0 |
| 힌트 3번 후 정답 | × 0.5 (최소 1일) |
| 끝까지 못맞춤 (fail) | 리셋 → 1일 |

### 마스터
힌트 없이 3번 연속 정답 → `mastered/`로 이동. 30일마다 확인.

### 맞춘 것도 기록 (L1)
힌트 없이 바로 맞춘 개념도 L1으로 기록. 장기 기억용, 간격만 길게.

---

## 5. Context Linking

모든 study/weakness 파일은 **최소 2개의 `[[연관 개념]]`** 역참조를 포함.

- weakness → `[[study 파일]]`로 "실제 정답" 연결 **필수**
- study → 관련 weakness 역참조 가능

예: `weakness/DataLoader.md` 안에서 "실제 정답 → [[Dataset_DataLoader]] 참조"

---

## 6. Feedback Loop — 다음 행동 1개만

document_skill 실행 후 **한 가지**만 제안:
- "다음은 X를 구현해보자" 혹은
- "내일 복습 대기: [개념]" 혹은
- "이 개념과 짝이 되는 Y가 빠졌다 — 다음에 다루자"

**여러 제안 금지.** 하나만.

---

## 7. 충돌 해결

동일 개념에 study와 weakness가 모두 있을 때:
- **weakness 우선** (이 사용자는 이걸 틀렸다는 사실 반영)
- study는 weakness의 "실제 정답 → [[X]] 참조" 링크 타겟 역할

---

## 8. 실행 체크리스트

document_skill 호출 시:

- [ ] 상태 판단 (unknown/shaky/understood/explainable)
- [ ] study 파일: 신규 생성 or 재현가능성 체크 후 유지/재작성
- [ ] weakness 생성 조건 확인 → 필요시 생성 (study 존재 확인 선행)
- [ ] `[[연관 개념]]` 최소 2개 포함
- [ ] `study/projects/{project_name}/README.md` 생성(없으면) 또는 업데이트
- [ ] 구현 체크 업데이트: `projects/{project_name}/code/` 코드 파일 읽고 구현 여부 판단
      기준: README 각 `- [ ]` 항목 텍스트 기준으로 코드 확인
      미완료: 코드 없음 / pass·...·TODO·raise NotImplementedError stub / 본문 비어있음
- [ ] 개념 파일 목록 갱신
- [ ] 신규 프로젝트 README 생성 시 → `study/README.md` 목록에 행 추가
- [ ] `약점노트/README.md` 업데이트 (weakness 생성/복습 반영)
      행 양식: `| [[w_개념명\|표시명]] | {project_name} | L{1-4} | {연속정답} | {next_review} |`
- [ ] **[Ingest 프로토콜 — CRITICAL] `study/index.md` 행 추가:**
      `| [[개념명]] | {타입} | {한 줄 요약} | {약점 링크 or -} |`
      index.md 없으면 신규 생성 (zero-state 대응)
- [ ] **[Ingest 프로토콜 — CRITICAL] `study/log.md` append:**
      `## [YYYY-MM-DD] ingest | 개념명 (프로젝트)`
      log.md 없으면 신규 생성 (zero-state 대응)
- [ ] 다음 행동 1개 제안

---

## 9. 프로젝트 README 관리

### 생성 조건
`study/projects/{project_name}/README.md`가 없을 때 → document_skill 최초 실행 시 자동 생성

생성 직후 → `study/README.md` 프로젝트 목록에 행 추가:
```
| {project_name} | {한 줄 주제} | [[projects/{project_name}/README]] | 진행 중 |
```

### 구현 가이드 — 플랜모드 필수

README의 **구현 순서/단계** 섹션을 신규 작성하거나 변경할 때:

1. **플랜모드 진입** (EnterPlanMode)
2. 구현 단계 계획 작성 후 사용자 수락 대기
3. 수락 시에만 README에 반영

> 구현 가이드 없이 구현 체크만 업데이트하는 경우는 플랜모드 불필요

### README 섹션 순서

```
구현 순서 → 막혔을 때 참조 매핑 → 개념 파일 현황
```

### 막혔을 때 참조 매핑 — 링크 규칙

- 볼 파일 열: 파일 존재 시 `[[파일명]]`, 미작성 시 `파일명.md 📝`

### 기본 내용

```markdown
## 개념 파일 현황
| 파일 | 상태 |
|------|------|
> ✅ = 파일 존재 / 📝 = 미작성
```

### 업데이트 시점

document_skill 실행 시마다:
- `projects/{project_name}/code/` 내 코드 파일 직접 읽기
- 코드에 해당 단계 구현 여부를 확인해서 구현 순서 체크 상태 결정
- 개념 파일 목록 갱신

---

## 10. 알림 규칙

weakness 생성/업데이트 후 반드시 알린다:
> "약점노트 L[X]에 저장했어. 다음 복습일: [날짜]"
