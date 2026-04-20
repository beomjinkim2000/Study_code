학습 세션 후 wiki 상태를 리뷰하라.

---

## 먼저 읽어라

- `.claude/docs/ARCHITECTURE.md`
- `.claude/docs/ADR.md`
- `study/index.md`
- `study/log.md` (오늘 항목 확인)

---

## 체크리스트

| 항목 | 결과 | 비고 |
|------|------|------|
| index.md 최신 | ✅/❌ | 누락 파일 목록 |
| orphan link 없음 | ✅/❌ | 끊어진 링크 목록 |
| SM-2 복습 대기 | ✅/❌ | next_review <= 오늘 항목 |
| study↔약점 일치 | ✅/❌ | 불일치 항목 |
| log.md 오늘 항목 | ✅/❌ | ingest 기록 있는지 |
| ADR 준수 | ✅/❌ | flat 구조 / [[]] 링크 형식 |
| state.json 최신 | ✅/❌ | concepts_completed 정확한지 |

---

## 위반 사항 처리

위반이 있으면 구체적 수정 방법 제안:
- orphan link → 파일 생성 or 링크를 `파일명.md 📝`로 교체
- index 누락 → index.md에 행 추가
- SM-2 overdue → 복습 진행 후 next_review 갱신
