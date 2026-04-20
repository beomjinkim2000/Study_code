# CLAUDE.md — 실행 워크플로우

## ⚠️ 필수 선행 규칙 — 모든 응답 전 실행
**사용자 첫 메시지에 응답하기 전, 반드시 §1 세션 시작 워크플로우를 완료하라.**
건너뛰거나 지연 금지. 어떤 질문이 와도 워크플로우 먼저.

---

## 자동 로드 (매 세션 guardrail — harness 패턴)
@study/약점노트/README.md
@study/session_queue.md
@.claude/docs/ARCHITECTURE.md
@.claude/rules/wiki_schema.md

---

## 아키텍처 규칙

- CRITICAL: document_skill 실행 시 반드시 study/index.md 행 추가 + study/log.md append (Ingest 프로토콜). 이유: 생략하면 wiki가 누적되지 않음.
- CRITICAL: projects/{name}/ (Raw layer) 파일은 절대 수정 금지. 읽기 전용. 이유: 학생 원본 코드 보호.
- CRITICAL: [[링크]] 대상 파일이 존재하지 않으면 링크 금지. 이유: orphan link → /lint 오류 발생.
- 약점노트 경로: study/약점노트/active/w_*.md (L 서브폴더 없음 — level은 frontmatter 소유)
- 모든 wiki 링크: [[파일명]] 형식만 허용 (경로·확장자 없음)

---

## 프로젝트 감지 (세션 시작 시 1회)

```
1. session_queue 항목에서 "{project_name}/개념명" 패턴 추출
2. queue 비어있으면 → study/projects/ 목록 중 최근 수정 폴더
3. 감지된 project_name으로 study/projects/{project_name}/README.md 읽기
```

> 이후 문서 전체의 {project_name}은 여기서 결정된 값을 사용한다.

---

> **기준**: 코드를 보지 않고 다시 작성 가능하면 완료. 아니면 진행 중.
> **교육 참조기준**: `.claude/rules/claude-teach.md`

---

## 시스템 역할 (빠른 참조)

| 파일 | 역할 |
|------|------|
| `session_queue.md` | 미완료 상태 추적 |
| `study/projects/{project_name}/README.md` | 구현 가이드 — 다음 할 것 |
| `study/projects/{project_name}/scaffolds/` | 실행 가능한 코드 연습 파일 (NN_이름.py) |
| `study/index.md` | Wiki 전체 카탈로그 — query 시 먼저 읽음 |
| `study/log.md` | append-only 활동 로그 (`grep "^## "` 파싱 가능) |
| `study/state.json` | 스크립트용 머신 상태 (bootstrap/lint 자동 업데이트) |
| `study/개념.md` | 개념 정확한 구조 |
| `약점노트/active/w_개념.md` | SM-2 사고 교정 |
| `학습인사이트.md` | 메타 학습 현재 스냅샷 (세션 종료 시 덮어쓰기) |
| `학습인사이트_log/` | 날짜별 성장 로그 누적 |
| `.claude/docs/ARCHITECTURE.md` | 3-layer 구조 설계 문서 (guardrail — 매 세션 자동 로드) |
| `.claude/rules/wiki_schema.md` | 페이지 타입·Ingest/Lint 규칙 (guardrail — 매 세션 자동 로드) |
| `session_control_skill.md` | 세션 출력 형식·선택지·흐름 제어 규칙 |
| `scripts/sm2.py` | SM-2 계산 모듈 — wiki_validate·tutor_validate가 import |
| `scripts/wiki_lint.py` | wiki 구조 검증 (Stop hook 자동 실행) |
| `scripts/wiki_validate.py` | 페이지 콘텐츠 스키마 검증 |
| `scripts/tutor_validate.py` | 튜터 워크플로우 검증 (queue·인사이트·SM-2) |
| `scripts/dl_coach_validate.py` | DL 코치 실험 로그 형식 검증 |

---

## 3-Layer Wiki 구조 (llm-wiki 패턴)

```
Layer 1: projects/{name}/        ← Raw (불변, 읽기 전용)
Layer 2: study/                  ← Wiki (LLM 소유·관리, Obsidian에서 열람)
Layer 3: .claude/                ← Schema (규칙·워크플로우 정의)
```

**Wiki 운영 3가지 (wiki_schema.md 상세 규칙 참조)**:
- **Ingest** (document_skill): 새 개념 → 개념 페이지 + index.md 행 + log.md 항목 + 약점노트
- **Query**: index.md 먼저 → 관련 페이지 드릴다운 → 좋은 답변은 새 페이지 저장 제안
- **Lint** (/lint 호출 또는 Stop hook 자동): 고아 링크·SM-2 만료·index 누락 점검

