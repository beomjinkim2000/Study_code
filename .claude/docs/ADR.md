# Architecture Decision Records

## 철학: 학습 > 해결. 재현 가능성 > 완성.

---

### ADR-001: llm-wiki 3-layer 패턴 채택
**결정**: Raw / Wiki / Schema 분리  
**이유**: RAG(매번 재탐색) 대신 persistent wiki(점진적 축적). 한 번 정리한 개념은 다음 세션에도 살아있다.  
**트레이드오프**: 파일 수 증가, 유지 비용 있음 → LLM이 담당하므로 실질적 부담 없음

---

### ADR-002: SM-2 간격 반복
**결정**: 오답뿐 아니라 정답도 약점노트로 추적  
**이유**: 망각 곡선 대응. 한 번 맞혔다고 기억이 유지되지 않음  
**트레이드오프**: 모든 개념에 약점노트 생성 → index.md + lint로 관리

---

### ADR-003: 약점노트 flat 구조
**결정**: `active/` 하나에 모든 파일 (L 서브폴더 제거)  
**이유**: 레벨 변경 시 파일 이동 불필요. level은 frontmatter가 소유  
**트레이드오프**: 폴더 탐색 시 레벨 구분 없음 → README.md 표가 커버

---

### ADR-004: index.md + log.md 분리
**결정**: content map(index.md) / 활동 로그(log.md) 완전 분리  
**이유**: 목적이 다름. index = 현재 상태(갱신), log = 역사(append-only)  
**트레이드오프**: document_skill 실행 시 두 파일 동시 업데이트 필요 → CRITICAL 규칙으로 강제

---

### ADR-005: scripts/ 자동화 도구
**결정**: bootstrap.py(설정) + wiki_lint.py(검증) 별도 Python 스크립트 유지  
**이유**: Claude 세션 없이도 실행 가능. Stop hook으로 자동 검증  
**트레이드오프**: Python 필요 → .venv 이미 존재

---

### ADR-006: Skill vs Agent (dl_research_coach)
**결정**: Skill로 구현 (Agent 분리 없음)  
**이유**: Agent는 session_queue, study 파일 등 현재 컨텍스트를 잃음. Skill은 전체 컨텍스트 유지  
**트레이드오프**: 메인 컨텍스트 window 사용 → 학습 연속성이 더 중요
