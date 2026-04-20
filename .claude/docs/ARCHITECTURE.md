# 아키텍처

## 3-Layer 구조 (llm-wiki 패턴)

```
Layer 1: projects/{name}/        ← Raw (불변, 학생 코드·데이터)
Layer 2: study/                  ← Wiki (LLM이 소유, Obsidian에서 열람)
Layer 3: .claude/                ← Schema (규칙·워크플로우 정의)
```

**원칙**: LLM은 Layer 2를 소유·관리한다. Layer 1은 절대 수정 금지.

## 운영 오퍼레이션

- **Ingest** (document_skill): 새 개념 → 개념 페이지 + index.md 행 추가 + log.md 기록 + 약점노트
- **Query**: study/index.md 먼저 읽기 → 관련 페이지 드릴다운 → 좋은 답변은 새 페이지로 저장
- **Lint** (lint_skill / scripts/wiki_lint.py): 주기적 wiki 상태 점검 + Stop hook 자동 실행

## 핵심 파일

| 파일 | 역할 | 비고 |
|------|------|------|
| `study/index.md` | 전체 페이지 카탈로그 | query 진입점 |
| `study/log.md` | append-only 활동 로그 | `grep "^## "` 파싱 가능 |
| `study/state.json` | 스크립트용 머신 상태 | bootstrap/lint 자동 업데이트 |
| `약점노트/active/` | SM-2 약점 파일 | flat 구조 — L 폴더 없음 |

## Obsidian 연동

- `study/` = Obsidian vault (symlink)
- `[[link]]` = Obsidian wikilinks (경로·확장자 없음)
- YAML frontmatter → Dataview 쿼리 가능
- graph view로 wiki 연결 구조 시각화

## 자동화

```bash
python3 scripts/bootstrap.py {name}   # 새 프로젝트 초기화
python3 scripts/wiki_lint.py          # 수동 검증
python3 scripts/test_wiki_lint.py     # 린터 테스트
```

Stop hook: 세션 종료 시 `wiki_lint.py` 자동 실행 → `study/log.md` 기록
