# Wiki Harness — 전체 워크플로우 실행 명령어

> harness_framework 패턴 적용: 가드레일 주입 → 단계별 실행 → 검증

## 이 명령어가 하는 일

`/harness` 호출 시 다음 순서로 wiki 상태를 완전 점검하고 보고한다:

```
Phase 1: 가드레일 로드
Phase 2: 구조 검증 (wiki_lint.py)
Phase 3: 콘텐츠 검증 (wiki_validate.py)
Phase 4: 보고서 출력
Phase 5: 튜터·DL코치 검증 (tutor_validate.py, dl_coach_validate.py)
```

---

## Phase 1 — 가드레일 로드

다음 파일을 읽고 현재 시스템 상태를 파악하라:

```
.claude/docs/ARCHITECTURE.md    ← 3-layer 구조 확인
.claude/docs/ADR.md             ← 결정 사항 확인
.claude/rules/wiki_schema.md    ← Ingest/Query/Lint 규칙
study/index.md                  ← 현재 wiki 카탈로그
study/state.json                ← 프로젝트 상태
```

출력 형식:
```
[Phase 1] 가드레일 로드
  ✓ ARCHITECTURE.md
  ✓ ADR.md
  ✓ wiki_schema.md
  ✓ index.md — {N}개 프로젝트, {M}개 개념
  ✓ state.json — active: {project_name}
```

---

## Phase 2 — 구조 검증

```bash
python3 scripts/wiki_lint.py
```

검사 항목:
- ① 고아 링크 (orphan_link): `[[파일명]]` → 파일 없음
- ② SM-2 복습 대기 (sm2_overdue): next_review <= 오늘
- ③ index.md 누락 (index_missing): study 파일이 index에 없음
- ④ 약점노트 미생성 (no_weakness): study 파일에 대응 w_*.md 없음

오류 있으면 Phase 3 전에 표시하되 계속 진행.

---

## Phase 3 — 콘텐츠 검증

```bash
python3 scripts/wiki_validate.py
```

검사 항목:
- 개념 페이지: frontmatter(type/project/tags), 필수 섹션, 최소 wikilinks
- 약점 페이지: frontmatter(level/next_review/mastered), study 링크
- state.json: 스키마 준수, 필수 필드, status 유효값

특정 프로젝트만 검증:
```bash
python3 scripts/wiki_validate.py --project 과제5
```

---

## Phase 4 — 통합 보고서

출력 형식:

```
╔══════════════════════════════════════╗
║  Wiki Harness Report — YYYY-MM-DD   ║
╠══════════════════════════════════════╣
║ Phase 2 (Lint)                       ║
║   orphan_link  : N개                 ║
║   sm2_overdue  : N개                 ║
║   index_missing: N개                 ║
║   no_weakness  : N개                 ║
╠══════════════════════════════════════╣
║ Phase 3 (Validate)                   ║
║   오류         : N개                 ║
║   경고         : N개                 ║
╠══════════════════════════════════════╣
║ Phase 5 (Tutor/Coach)                ║
║   tutor 오류   : N개                 ║
║   coach 오류   : N개                 ║
╠══════════════════════════════════════╣
║ 총 이슈: N개   상태: ✅ / ⚠️ / ❌    ║
╚══════════════════════════════════════╝
```

상태 판단:
- ✅ 이슈 0개
- ⚠️ 경고만 있음 (오류 없음)
- ❌ 오류 1개 이상

---

## Phase 5 — 튜터·DL코치 검증

```bash
python3 scripts/tutor_validate.py
python3 scripts/dl_coach_validate.py [project_name]
```

검사 항목 (tutor_validate.py):
- ① session_queue.md 상태 필드 (이해중|구현중|검증중만 허용)
- ② 학습인사이트.md 필수 섹션 (현재 수준, 잘 잡힌 개념, 다음 세션 포인트)
- ③ SM-2 next_review 일관성 (sm2.py 사용)

검사 항목 (dl_coach_validate.py):
- ① 현재 단계 필드 (①②③④ 중 하나)
- ② 실험 테이블 필수 컬럼 (#|단계|변경 사항|가설|val_loss|val_acc|결론|다음 가설)
- ③ Baseline 행 (#=0) 존재 여부
- ④ 실험 번호 연속성
- ⑤ 다음 가설 열 (마지막 행 제외 채워져 있는지)

---

## 수동 실행 순서

```bash
# 전체 검증
python3 scripts/wiki_lint.py
python3 scripts/wiki_validate.py
python3 scripts/tutor_validate.py
python3 scripts/dl_coach_validate.py

# 특정 프로젝트
python3 scripts/wiki_validate.py --project 과제5
python3 scripts/dl_coach_validate.py 과제5

# 테스트 전체 실행
python3 scripts/test_sm2.py
python3 scripts/test_wiki_lint.py
python3 scripts/test_wiki_validate.py
python3 scripts/test_tutor.py
python3 scripts/test_dl_coach.py
python3 scripts/test_bootstrap.py
```

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `scripts/wiki_lint.py` | 구조 검증 (링크·참조 관계) |
| `scripts/wiki_validate.py` | 콘텐츠 검증 (스키마 준수) |
| `scripts/schemas/concept_page.json` | 개념 페이지 스키마 정의 |
| `scripts/schemas/weakness_page.json` | 약점 페이지 스키마 정의 |
| `scripts/schemas/state_schema.json` | state.json 스키마 정의 |
| `scripts/bootstrap.py` | 새 프로젝트 초기화 |
| `.claude/docs/ARCHITECTURE.md` | 3-layer 구조 설계 (가드레일) |
| `.claude/rules/wiki_schema.md` | Ingest/Query/Lint 규칙 (가드레일) |

---

## 오류 수정 가이드

| 오류 타입 | 수정 방법 |
|-----------|----------|
| `orphan_link` | 링크된 파일 생성 or `[[링크]]` 제거 |
| `sm2_overdue` | 약점노트 복습 세션 진행 |
| `index_missing` | document_skill Ingest 프로토콜 재실행 |
| `no_weakness` | 약점노트 생성 (document_skill이 처리) |
| `missing_frontmatter` | 해당 페이지에 YAML frontmatter 추가 |
| `missing_section` | 해당 섹션 추가 (wiki_schema.md 참조) |
| `mastery_inconsistent` | mastered: true 로 업데이트 |
