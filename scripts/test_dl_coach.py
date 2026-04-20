#!/usr/bin/env python3
"""DLCoachValidator 단위 테스트
Usage: python3 scripts/test_dl_coach.py
"""
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

VALID_LOG = """\
# Experiment Log — 테스트

현재 단계: ①

| # | 단계 | 변경 사항 | 가설 | val_loss | val_acc | 결론 | 다음 가설 |
|---|------|-----------|------|----------|---------|------|-----------|
| 0 | ① | Baseline | - | 0.85 | 0.70 | 기준점 | 학습률 낮추기 |
| 1 | ② | lr=0.001 | 낮은 lr로 안정화 | 0.72 | 0.78 | 개선 | 배치 크기 조정 |
"""


def _make_validator(tmpdir, project="테스트"):
    import dl_coach_validate as dc
    dc.BASE = tmpdir
    dc.STUDY = tmpdir / "study"
    log_dir = tmpdir / "study" / "projects" / project / "experiments"
    log_dir.mkdir(parents=True, exist_ok=True)
    return dc.DLCoachValidator(project=project), log_dir


class TestDLCoachValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_log(self, content, project="테스트"):
        _, log_dir = _make_validator(self.tmpdir, project)
        (log_dir / "log.md").write_text(content, encoding="utf-8")

    def test_valid_log_passes(self):
        """유효한 실험 로그는 오류 없음"""
        self._write_log(VALID_LOG)
        v, _ = _make_validator(self.tmpdir)
        content = (self.tmpdir / "study" / "projects" / "테스트" / "experiments" / "log.md").read_text(encoding="utf-8")
        v._check_current_phase(content, self.tmpdir / "study" / "projects" / "테스트" / "experiments" / "log.md")
        v._check_table_columns(content, self.tmpdir / "study" / "projects" / "테스트" / "experiments" / "log.md")
        v._check_baseline_row(content, self.tmpdir / "study" / "projects" / "테스트" / "experiments" / "log.md")
        v._check_number_continuity(content, self.tmpdir / "study" / "projects" / "테스트" / "experiments" / "log.md")
        self.assertEqual(len(v.errors), 0)

    def test_missing_phase_errors(self):
        """현재 단계 필드 없으면 오류"""
        log = VALID_LOG.replace("현재 단계: ①\n", "")
        self._write_log(log)
        v, log_dir = _make_validator(self.tmpdir)
        content = (log_dir / "log.md").read_text(encoding="utf-8")
        v._check_current_phase(content, log_dir / "log.md")
        errs = [e for e in v.errors if e["type"] == "missing_phase"]
        self.assertEqual(len(errs), 1)

    def test_invalid_phase_errors(self):
        """유효하지 않은 단계(⑤ 등)는 오류"""
        log = VALID_LOG.replace("현재 단계: ①", "현재 단계: ⑤")
        self._write_log(log)
        v, log_dir = _make_validator(self.tmpdir)
        content = (log_dir / "log.md").read_text(encoding="utf-8")
        v._check_current_phase(content, log_dir / "log.md")
        errs = [e for e in v.errors if e["type"] == "invalid_phase"]
        self.assertEqual(len(errs), 1)

    def test_missing_column_errors(self):
        """필수 컬럼 누락 시 오류"""
        log = VALID_LOG.replace("| # | 단계 | 변경 사항 | 가설 | val_loss | val_acc | 결론 | 다음 가설 |",
                                "| # | 단계 | 변경 사항 | 가설 | val_loss | 결론 | 다음 가설 |")
        self._write_log(log)
        v, log_dir = _make_validator(self.tmpdir)
        content = (log_dir / "log.md").read_text(encoding="utf-8")
        v._check_table_columns(content, log_dir / "log.md")
        errs = [e for e in v.errors if e["type"] == "missing_column"]
        self.assertGreater(len(errs), 0)
        cols = [e["column"] for e in errs]
        self.assertIn("val_acc", cols)

    def test_missing_baseline_errors(self):
        """Baseline 행(#=0) 없으면 오류"""
        log = VALID_LOG.replace("| 0 | ① | Baseline | - | 0.85 | 0.70 | 기준점 | 학습률 낮추기 |\n", "")
        self._write_log(log)
        v, log_dir = _make_validator(self.tmpdir)
        content = (log_dir / "log.md").read_text(encoding="utf-8")
        v._check_baseline_row(content, log_dir / "log.md")
        errs = [e for e in v.errors if e["type"] == "missing_baseline"]
        self.assertEqual(len(errs), 1)

    def test_gap_in_numbers_warns(self):
        """실험 번호 불연속 시 경고"""
        log = """\
# Experiment Log

현재 단계: ②

| # | 단계 | 변경 사항 | 가설 | val_loss | val_acc | 결론 | 다음 가설 |
|---|------|-----------|------|----------|---------|------|-----------|
| 0 | ① | Baseline | - | 0.85 | 0.70 | 기준점 | 테스트 |
| 2 | ② | lr=0.001 | 안정화 | 0.72 | 0.78 | 개선 | - |
"""
        self._write_log(log)
        v, log_dir = _make_validator(self.tmpdir)
        content = (log_dir / "log.md").read_text(encoding="utf-8")
        v._check_number_continuity(content, log_dir / "log.md")
        warns = [w for w in v.warnings if w["type"] == "gap_in_numbers"]
        self.assertEqual(len(warns), 1)
        self.assertIn(1, warns[0]["missing"])

    def test_empty_next_hypothesis_warns(self):
        """마지막 행 제외 다음 가설 열 비어있으면 경고"""
        log = """\
# Experiment Log

현재 단계: ②

| # | 단계 | 변경 사항 | 가설 | val_loss | val_acc | 결론 | 다음 가설 |
|---|------|-----------|------|----------|---------|------|-----------|
| 0 | ① | Baseline | - | 0.85 | 0.70 | 기준점 | - |
| 1 | ② | lr=0.001 | 안정화 | 0.72 | 0.78 | 개선 | 배치 조정 |
"""
        self._write_log(log)
        v, log_dir = _make_validator(self.tmpdir)
        content = (log_dir / "log.md").read_text(encoding="utf-8")
        v._check_next_hypothesis(content, log_dir / "log.md")
        warns = [w for w in v.warnings if w["type"] == "empty_next_hypothesis"]
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0]["row"], "0")

    def test_no_log_file_returns_zero(self):
        """log.md 없으면 오류 0 반환"""
        import dl_coach_validate as dc
        dc.BASE = self.tmpdir
        dc.STUDY = self.tmpdir / "study"
        (self.tmpdir / "study" / "projects").mkdir(parents=True, exist_ok=True)
        v = dc.DLCoachValidator(project="없는프로젝트")
        result = v.run()
        self.assertEqual(result, 0)


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    sys.exit(0 if result.result.wasSuccessful() else 1)
