#!/usr/bin/env python3
"""WikiBootstrapper 단위 테스트 — 임시 디렉토리 격리
Usage: python3 scripts/test_bootstrap.py
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def _make_bootstrapper(tmpdir, project="테스트프로젝트"):
    import bootstrap
    bootstrap.BASE = tmpdir
    bootstrap.STUDY = tmpdir / "study"
    bootstrap.PROJECTS_RAW = tmpdir / "projects"
    return bootstrap.WikiBootstrapper(project)


class TestRawLayerCheck(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_missing_raw_layer_exits(self):
        """projects/{name}/ 없으면 sys.exit(1)"""
        b = _make_bootstrapper(self.tmpdir)
        with self.assertRaises(SystemExit) as ctx:
            b._check_raw_layer()
        self.assertEqual(ctx.exception.code, 1)

    def test_existing_raw_layer_passes(self):
        """projects/{name}/ 있으면 통과"""
        (self.tmpdir / "projects" / "테스트프로젝트").mkdir(parents=True)
        b = _make_bootstrapper(self.tmpdir)
        b._check_raw_layer()  # 예외 없음


class TestCreateStudyDir(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study").mkdir()
        (self.tmpdir / "projects" / "테스트프로젝트").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_study_dirs_created(self):
        """study/projects/{name}/ 과 약점노트/active/ 생성됨"""
        b = _make_bootstrapper(self.tmpdir)
        b._create_study_dir()
        self.assertTrue((self.tmpdir / "study" / "projects" / "테스트프로젝트").exists())
        self.assertTrue((self.tmpdir / "study" / "약점노트" / "active").exists())


class TestCreateReadme(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study" / "projects" / "테스트프로젝트").mkdir(parents=True)
        (self.tmpdir / "projects" / "테스트프로젝트").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_readme_created(self):
        """README.md 신규 생성됨"""
        b = _make_bootstrapper(self.tmpdir)
        b._create_readme()
        readme = self.tmpdir / "study" / "projects" / "테스트프로젝트" / "README.md"
        self.assertTrue(readme.exists())
        self.assertIn("테스트프로젝트", readme.read_text(encoding="utf-8"))

    def test_readme_not_overwritten(self):
        """기존 README.md 덮어쓰지 않음"""
        readme = self.tmpdir / "study" / "projects" / "테스트프로젝트" / "README.md"
        readme.write_text("기존 내용", encoding="utf-8")
        b = _make_bootstrapper(self.tmpdir)
        b._create_readme()
        self.assertEqual(readme.read_text(encoding="utf-8"), "기존 내용")


class TestCreateScaffolds(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study" / "projects" / "테스트프로젝트").mkdir(parents=True)
        (self.tmpdir / "projects" / "테스트프로젝트").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_scaffolds_dir_created(self):
        """scaffolds/ 디렉토리 생성됨"""
        b = _make_bootstrapper(self.tmpdir)
        b._create_scaffolds()
        self.assertTrue(
            (self.tmpdir / "study" / "projects" / "테스트프로젝트" / "scaffolds").exists()
        )

    def test_starter_scaffold_created(self):
        """00_starter.py 생성되고 프로젝트명 포함"""
        b = _make_bootstrapper(self.tmpdir)
        b._create_scaffolds()
        starter = self.tmpdir / "study" / "projects" / "테스트프로젝트" / "scaffolds" / "00_starter.py"
        self.assertTrue(starter.exists())
        self.assertIn("테스트프로젝트", starter.read_text(encoding="utf-8"))

    def test_starter_not_overwritten(self):
        """기존 00_starter.py 덮어쓰지 않음"""
        scaffold_dir = self.tmpdir / "study" / "projects" / "테스트프로젝트" / "scaffolds"
        scaffold_dir.mkdir(parents=True)
        starter = scaffold_dir / "00_starter.py"
        starter.write_text("기존 내용", encoding="utf-8")
        b = _make_bootstrapper(self.tmpdir)
        b._create_scaffolds()
        self.assertEqual(starter.read_text(encoding="utf-8"), "기존 내용")

    def test_experiments_dir_created(self):
        """experiments/ 디렉토리 생성됨"""
        b = _make_bootstrapper(self.tmpdir)
        b._create_scaffolds()
        self.assertTrue(
            (self.tmpdir / "study" / "projects" / "테스트프로젝트" / "experiments").exists()
        )

    def test_experiment_log_created(self):
        """experiments/log.md 생성됨"""
        b = _make_bootstrapper(self.tmpdir)
        b._create_scaffolds()
        log = self.tmpdir / "study" / "projects" / "테스트프로젝트" / "experiments" / "log.md"
        self.assertTrue(log.exists())
        self.assertIn("Phase 1", log.read_text(encoding="utf-8"))


class TestInitZeroState(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study" / "약점노트" / "active").mkdir(parents=True)
        (self.tmpdir / "projects" / "테스트프로젝트").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_zero_state_files_created(self):
        """session_queue.md, 약점노트/README.md, 학습인사이트.md 생성됨"""
        b = _make_bootstrapper(self.tmpdir)
        b._init_zero_state()
        self.assertTrue((self.tmpdir / "study" / "session_queue.md").exists())
        self.assertTrue((self.tmpdir / "study" / "약점노트" / "README.md").exists())
        self.assertTrue((self.tmpdir / "study" / "학습인사이트.md").exists())

    def test_existing_files_not_overwritten(self):
        """기존 파일 있으면 덮어쓰지 않음"""
        queue = self.tmpdir / "study" / "session_queue.md"
        queue.write_text("기존 큐", encoding="utf-8")
        b = _make_bootstrapper(self.tmpdir)
        b._init_zero_state()
        self.assertEqual(queue.read_text(encoding="utf-8"), "기존 큐")


class TestUpdateIndex(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study").mkdir()
        (self.tmpdir / "projects" / "테스트프로젝트").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_index_created_when_missing(self):
        """index.md 없으면 신규 생성 후 섹션 추가"""
        b = _make_bootstrapper(self.tmpdir)
        b._update_index()
        index = self.tmpdir / "study" / "index.md"
        self.assertTrue(index.exists())
        self.assertIn("## 테스트프로젝트", index.read_text(encoding="utf-8"))

    def test_section_added_when_not_present(self):
        """기존 index.md에 해당 섹션 없으면 추가"""
        index = self.tmpdir / "study" / "index.md"
        index.write_text("# Study Index\n\n## 다른프로젝트\n\n내용\n", encoding="utf-8")
        b = _make_bootstrapper(self.tmpdir)
        b._update_index()
        self.assertIn("## 테스트프로젝트", index.read_text(encoding="utf-8"))
        self.assertIn("## 다른프로젝트", index.read_text(encoding="utf-8"))

    def test_section_not_duplicated(self):
        """이미 섹션 있으면 중복 추가하지 않음"""
        index = self.tmpdir / "study" / "index.md"
        index.write_text("# Study Index\n\n## 테스트프로젝트\n\n내용\n", encoding="utf-8")
        b = _make_bootstrapper(self.tmpdir)
        b._update_index()
        content = index.read_text(encoding="utf-8")
        self.assertEqual(content.count("## 테스트프로젝트"), 1)


class TestUpdateLogAndState(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study").mkdir()
        (self.tmpdir / "projects" / "테스트프로젝트").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_log_entry_recorded(self):
        """log.md에 init 항목 기록됨"""
        b = _make_bootstrapper(self.tmpdir)
        b._update_log()
        log = self.tmpdir / "study" / "log.md"
        self.assertTrue(log.exists())
        self.assertIn("init | 테스트프로젝트", log.read_text(encoding="utf-8"))

    def test_state_json_updated(self):
        """state.json에 프로젝트 키 및 active_project 기록됨"""
        b = _make_bootstrapper(self.tmpdir)
        b._update_state()
        state_path = self.tmpdir / "study" / "state.json"
        self.assertTrue(state_path.exists())
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["active_project"], "테스트프로젝트")
        self.assertIn("테스트프로젝트", state["projects"])
        self.assertEqual(state["projects"]["테스트프로젝트"]["status"], "in_progress")


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    sys.exit(0 if result.result.wasSuccessful() else 1)
