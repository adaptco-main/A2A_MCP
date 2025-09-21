from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from app.orchestrator_agent import CoreOrchestratorMergeAgent


def run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )


def configure_repo(repo: Path) -> None:
    run_git(["config", "user.name", "Test Agent"], cwd=repo)
    run_git(["config", "user.email", "agent@example.com"], cwd=repo)


class CoreOrchestratorMergeAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.remote = base / "remote.git"
        self.upstream = base / "upstream"
        self.agent_repo = base / "agent"

        self.upstream.mkdir()
        run_git(["init"], cwd=self.upstream)
        configure_repo(self.upstream)

        (self.upstream / "README.md").write_text("core orchestrator\n")
        run_git(["add", "README.md"], cwd=self.upstream)
        run_git(["commit", "-m", "initial"], cwd=self.upstream)
        run_git(["branch", "-M", "main"], cwd=self.upstream)

        run_git(["init", "--bare", str(self.remote)], cwd=base)
        run_git(["remote", "add", "origin", str(self.remote)], cwd=self.upstream)
        run_git(["push", "-u", "origin", "main"], cwd=self.upstream)

        subprocess.run(
            ["git", "--git-dir", str(self.remote), "symbolic-ref", "HEAD", "refs/heads/main"],
            check=True,
            text=True,
            capture_output=True,
        )

        run_git(["checkout", "-b", "feature/alpha"], cwd=self.upstream)
        (self.upstream / "feature.txt").write_text("alpha\n")
        run_git(["add", "feature.txt"], cwd=self.upstream)
        run_git(["commit", "-m", "feature alpha"], cwd=self.upstream)
        run_git(["push", "-u", "origin", "feature/alpha"], cwd=self.upstream)

        run_git(["checkout", "main"], cwd=self.upstream)
        run_git(["checkout", "-b", "chore/docs"], cwd=self.upstream)
        (self.upstream / "docs.md").write_text("docs\n")
        run_git(["add", "docs.md"], cwd=self.upstream)
        run_git(["commit", "-m", "docs"], cwd=self.upstream)
        run_git(["push", "-u", "origin", "chore/docs"], cwd=self.upstream)
        run_git(["checkout", "main"], cwd=self.upstream)

        run_git(["clone", str(self.remote), str(self.agent_repo)], cwd=base)
        configure_repo(self.agent_repo)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_dry_run_reports_feature_branches(self) -> None:
        agent = CoreOrchestratorMergeAgent(self.agent_repo)
        report = agent.pull_and_merge(target_branch="main", include_prefixes=("feature/",), dry_run=True)

        self.assertEqual(report.inbound_branches, ["feature/alpha"])
        self.assertEqual(len(report.outcomes), 1)
        outcome = report.outcomes[0]
        self.assertEqual(outcome.remote_ref, "origin/feature/alpha")
        self.assertEqual(outcome.skipped_reason, "dry-run")
        self.assertFalse(outcome.merged)

    def test_merge_applies_feature_branch(self) -> None:
        agent = CoreOrchestratorMergeAgent(self.agent_repo)
        report = agent.pull_and_merge(target_branch="main", include_prefixes=("feature/",))

        self.assertEqual([o.branch for o in report.outcomes], ["feature/alpha"])
        outcome = report.outcomes[0]
        self.assertTrue(outcome.merged)
        self.assertIsNone(outcome.error)

        status = run_git(["status", "--porcelain"], cwd=self.agent_repo)
        self.assertEqual(status.stdout.strip(), "")

        main_contents = (self.agent_repo / "feature.txt").read_text()
        self.assertIn("alpha", main_contents)
        self.assertFalse((self.agent_repo / "docs.md").exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
