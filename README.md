# Claude Code 학습 시스템

Claude Code CLI를 활용한 LLM-wiki 기반 딥러닝 학습 프레임워크.  
개념 이해 → 코드 구현 → 검증 → wiki 문서화까지 세션 단위로 관리한다.

---

## 구조

```
.claude/        ← 튜터 규칙·워크플로우 (rules, skills, docs)
scripts/        ← 자동화 도구 (bootstrap, SM-2, lint, validate)
projects/       ← 프로젝트별 Raw 데이터·코드 (Git 제외)
study/          ← LLM이 관리하는 Wiki (개념 노트, 약점노트, 실험 로그)
CLAUDE.md       ← Claude Code 세션 진입점 (규칙 총괄)
```

## 시작하는 법

**1. 레포 클론**
```bash
git clone https://github.com/beomjinkim2000/Study_code.git
cd Study_code
```

**2. 프로젝트 데이터 추가** (Git 미포함 — 직접 넣기)
```bash
mkdir -p projects/{project_name}/code
mkdir -p projects/{project_name}/data
```

**3. Wiki 구조 초기화**
```bash
python3 scripts/bootstrap.py {project_name}
```
→ `study/projects/{project_name}/` 하위에 README, scaffold, 실험 로그 자동 생성

**4. Claude Code로 세션 시작**
```bash
claude
```
→ CLAUDE.md 규칙에 따라 세션 시작 워크플로우 자동 실행

---

## 세션 흐름

```
개념 질문 → 설명 + 이해 확인
         → scaffold 작성 (Learn by Doing)
         → 검증 (노트북 독립 재작성 가능?)
         → document_skill: wiki 문서화 + SM-2 약점노트
```

## 주요 스크립트

| 명령어 | 역할 |
|--------|------|
| `python3 scripts/bootstrap.py {name}` | 새 프로젝트 wiki 초기화 |
| `python3 scripts/wiki_lint.py` | wiki 구조 검증 (orphan link, SM-2 만료 등) |
| `python3 scripts/test_bootstrap.py` | 전체 단위 테스트 실행 |
