from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from backend.graph.artifacts import (
    GENERATED_GIT_HANDOFF_ROOT,
    GENERATED_ROBOT_ROOT,
    PROJECT_ROOT,
    relative_to_project,
    slug,
)
from backend.graph.state import TestContext


LOCAL_GH = PROJECT_ROOT / ".tools" / "gh-extract" / "bin" / "gh.exe"


@dataclass(frozen=True)
class GitExecutionResult:
    handoff_path: Path
    status: str
    branch: str
    commit_sha: str | None = None
    pr_url: str | None = None
    errors: list[str] = field(default_factory=list)


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _run_gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    command = str(LOCAL_GH) if LOCAL_GH.is_file() else "gh"
    return subprocess.run(
        [command, *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _command_error(command: str, result: subprocess.CompletedProcess[str]) -> str:
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    return f"{command} failed with exit code {result.returncode}: {output.strip()}"


def _is_git_repo() -> bool:
    if shutil.which("git") is None:
        return False
    return _run_git(["rev-parse", "--is-inside-work-tree"]).returncode == 0


def _branch_exists(branch: str) -> bool:
    return _run_git(["rev-parse", "--verify", branch]).returncode == 0


def _remote_exists(remote: str = "origin") -> bool:
    return _run_git(["remote", "get-url", remote]).returncode == 0


def _current_branch() -> str | None:
    result = _run_git(["branch", "--show-current"])
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None


def _write_handoff_payload(payload: dict[str, object], context_id: str) -> Path:
    GENERATED_GIT_HANDOFF_ROOT.mkdir(parents=True, exist_ok=True)
    handoff_path = GENERATED_GIT_HANDOFF_ROOT / f"{context_id}.json"
    handoff_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return Path(relative_to_project(handoff_path))


def _handoff_payload(
    *,
    context: TestContext,
    reviewed_by: str,
    branch: str,
    pr_title: str,
    pr_body: str,
    status: str,
    commit_sha: str | None = None,
    pr_url: str | None = None,
    errors: list[str] | None = None,
) -> dict[str, object]:
    assert context.ticket is not None
    return {
        "context_id": context.context_id,
        "ticket_id": context.ticket.id,
        "reviewed_by": reviewed_by,
        "branch": branch,
        "commit_sha": commit_sha,
        "pr_url": pr_url,
        "pr_title": pr_title,
        "pr_body": pr_body,
        "files": context.approval.review_items if context.approval else [],
        "status": status,
        "errors": errors or [],
    }


def _safe_review_items(items: list[str], errors: list[str]) -> list[str]:
    """Return only the review items that resolve inside GENERATED_ROBOT_ROOT.

    ``git add -f`` bypasses .gitignore, so each path must be re-validated at
    handoff time (W8) -- a traversal sequence, absolute path, or symlink that
    escapes the generated robot root is dropped and recorded as an error rather
    than force-added. Operates on the already-stored project-relative review
    item strings, mirroring resolve_robot_file's containment check.
    """
    robot_root = GENERATED_ROBOT_ROOT.resolve()
    safe: list[str] = []
    for item in items:
        candidate = Path(item)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        try:
            resolved = candidate.resolve()
            resolved.relative_to(robot_root)
        except (ValueError, OSError):
            errors.append(
                f"Refusing to stage '{item}': path escapes the generated robot "
                "root (possible traversal or symlink); dropped from handoff."
            )
            continue
        safe.append(item)
    return safe


def create_git_handoff(context: TestContext, reviewed_by: str) -> GitExecutionResult:
    if context.approval is None:
        raise ValueError("Git handoff requires approval state")
    if context.ticket is None:
        raise ValueError("Git handoff requires ticket data")
    branch = context.approval.git_branch or f"aegis/{slug(context.ticket.id)}"
    original_branch = _current_branch()
    pr_title = f"[AegisQA] {context.ticket.id} - {context.ticket.title}"
    pr_body = (
        f"Generated Robot Framework automation for {context.ticket.id}.\n\n"
        f"Reviewer: {reviewed_by}\n"
        f"Files:\n"
        + "\n".join(f"- {item}" for item in context.approval.review_items)
    )

    if not _is_git_repo():
        error = "PROJECT_ROOT is not inside a Git work tree; branch, commit, and PR were not created."
        handoff_path = _write_handoff_payload(
            _handoff_payload(
                context=context,
                reviewed_by=reviewed_by,
                branch=branch,
                pr_title=pr_title,
                pr_body=pr_body,
                status="blocked",
                errors=[error],
            ),
            context.context_id,
        )
        return GitExecutionResult(
            handoff_path=handoff_path,
            status="blocked",
            branch=branch,
            errors=[error],
        )

    errors: list[str] = []
    switch_args = ["switch", branch] if _branch_exists(branch) else ["switch", "-c", branch]
    switch_result = _run_git(switch_args)
    if switch_result.returncode != 0:
        errors.append(_command_error(f"git {' '.join(switch_args)}", switch_result))

    # W8: re-validate every review item resolves *inside* the generated robot
    # root before force-adding. `git add -f` bypasses .gitignore, so a reviewer-
    # or context-controlled path that escaped the artifact root (traversal,
    # absolute path, symlink) could otherwise stage arbitrary files. Items that
    # fail the check are dropped and recorded as errors rather than added.
    safe_items = _safe_review_items(context.approval.review_items, errors)

    if not errors and safe_items:
        add_result = _run_git(["add", "-f", "--", *safe_items])
        if add_result.returncode != 0:
            errors.append(_command_error("git add", add_result))

    commit_sha: str | None = None
    if not errors:
        diff_result = _run_git(["diff", "--cached", "--quiet"])
        if diff_result.returncode == 0:
            rev_result = _run_git(["rev-parse", "HEAD"])
            if rev_result.returncode == 0:
                commit_sha = rev_result.stdout.strip()
        else:
            commit_message = (
                f"aegis: {context.ticket.id} generated Robot automation "
                f"[approved by {reviewed_by}]"
            )
            commit_result = _run_git(["commit", "-m", commit_message])
            if commit_result.returncode != 0:
                errors.append(_command_error("git commit", commit_result))
            else:
                rev_result = _run_git(["rev-parse", "HEAD"])
                if rev_result.returncode == 0:
                    commit_sha = rev_result.stdout.strip()

    if not errors and _remote_exists():
        push_result = _run_git(["push", "-u", "origin", branch])
        if push_result.returncode != 0:
            errors.append(_command_error("git push -u origin", push_result))

    pr_url: str | None = None
    gh_available = shutil.which("gh") is not None or LOCAL_GH.is_file()
    if not errors and gh_available:
        pr_result = _run_gh(["pr", "create", "--title", pr_title, "--body", pr_body, "--head", branch])
        if pr_result.returncode == 0:
            pr_url = pr_result.stdout.strip().splitlines()[-1]
        else:
            errors.append(_command_error("gh pr create", pr_result))

    if original_branch is not None and original_branch != branch:
        restore_result = _run_git(["switch", original_branch])
        if restore_result.returncode != 0:
            errors.append(_command_error(f"git switch {original_branch}", restore_result))

    status = "blocked" if errors else "completed"
    handoff_path = _write_handoff_payload(
        _handoff_payload(
            context=context,
            reviewed_by=reviewed_by,
            branch=branch,
            pr_title=pr_title,
            pr_body=pr_body,
            status=status,
            commit_sha=commit_sha,
            pr_url=pr_url,
            errors=errors,
        ),
        context.context_id,
    )
    return GitExecutionResult(
        handoff_path=handoff_path,
        status=status,
        branch=branch,
        commit_sha=commit_sha,
        pr_url=pr_url,
        errors=errors,
    )
