#!/usr/bin/env python3
"""WikiLinter 테스트 — harness test_execute.py 패턴 (임시 디렉토리)
Usage: python3 scripts/test_wiki_lint.py
"""
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent))
import wiki_lint


class TestWikiLinter(unittest.TestCase):
    """각 테스트는 독립적인 임시 디렉토리 사용"""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study" / "projects" / "테스트").mkdir(parents=True)
        (self.tmpdir / "study" / "약점노트" / "active").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _make_linter(self) -> wiki_lint.WikiLinter:
        wiki_lint.BASE = self.tmpdir
        wiki_lint.STUDY = self.tmpdir / "study"
        wiki_lint.ACTIVE = self.tmpdir / "study" / "약점노트" / "active"
        return wiki_lint.WikiLinter()

    # ── ① orphan link ──────────────────────────────────────────────

    def test_orphan_link_detection(self):
        """존재하지 않는 파일 링크 감지"""
        (self.tmpdir / "study" / "projects" / "테스트" / "개념.md").write_text(
            "[[없는파일]]", encoding="utf-8"
        )
        linter = self._make_linter()
        linter._check_orphan_links()
        orphans = [i for i in linter.issues if i["type"] == "orphan_link"]
        self.assertEqual(len(orphans), 1)
        self.assertEqual(orphans[0]["link"], "없는파일")

    def test_orphan_link_no_false_positive(self):
        """실제 존재하는 파일 링크는 감지하지 않음"""
        proj = self.tmpdir / "study" / "projects" / "테스트"
        (proj / "실제파일.md").write_text("", encoding="utf-8")
        (proj / "개념.md").write_text("[[실제파일]]", encoding="utf-8")
        linter = self._make_linter()
        linter._check_orphan_links()
        self.assertEqual(len(linter.issues), 0)

    # ── ② SM-2 overdue ─────────────────────────────────────────────

    def test_sm2_overdue(self):
        """next_review가 어제면 감지"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        (self.tmpdir / "study" / "약점노트" / "active" / "w_테스트.md").write_text(
            f"---\nnext_review: {yesterday}\n---\n", encoding="utf-8"
        )
        linter = self._make_linter()
        linter._check_sm2_overdue()
        overdue = [i for i in linter.issues if i["type"] == "sm2_overdue"]
        self.assertEqual(len(overdue), 1)

    def test_sm2_future_not_flagged(self):
        """미래 날짜는 감지하지 않음"""
        future = (date.today() + timedelta(days=5)).isoformat()
        (self.tmpdir / "study" / "약점노트" / "active" / "w_테스트.md").write_text(
            f"---\nnext_review: {future}\n---\n", encoding="utf-8"
        )
        linter = self._make_linter()
        linter._check_sm2_overdue()
        self.assertEqual(len(linter.issues), 0)

    # ── ③ index completeness ───────────────────────────────────────

    def test_index_missing_entry(self):
        """study 파일이 index.md에 없으면 감지"""
        (self.tmpdir / "study" / "projects" / "테스트" / "개념.md").write_text(
            "", encoding="utf-8"
        )
        (self.tmpdir / "study" / "index.md").write_text(
            "# Index\n(비어있음)\n", encoding="utf-8"
        )
        linter = self._make_linter()
        linter._check_index_completeness()
        missing = [i for i in linter.issues if i["type"] == "index_missing"]
        self.assertEqual(len(missing), 1)

    # ── ④ log format ───────────────────────────────────────────────

    def test_log_format(self):
        """log.md에 lint 결과가 올바른 형식으로 기록됨"""
        log = self.tmpdir / "study" / "log.md"
        log.write_text("# Log\n", encoding="utf-8")
        linter = self._make_linter()
        linter._update_log()
        content = log.read_text(encoding="utf-8")
        today = date.today().isoformat()
        self.assertIn(f"## [{today}] lint |", content)


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    sys.exit(0 if result.result.wasSuccessful() else 1)
