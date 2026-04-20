# Lint Skill

> 호출: `/lint`  
> llm-wiki Lint 패턴 — wiki 건강 점검

참조: `.claude/rules/wiki_schema.md` Lint 기준

---

## 점검 항목

① **orphan link** — `[[링크]]` → 파일 없음  
② **SM-2 overdue** — `next_review <= 오늘` 인 약점노트  
③ **index 누락** — study 파일 있는데 `study/index.md`에 없는 것  
④ **study↔약점 불일치** — study 파일 있는데 `w_*.md` 없는 것  
⑤ **약점 고아** — `w_*.md` 있는데 study 파일 없는 것  

---

## 실행 절차

1. 각 항목별 목록 출력
2. `study/log.md` append:
   ```
   ## [오늘날짜] lint | 이상 없음  (또는 N개 문제)
   ```
3. 수정 필요 항목은 구체적 수정 방법 제안

---

## 자동 실행

Stop hook이 모든 세션 종료 시 `scripts/wiki_lint.py`를 자동으로 실행.  
수동 실행: `python3 scripts/wiki_lint.py`

---

## 출력 형식

```
Wiki Lint — YYYY-MM-DD
──────────────────────
① orphan link: N개
② SM-2 overdue: N개  
③ index 누락: N개
④ study↔약점 불일치: N개

[문제 있을 때]
  [orphan_link] study/projects/과제5/개념.md → [[없는파일]]
  수정: [[없는파일]] → 없는파일.md 📝 로 교체하거나 파일 생성

✅ 이상 없음 / ⚠️ N개 수정 필요
```
