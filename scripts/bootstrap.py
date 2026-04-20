#!/usr/bin/env python3
"""Wiki Bootstrapper — 새 학습 프로젝트 위키 구조 생성
Usage: python3 scripts/bootstrap.py <project_name>
"""
import sys
import json
from pathlib import Path
from datetime import date

BASE = Path(__file__).parent.parent
STUDY = BASE / "study"
PROJECTS_RAW = BASE / "projects"


class WikiBootstrapper:
    """harness StepExecutor 패턴 — 단계별 실행 + 진행 표시 + 검증"""

    def __init__(self, project_name: str):
        self.name = project_name
        self.today = date.today().isoformat()
        self.steps = [
            ("raw layer 확인",      self._check_raw_layer),
            ("study 디렉토리 생성", self._create_study_dir),
            ("README.md 생성",      self._create_readme),
            ("scaffold 생성",       self._create_scaffolds),
            ("zero-state 초기화",   self._init_zero_state),
            ("index.md 업데이트",   self._update_index),
            ("log.md 기록",         self._update_log),
            ("state.json 업데이트", self._update_state),
        ]

    def run(self):
        print(f"\n{'='*50}")
        print(f" WikiBootstrapper: {self.name}")
        print(f"{'='*50}")
        for label, fn in self.steps:
            print(f"  ▸ {label}...", end=" ", flush=True)
            fn()
            print("완료")
        self._print_summary()

    def _check_raw_layer(self):
        raw = PROJECTS_RAW / self.name
        if not raw.exists():
            print(f"\n[ERROR] projects/{self.name}/ 없음. Raw layer를 먼저 추가하라.")
            sys.exit(1)

    def _create_study_dir(self):
        (STUDY / "projects" / self.name).mkdir(parents=True, exist_ok=True)
        (STUDY / "약점노트" / "active").mkdir(parents=True, exist_ok=True)

    def _create_readme(self):
        readme = STUDY / "projects" / self.name / "README.md"
        if readme.exists():
            return
        readme.write_text(
            f"# {self.name} 학습 가이드\n\n"
            "## 구현 순서\n- [ ] (document_skill 최초 실행 시 자동 채워짐)\n\n"
            "## 막혔을 때 참조 매핑\n| 단계 | 볼 파일 |\n|------|--------|\n\n"
            "## 개념 파일 현황\n| 파일 | 상태 |\n|------|------|\n"
            "> ✅ = 파일 존재 / 📝 = 미작성\n",
            encoding="utf-8",
        )

    def _create_scaffolds(self):
        scaffold_dir = STUDY / "projects" / self.name / "scaffolds"
        scaffold_dir.mkdir(parents=True, exist_ok=True)

        exp_dir = STUDY / "projects" / self.name / "experiments"
        exp_dir.mkdir(parents=True, exist_ok=True)

        starter = scaffold_dir / "00_starter.py"
        if not starter.exists():
            starter.write_text(
                f'"""\nScaffold 00: Starter — {self.name}\n'
                "목적: 데이터 로딩 → 모델 → 학습 루프 뼈대 작성\n"
                "완료 기준: if __name__ == '__main__' 블록이 에러 없이 실행됨\n"
                '"""\n'
                "import torch\n"
                "import torch.nn as nn\n"
                "from torch.utils.data import Dataset, DataLoader\n"
                "import os\n\n"
                'DEVICE = "cuda" if torch.cuda.is_available() else "cpu"\n\n\n'
                "# TODO(human): Dataset 구현\n"
                "class MyDataset(Dataset):\n"
                "    def __init__(self):\n"
                "        pass\n\n"
                "    def __len__(self):\n"
                "        pass\n\n"
                "    def __getitem__(self, idx):\n"
                "        pass\n\n\n"
                "# TODO(human): Model 구현\n"
                "class MyModel(nn.Module):\n"
                "    def __init__(self):\n"
                "        super().__init__()\n\n"
                "    def forward(self, x):\n"
                "        pass\n\n\n"
                "def train_one_epoch(model, loader, criterion, optimizer):\n"
                "    model.train()\n"
                "    total_loss = 0.0\n"
                "    for batch in loader:\n"
                "        # TODO(human): forward → loss → backward → step\n"
                "        pass\n"
                "    return total_loss / len(loader)\n\n\n"
                'if __name__ == "__main__":\n'
                "    # 구현 후 여기서 실행 확인\n"
                "    model = MyModel().to(DEVICE)\n"
                "    print(model)\n",
                encoding="utf-8",
            )

        exp_log = exp_dir / "log.md"
        if not exp_log.exists():
            exp_log.write_text(
                f"# 실험 로그 — {self.name}\n\n"
                "> 각 Phase 결과를 여기에 기록. Claude가 세션 중 채워줌.\n\n"
                "## Phase 1\n\n| 설정 | val_loss | 비고 |\n|------|----------|------|\n\n"
                "## Phase 2\n\n| 설정 | val_loss | 비고 |\n|------|----------|------|\n\n"
                "## Phase 3\n\n| 설정 | val_loss | 비고 |\n|------|----------|------|\n\n"
                "## 최종 선택\n\n- Loss: \n- 모델: \n- LR: \n",
                encoding="utf-8",
            )

    def _init_zero_state(self):
        """study/ 최상위 파일 없으면 생성 (첫 사용자 zero-state 대응)"""
        queue = STUDY / "session_queue.md"
        if not queue.exists():
            queue.write_text(
                "# 세션 큐\n> 미완료 상태 관리.\n\n## 현재 큐\n\n_(없음)_\n",
                encoding="utf-8",
            )

        weakness_readme = STUDY / "약점노트" / "README.md"
        if not weakness_readme.exists():
            weakness_readme.write_text(
                f"# 약점노트 현황\n\n> SM-2 기반 간격 반복\n\n"
                f"_updated: {self.today}_\n\n"
                "## 복습 대기\n\n없음\n\n"
                "## 전체 active\n\n"
                "| 개념 | 프로젝트 | 레벨 | 연속정답 | 다음복습 |\n"
                "|------|----------|------|----------|----------|\n\n"
                "## 마스터 완료\n\n없음\n",
                encoding="utf-8",
            )

        insight = STUDY / "학습인사이트.md"
        if not insight.exists():
            insight.write_text(
                f"# 학습 인사이트\n\n_updated: {self.today}_\n\n"
                "(첫 세션 종료 후 자동 업데이트됨)\n",
                encoding="utf-8",
            )

    def _update_index(self):
        index = STUDY / "index.md"
        header = f"# Study Index\n_updated: {self.today}_\n\n"
        section = (
            f"## {self.name}\n\n"
            "| 페이지 | 타입 | 요약 | 약점 |\n"
            "|--------|------|------|------|\n"
        )
        if not index.exists():
            index.write_text(header + section, encoding="utf-8")
        else:
            content = index.read_text(encoding="utf-8")
            if f"## {self.name}" not in content:
                index.write_text(content.rstrip() + f"\n\n{section}", encoding="utf-8")

    def _update_log(self):
        log = STUDY / "log.md"
        entry = f"## [{self.today}] init | {self.name} bootstrapped\n"
        if not log.exists():
            log.write_text(
                '# Learning Log\n_append-only. grep "^## " log.md 로 파싱 가능._\n\n' + entry,
                encoding="utf-8",
            )
        else:
            with log.open("a", encoding="utf-8") as f:
                f.write(entry)

    def _update_state(self):
        state_path = STUDY / "state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
        else:
            state = {"version": "1.0", "last_lint": None, "active_project": None, "projects": {}}
        state["active_project"] = self.name
        state["projects"][self.name] = {
            "status": "in_progress",
            "bootstrapped_at": self.today,
            "concepts_completed": 0,
            "concepts_total": 0,
        }
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _print_summary(self):
        print(f"\n{'='*50}")
        print(f" 완료: {self.name}")
        print(f"  study/projects/{self.name}/README.md 생성됨")
        print(f"  study/projects/{self.name}/scaffolds/00_starter.py 생성됨")
        print(f"  study/projects/{self.name}/experiments/log.md 생성됨")
        print(f"  study/index.md 섹션 추가됨")
        print(f"  study/log.md init 항목 기록됨")
        print(f"  study/state.json 업데이트됨")
        print(f"\n다음 단계:")
        print(f"  python3 scripts/wiki_lint.py")
        print(f"{'='*50}\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/bootstrap.py <project_name>")
        sys.exit(1)
    WikiBootstrapper(sys.argv[1]).run()
