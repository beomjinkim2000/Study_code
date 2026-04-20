#!/usr/bin/env python3
"""약점노트 README.md 자동 생성
Usage: python3 scripts/update_weakness_readme.py

active/ 폴더의 w_*.md 파일을 파싱해 오늘 날짜 기준 복습 대기 목록을 생성.
"""
from pathlib import Path
from datetime import date
import re

BASE = Path(__file__).parent.parent
ACTIVE = BASE / "study" / "약점노트" / "active"
README = BASE / "study" / "약점노트" / "README.md"
TODAY = date.today()

SM2_TABLE = """\
## 복습 간격 기준 (SM-2)

| 결과 | 인터벌 |
|------|--------|
| 힌트 없이 정답 (perfect) | × 2.5 |
| 힌트 1번 후 정답 | × 1.5 |
| 힌트 2번 후 정답 | × 1.0 |
| 힌트 3번 후 정답 | × 0.5 |
| 끝까지 못맞춤 | 리셋 → 1일 |

힌트 없이 3번 연속 정답 → `mastered/`로 이동"""


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"')
    return fm


def build_display_name(fm: dict, stem: str) -> str:
    concept = fm.get("concept", "")
    if concept:
        return concept
    return stem.replace("w_", "").replace("_", " ")


def main():
    entries = []
    for wf in sorted(ACTIVE.glob("w_*.md")):
        if wf.name == ".gitkeep":
            continue
        fm = parse_frontmatter(wf)
        next_review_str = fm.get("next_review", "")
        try:
            next_review = date.fromisoformat(str(next_review_str))
        except ValueError:
            next_review = None

        stem = wf.stem  # e.g. w_transform
        display = build_display_name(fm, stem)
        project = fm.get("project", fm.get("subject", "-")).split("_")[0]
        level = str(fm.get("level", "-"))
        if not level.startswith("L"):
            level = f"L{level}"
        streak = fm.get("current_streak", "0")
        mastered = str(fm.get("mastered", "false")).lower() == "true"

        entries.append({
            "stem": stem,
            "display": display,
            "project": project,
            "level": level,
            "streak": streak,
            "next_review": next_review,
            "next_review_str": str(next_review_str),
            "mastered": mastered,
        })

    overdue = [e for e in entries if e["next_review"] and e["next_review"] <= TODAY and not e["mastered"]]
    active_all = [e for e in entries if not e["mastered"]]

    overdue_section = f"## 복습 대기 (next_review <= {TODAY})\n\n"
    if overdue:
        overdue_section += "| 개념 | due |\n|------|-----|\n"
        for e in sorted(overdue, key=lambda x: x["next_review"]):
            overdue_section += f"| [[{e['stem']}\\|{e['display']}]] | {e['next_review_str']} |\n"
    else:
        overdue_section += "없음\n"

    active_section = "## 전체 active\n\n"
    active_section += "| 개념 | 프로젝트 | 레벨 | 연속정답 | 다음복습 |\n"
    active_section += "|------|----------|------|----------|----------|\n"
    for e in active_all:
        active_section += (
            f"| [[{e['stem']}\\|{e['display']}]] | {e['project']} | "
            f"{e['level']} | {e['streak']} | {e['next_review_str']} |\n"
        )

    content = f"""# 약점노트 현황

> SM-2 기반 간격 반복 — 틀린 것뿐 아니라 **맞춘 것도** 복습 (간격만 다름)
> 새 개념 생기면 약점노트도 같이 생성. study 파일 1개 = 약점노트 1개.

_updated: {TODAY}_

---

{overdue_section}
---

{active_section}
---

## 마스터 완료

없음

---

{SM2_TABLE}
"""
    README.write_text(content, encoding="utf-8")
    print(f"✓ 약점노트 README 업데이트 완료 ({TODAY})")
    print(f"  복습 대기: {len(overdue)}개 / 전체 active: {len(active_all)}개")


if __name__ == "__main__":
    main()