---

## session_queue 시스템

- queue는 할 일 목록이 아니라 현재 학습 상태 추적이다

상태 (3가지만):
```
이해중 → 구현중 → 검증중
```

기본 흐름:
- 구현 필요 개념: 코드 시작 → 구현중 → 코드 완성 → 검증중
- 구현 불필요 개념: 이해 확인 완료 → 검증중
- 검증중 → 코드 재작성 가능 + 개념 설명 가능 → queue 제거 + document_skill

상세 규칙:
→ `.claude/skills/queue_skill.md` 참조

---

## 1. 세션 시작

```
[가드레일 확인 — 자동 로드됨]:
  .claude/docs/ARCHITECTURE.md — 3-layer 구조 숙지 (매 세션 자동)
  .claude/rules/wiki_schema.md — Ingest/Query/Lint 규칙 숙지 (매 세션 자동)

study/학습인사이트.md 읽기
  → 현재 수준 판단 (이해 / 구현 / 설명)
  → 수준에 따라 설명 깊이·힌트 수준·구현 유도 강도 조절

session_queue.md 읽기
  → 미완료 항목 있음?
      Yes → 해당 항목부터 시작
      No  → 다음

약점노트/README.md 읽기
  → 복습 대기(next_review <= 오늘) 있음?
      Yes → 복습 먼저
      No  → 다음

study/projects/{project_name}/README.md 읽기
  → 구현 체크 미완료 항목 확인 → 그것부터

[선택] study/index.md:
  → 현재 개념 목록 파악 — query 발생 시 진입점으로 활용
```

출력 형식·선택지·흐름 제어·종료 방식:
→ `.claude/skills/session_control_skill.md` 참조

---

## 2. 문제/개념 발생 시

```
1. session_queue 처리 (.claude/skills/queue_skill.md 참조):
   - queue에 없으면 → 이해중으로 추가
   - queue에 있으면 → 상태 변경 없음 (§3/§4에서 처리)
   형식: - [ ] {project_name}/개념명 (상태: 이해중|구현중|검증중)

2. 개념 질문인가, 코드 문제인가?

판단 기준:

[코드 문제]
- "구현", "작성", "만들어", "동작", "에러"
- 실행 결과가 중요

[개념 문제]
- "왜", "차이", "의미", "원리"
- 설명이 중요

예외:
- 개념 질문이지만 구현이 핵심인 경우
  → 개념 확인 후 코드 문제로 전환

   → 개념 질문  : §3으로
   → 코드 문제  : §4로
```

---

## 3. 개념 질문 (Exposition 모드)

```
참조 순서 (Query 프로토콜):
  1. study/index.md — 관련 페이지 있는지 먼저 확인
     있으면 → 해당 파일 읽기, 없으면 아래로
  2. study/projects/{project_name}/개념명.md (직접 경로)
  3. .claude/rules/claude-teach.md §10

행동:
  1. 정답 알면 → 바로 설명 (탐구로 위장 금지)
  2. 이해 확인 질문 1개
  3. 확인 완료 → 개념 유형 판단:
       구현 필요? Yes → session_queue: 이해중 유지, §4로
                 No  → session_queue: 검증중으로 상태 변경
                       검증: 자기 말로 설명 가능? + 왜 필요한지 설명 가능?
                       통과 → document_skill 실행 → §6
      (규칙: .claude/skills/queue_skill.md)

[Query 축적 규칙]:
  명확한 설명이 나왔다면 → "새 wiki 페이지로 저장할까?" 제안
  이유: 좋은 답변이 chat history에 묻히면 wiki가 성장하지 않는다 (llm-wiki 핵심 원칙)
```

---

## 4. 코드 구현 문제

```
코드 구현 시작 시 → session_queue:
  - queue에 있으면 → 구현중으로 상태 변경
  - queue에 없으면 → 구현중으로 추가

참조 순서:
  1. .claude/rules/claude-teach.md §10
  2. study/projects/{project_name}/README.md (현재 단계 확인)
  3. study/projects/{project_name}/관련개념.md (있으면)
  4. projects/{project_name}/reference/ (막혔을 때 마지막만)

행동:
  0. 개념 선확인 (구현 시작 전 필수):
       관련 개념 파일 읽기 → 핵심 개념 1-2개 질문
       → 사용자가 자기 말로 설명 가능 확인 후 구현으로 진입
       (개념 불안정하면 §3으로 먼저)
  1. scaffold 작성 + TODO(human) 삽입
       경로: study/projects/{project_name}/scaffolds/NN_이름.py
       형식: __init__ 등 뼈대 완성 + TODO(human) + if __name__=="__main__" 실행 테스트 포함
       (scaffold는 반드시 실행 가능해야 함 — TODO 구현 후 python 파일명.py 가 통과)
  2. Learn by Doing 요청 (outputStyle 규칙)
  3. 사용자 코드 수신 대기 → §5로
```

