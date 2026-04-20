# PRD: 학습 위키 시스템

## 목표
딥러닝 과제를 통해 개념을 이해하고, **코드 없이 재작성 가능한 수준**까지 익힌다.

## 사용자
혼자 공부하는 학생. `projects/` 폴더만 있으면 즉시 시작 가능 (zero-state).

## 핵심 기능

1. **개념 위키** (Ingest): 공부한 것을 체계적으로 축적. 세션이 끊겨도 누적됨.
2. **약점 추적** (SM-2 Lint): 잊기 전에 복습. 맞춘 것도 추적.
3. **실험 코칭** (dl_research_coach): DL 실험을 논리적 흐름으로 — `/dl-coach` 호출 시.

## MVP 제외

- 임베딩/벡터 검색 → index.md로 충분 (현재 규모)
- 자동화된 학습 세션 → 반드시 인터랙티브
- 협업 기능 → 1인 사용

## 디자인 원칙

- 새 프로젝트 = `python3 scripts/bootstrap.py {name}` 한 줄
- 세션 종료 시 Stop hook이 wiki 건강 자동 점검
- Obsidian graph view로 지식 연결 시각화

## 명령어

```bash
python3 scripts/bootstrap.py {project_name}   # 새 프로젝트 설정
python3 scripts/wiki_lint.py                   # wiki 검증
python3 scripts/test_wiki_lint.py              # 린터 테스트
```

## 슬래시 명령어

| 명령어 | 역할 |
|--------|------|
| `/lint` | wiki 상태 점검 |
| `/dl-coach` | DL 실험 코칭 시작 |
| `/setup-project` | 새 프로젝트 wiki 구조 설정 |
| `/review-session` | 세션 후 wiki 리뷰 |
| `/check-progress` | 학습 진도 확인 |
