# Wiki Schema (llm-wiki 기반)

## 페이지 타입

| 타입 | 예시 | 설명 |
|------|------|------|
| `concept` | `transform.md` | 단일 개념 |
| `comparison` | `sorted_vs_sort.md` | X vs Y |
| `weakness` | `w_*.md` | SM-2 오답 추적 |
| `synthesis` | (필요 시) | 여러 개념 연결 |

## YAML frontmatter (study 페이지)

```yaml
---
type: concept | comparison | synthesis
project: 과제5
tags: [딥러닝, 과제5]
---
```

## Ingest 절차 (document_skill 실행 시 — CRITICAL)

1. 개념 페이지 생성/업데이트 (`study/projects/{name}/개념명.md`)
2. `study/index.md` 해당 프로젝트 섹션에 행 추가:
   ```
   | [[개념명]] | {타입} | {한 줄 요약} | {약점 링크 or -} |
   ```
3. 관련 페이지 cross-ref 업데이트 (최소 2개 `[[링크]]`)
4. `study/log.md` append:
   ```
   ## [YYYY-MM-DD] ingest | 개념명 (프로젝트)
   ```
5. 약점 조건 충족 시 `active/w_*.md` 생성

**index.md나 log.md가 없으면 신규 생성 (zero-state 대응)**

## Query 절차

1. `study/index.md` 먼저 읽기 (카탈로그 파악)
2. 관련 페이지 드릴다운
3. 좋은 답변 → "새 위키 페이지로 저장할까?" 제안  
   이유: 좋은 답변이 chat history에 묻히면 wiki가 성장하지 않음

## Lint 기준 (lint_skill / wiki_lint.py)

| 항목 | 감지 조건 |
|------|----------|
| orphan link | `[[링크]]` → 파일 없음 |
| SM-2 overdue | `next_review <= 오늘` |
| index 누락 | study 파일 있는데 index.md에 없음 |
| study↔약점 불일치 | study 파일 있는데 `w_*.md` 없음 |

## log.md 포맷 (append-only — 수정 금지)

```
## [YYYY-MM-DD] ingest | 개념명 (프로젝트)
## [YYYY-MM-DD] lint | 이상 없음 | N개 문제
## [YYYY-MM-DD] init | {project} bootstrapped
```

→ `grep "^## " study/log.md` 로 파싱 가능

## 링크 규칙

- 형식: `[[파일명]]` (`.md` 확장자 없음, 경로 없음)
- 약점노트: `[[w_파일명]]`
- **존재하지 않는 파일 링크 금지** — 항상 파일 존재 확인 후 링크

## 약점노트 경로

```
study/약점노트/active/w_*.md    ← FLAT (L 서브폴더 없음)
```

level은 frontmatter `level:` 필드가 소유. 폴더 이동 불필요.