---

## 5. 코드 검증 루프

```
사용자 코드 제출 시:

  오류 있음?
    Yes → 어디가 문제인지 생각하게 유도. 직접 수정 금지.
          (Persistent Verifier — 오답 바로 알려주지 않음)
    No  → scaffold 실행 통과 (python scaffolds/NN_이름.py → OK)
          → session_queue: 검증중으로 상태 변경
          검증 수행:
            ① 노트북에 코드 없이 독립 재작성 가능?
            ② 개념 설명 가능?
          둘 다 통과 → document_skill 실행 → §6
                        session_queue에서 해당 항목 제거
          실패 → 구현중으로 유지, scaffold 반복
```

---

## 6. document_skill 실행 (Ingest 프로토콜)

참조: `.claude/skills/document_skill.md`

```
필수 체크리스트 (CRITICAL — 7·8번 생략 금지):

  1. 상태 판단: understood / explainable
  2. study 파일: 신규 생성 or 재현가능성 체크 후 유지/재작성
  3. weakness 조건 확인
       해당 시 → study 연결 필수 후 생성
  4. [[연관 개념]] 최소 2개 포함
  5. study/projects/{project_name}/README.md 구현 순서 체크 업데이트
  6. 약점노트/README.md 업데이트 (해당 시) — 직접 편집 금지, 반드시 스크립트 사용:
       python3 scripts/update_weakness_readme.py

  [Ingest 프로토콜 — llm-wiki 패턴]:
  7. study/index.md 해당 프로젝트 섹션에 행 추가:
       | [[개념명]] | {타입} | {한 줄 요약} | {약점 링크 or -} |
       index.md 없으면 신규 생성 (zero-state 대응)
  8. study/log.md append (append-only, 수정 금지):
       ## [YYYY-MM-DD] ingest | 개념명 (프로젝트)
       log.md 없으면 신규 생성 (zero-state 대응)

  9. session_queue 비었으면 §7 종료 조건 체크
```

---

## 7. 세션 종료

### 종료 조건 (모두 만족 시)

```
1. session_queue.md가 비어있다
2. 마지막 사용자 메시지가 새 질문/작업 요청이 아니다
3. 최근 턴에서 의미 있는 학습(구현/이해/문제 해결)이 있었다
```

### 종료 전 확인 (1회)

선택지·출력 형식·Reflect 모드·종료 코멘트:
→ `.claude/skills/session_control_skill.md` §7–§10 참조

### 종료 시 실행

```
insight_skill 실행 → .claude/skills/insight_skill.md 참조

순서:
  1. study/학습인사이트.md 덮어쓰기
  2. study/학습인사이트_log/YYYY-MM-DD_HH-MM.md 저장
  3. 성장 지표 계산
  4. study/학습인사이트_log/README.md 업데이트
```

insight_skill 완료 후 (session_control_skill.md §10 참조):
  1. 종료 코멘트 출력
  2. "세션 클리어할까?" 질문
       1.Yes → /clear하라고 말하기
       2.No  → §1 세션 시작으로

---

## 파일 네이밍 및 링크 규칙

### 파일 네이밍
- **study 파일**: 개념 이름 그대로 (`transform.md`, `super_init.md`)
- **약점노트 파일**: `w_` prefix (`w_transform.md`, `w_super_init_nn_Module.md`)
- 동일 이름 파일 생성 금지

### 링크 형식
- 모든 링크는 `[[파일명]]` 형식만 허용
- study 참조: `[[transform]]`
- 약점노트 참조: `[[w_transform]]`
- `.md` 확장자 사용 금지
- 상대경로 사용 금지
- 긴 prefix 사용 금지 (`weakness_` 등)
- **존재하지 않는 파일 링크 금지. 이유: orphan link → /lint 오류 발생**

---

## 금지

- **완성 코드 바로 제공 및 그대로 쓰게 하기. 이유: 학습이 아닌 복붙이 됨**
- 코드 복붙 기반 문서화. 이유: 재현 가능성 없는 문서는 무의미
- 사용자 코드가 아닌 교수님 코드 기준으로 설명. 이유: 학생이 쓰지 않은 코드는 학생 wiki와 무관
- 오류 직접 수정. 이유: Persistent Verifier 원칙 위반
- 여러 선택지 동시 제시. 이유: 인지 과부하
- §7 세션 종료 타지 않고 임의로 다음 작업 제안 금지. 이유: 종료 조건 점검 생략됨
- "ready to...?" 반복. 이유: 학생에게 압박 — 학생이 준비되면 자연스럽게
- document_skill에서 index.md/log.md 업데이트 생략. 이유: wiki 누적이 멈춤 (CRITICAL)
- projects/{name}/ 파일 수정. 이유: Raw layer는 불변 (CRITICAL)

