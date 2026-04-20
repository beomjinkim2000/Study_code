이 명령어는 새 학습 프로젝트의 wiki 구조를 설정한다.

---

## 워크플로우

### A. 탐색 (먼저 읽어라)

- `.claude/docs/ARCHITECTURE.md` — 3-layer 구조 확인
- `.claude/docs/PRD.md` — 시스템 목적 확인
- `study/index.md` — 현재 wiki 상태 확인

### B. 설정

```bash
python3 scripts/bootstrap.py {project_name}
```

bootstrap.py가 자동으로 처리하는 것:
- `projects/{name}/` 존재 확인 (Raw layer 필수)
- `study/projects/{name}/README.md` 생성
- `study/index.md` 섹션 추가
- `study/log.md` init 항목 기록
- `study/state.json` 업데이트
- zero-state 초기화 (session_queue, 약점노트/README.md, 학습인사이트.md 없으면 생성)

### C. 검증 (AC)

```bash
python3 scripts/wiki_lint.py
```

확인 항목:
- `study/projects/{name}/README.md` 생성됨?
- `study/index.md`에 `## {name}` 섹션 있음?
- `study/log.md`에 init 항목 있음?
- lint 결과 0개 문제?

---

## 금지사항

- bootstrap.py 없이 수동으로 파일 생성하지 마라. 이유: 구조 불일치 → lint 오류
- `projects/{name}/` (raw layer)를 건드리지 마라. 이유: 불변 원칙 위반
