from __future__ import annotations

import logging
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence

logger = logging.getLogger("core_orchestrator.merge_agent")


@dataclass
class GitCommandResult:
    """Container for information returned from a Git subprocess."""

    command: Sequence[str]
    stdout: str
    stderr: str
    returncode: int


class GitCommandError(RuntimeError):
    """Raised when a Git subprocess exits with a non-zero status."""

    def __init__(
        self,
        command: Sequence[str],
        returncode: int,
        stdout: str,
        stderr: str,
    ) -> None:
        pretty = " ".join(shlex.quote(arg) for arg in command)
        message = f"git command `{pretty}` failed with exit code {returncode}"
        if stderr:
            message = f"{message}: {stderr.strip()}"
        super().__init__(message)
        self.command = tuple(command)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class DirtyWorktreeError(RuntimeError):
    """Raised when the repository contains uncommitted changes."""


@dataclass
class MergeOutcome:
    """Result for a single branch merge attempt."""

    branch: str
    remote_ref: str
    merged: bool = False
    skipped_reason: str | None = None
    error: str | None = None
    commands: List[GitCommandResult] = field(default_factory=list)


@dataclass
class MergeReport:
    """Aggregate report returned from :meth:`CoreOrchestratorMergeAgent.pull_and_merge`."""

    target_branch: str
    inbound_branches: List[str]
    setup_commands: List[GitCommandResult] = field(default_factory=list)
    outcomes: List[MergeOutcome] = field(default_factory=list)

    def merged_branches(self) -> List[str]:
        """Return the list of branches that were successfully merged."""

        return [outcome.branch for outcome in self.outcomes if outcome.merged]


class CoreOrchestratorMergeAgent:
    """
    Automates pulling and merging inbound branches for the Core Orchestrator repo.

    The agent runs Git commands directly against the repository on disk, enforcing
    clean worktree invariants, performing targeted merges, and optionally pushing
    the results back to the remote.
    """

    def __init__(self, repo_path: Path | str, remote: str = "origin") -> None:
        self.repo_path = Path(repo_path).resolve()
        self.remote = remote
        self._ensure_repository()

    def pull_and_merge(
        self,
        *,
        target_branch: str = "main",
        include_prefixes: Iterable[str] | None = None,
        exclude_branches: Iterable[str] | None = None,
        dry_run: bool = False,
        push_after_merge: bool = False,
        stop_on_failure: bool = True,
    ) -> MergeReport:
        """
        Fetch inbound branches, merge them into *target_branch*, and optionally push.

        Args:
            target_branch: Branch that should receive the inbound merges.
            include_prefixes: Optional iterable of branch prefixes to include. If
                omitted, all remote branches except the target are considered.
            exclude_branches: Explicit branch names to ignore.
            dry_run: When ``True`` the method produces a merge plan without
                executing the merge commands.
            push_after_merge: Push the target branch to the remote once a merge
                succeeds.
            stop_on_failure: When ``True`` (default) abort subsequent merges after
                the first failure. Remaining branches will be marked as blocked.

        Returns:
            A :class:`MergeReport` describing the work performed or planned.
        """

        self._assert_clean_worktree()
        report = MergeReport(target_branch=target_branch, inbound_branches=[])

        report.setup_commands.append(self._fetch_remote())

        remote_branches = self._list_remote_branches()
        filtered = self._filter_branches(
            remote_branches,
            target_branch=target_branch,
            include_prefixes=tuple(include_prefixes) if include_prefixes else None,
            exclude_branches=set(exclude_branches or []),
        )
        report.inbound_branches.extend(filtered)

        checkout_cmd = self._run_git("checkout", target_branch)
        report.setup_commands.append(checkout_cmd)
        pull_cmd = self._run_git("pull", self.remote, target_branch)
        report.setup_commands.append(pull_cmd)

        if dry_run:
            for branch in filtered:
                report.outcomes.append(
                    MergeOutcome(
                        branch=branch,
                        remote_ref=f"{self.remote}/{branch}",
                        skipped_reason="dry-run",
                    )
                )
            return report

        for index, branch in enumerate(filtered):
            remote_ref = f"{self.remote}/{branch}"
            outcome = MergeOutcome(branch=branch, remote_ref=remote_ref)
            try:
                merge_result = self._run_git("merge", "--no-ff", remote_ref)
                outcome.commands.append(merge_result)
                outcome.merged = True

                if push_after_merge:
                    push_result = self._run_git("push", self.remote, target_branch)
                    outcome.commands.append(push_result)
            except GitCommandError as error:  # pragma: no cover - exercised in tests
                outcome.error = str(error)
                outcome.commands.append(
                    GitCommandResult(
                        command=error.command,
                        stdout=error.stdout,
                        stderr=error.stderr,
                        returncode=error.returncode,
                    )
                )
                logger.error("Merge failed for branch %s: %s", branch, error)

                if self._merge_in_progress():
                    self._run_git("merge", "--abort", check=False)

                report.outcomes.append(outcome)

                if stop_on_failure:
                    for blocked in filtered[index + 1 :]:
                        report.outcomes.append(
                            MergeOutcome(
                                branch=blocked,
                                remote_ref=f"{self.remote}/{blocked}",
                                skipped_reason="blocked-by-failure",
                            )
                        )
                    break
                continue

            report.outcomes.append(outcome)

        return report

    def _fetch_remote(self) -> GitCommandResult:
        return self._run_git("fetch", "--prune", self.remote)

    def _list_remote_branches(self) -> List[str]:
        result = self._run_git(
            "for-each-ref",
            "--format=%(refname:strip=3)",
            f"refs/remotes/{self.remote}",
        )
        branches = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return sorted(branch for branch in branches if branch != "HEAD")

    @staticmethod
    def _filter_branches(
        branches: Iterable[str],
        *,
        target_branch: str,
        include_prefixes: tuple[str, ...] | None,
        exclude_branches: set[str],
    ) -> List[str]:
        filtered: List[str] = []
        for branch in branches:
            if branch == target_branch or branch in exclude_branches:
                continue
            if include_prefixes and not any(branch.startswith(prefix) for prefix in include_prefixes):
                continue
            filtered.append(branch)
        return filtered

    def _ensure_repository(self) -> None:
        if not self.repo_path.exists():
            raise FileNotFoundError(f"repository path does not exist: {self.repo_path}")
        git_dir = self.repo_path / ".git"
        if not git_dir.is_dir():
            raise FileNotFoundError(f"{self.repo_path} is not a git repository")

    def _assert_clean_worktree(self) -> None:
        status = self._run_git("status", "--porcelain")
        if status.stdout:
            raise DirtyWorktreeError("repository contains uncommitted changes")

    def _merge_in_progress(self) -> bool:
        return (self.repo_path / ".git" / "MERGE_HEAD").exists()

    def _run_git(self, *args: str, check: bool = True) -> GitCommandResult:
        command = ("git",) + args
        logger.debug("Executing git command: %s", " ".join(shlex.quote(arg) for arg in command))
        proc = subprocess.run(
            command,
            cwd=self.repo_path,
            text=True,
            capture_output=True,
            check=False,
        )
        result = GitCommandResult(
            command=command,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            returncode=proc.returncode,
        )
        if check and proc.returncode != 0:
            raise GitCommandError(command, proc.returncode, result.stdout, result.stderr)
        return result


__all__ = [
    "CoreOrchestratorMergeAgent",
    "DirtyWorktreeError",
    "GitCommandError",
    "GitCommandResult",
    "MergeOutcome",
    "MergeReport",
]