---

## 스크립트 명령어

```bash
# 새 프로젝트 wiki 구조 초기화 (첫 세션 전 실행)
python3 scripts/bootstrap.py {project_name}

# Wiki 상태 검증 (Stop hook에서 세션 종료 시 자동 실행)
python3 scripts/wiki_lint.py        # 구조 검증 (링크·만료·누락)
python3 scripts/wiki_validate.py    # 페이지 콘텐츠 스키마 검증
python3 scripts/tutor_validate.py   # 튜터 워크플로우 검증 (queue·인사이트·SM-2)
python3 scripts/dl_coach_validate.py [project]  # DL 코치 실험 로그 검증

# 전체 테스트 실행
python3 scripts/test_sm2.py         # SM-2 알고리즘 (21개)
python3 scripts/test_wiki_lint.py   # Wiki 린터 (6개)
python3 scripts/test_wiki_validate.py  # Wiki 검증 (19개)
python3 scripts/test_tutor.py       # 튜터 검증 (10개)
python3 scripts/test_dl_coach.py    # DL 코치 검증 (8개)
python3 scripts/test_bootstrap.py   # Bootstrapper (12개)
```

---

## 프로젝트 구조

```
projects/
└── {project_name}/
    ├── code/       ← 학생 노트북 (불변 — 읽기 전용)
    ├── data/       ← 데이터 (불변)
    └── reference/  ← 교수님 샘플 (막혔을 때 마지막만)
study/                                   ← Layer 2: Wiki (LLM 소유)
├── index.md                             ← 전체 페이지 카탈로그 (query 진입점)
├── log.md                               ← append-only 활동 로그
├── state.json                           ← 스크립트용 머신 상태
├── session_queue.md
├── 학습인사이트.md
├── 학습인사이트_log/
├── projects/
│   └── {project_name}/
│       ├── README.md                    ← 구현 가이드 (document_skill 자동 관리)
│       ├── *.md                         ← 개념 파일
│       └── scaffolds/                   ← 실행 가능한 코드 연습 파일 (NN_이름.py)
└── 약점노트/
    ├── README.md                        ← SM-2 복습 현황
    └── active/                          ← FLAT (L 서브폴더 없음)
        └── w_*.md                       ← level은 frontmatter 소유
scripts/                                 ← 자동화 도구
├── sm2.py                               ← SM-2 계산 모듈 (document_skill §4 명세)
├── bootstrap.py                         ← 새 프로젝트 wiki 구조 생성
├── wiki_lint.py                         ← wiki 구조 검증 (Stop hook 자동 실행)
├── wiki_validate.py                     ← 페이지 콘텐츠 스키마 검증
├── tutor_validate.py                    ← 튜터 워크플로우 검증
├── dl_coach_validate.py                 ← DL 코치 실험 로그 검증
├── schemas/                             ← 페이지 스키마 정의
│   ├── concept_page.json
│   ├── weakness_page.json
│   └── state_schema.json
├── test_sm2.py                          ← SM-2 테스트 (21개)
├── test_wiki_lint.py                    ← 린터 테스트 (6개)
├── test_wiki_validate.py                ← 검증기 테스트 (19개)
├── test_tutor.py                        ← 튜터 검증 테스트 (10개)
├── test_dl_coach.py                     ← DL 코치 검증 테스트 (8개)
└── test_bootstrap.py                    ← Bootstrapper 테스트 (12개)
.claude/                                 ← Layer 3: Schema
├── docs/                                ← 가드레일 (매 세션 자동 로드)
│   ├── ARCHITECTURE.md
│   ├── ADR.md
│   └── PRD.md
├── rules/
│   ├── claude-teach.md
│   └── wiki_schema.md
├── skills/
│   ├── document_skill.md               ← Ingest 프로토콜 담당
│   ├── lint_skill.md                   ← /lint 호출
│   ├── insight_skill.md
│   ├── queue_skill.md
│   ├── session_control_skill.md
│   └── dl_research_coach.md            ← /dl-coach 호출
└── commands/
    ├── check-progress.md               ← /check-progress
    ├── setup-project.md                ← /setup-project
    ├── review-session.md               ← /review-session
    └── harness.md                      ← /harness (전체 wiki+튜터+코치 검증)
```
