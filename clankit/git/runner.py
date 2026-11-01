"""Git CLI command runner.

Executes standard git commands via subprocess, maintaining complete credential neutrality
and logging all CLI interactions for user transparency.
"""

from __future__ import annotations
import os
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Optional
from clankit.git.models import CommandResult


class GitRunner:
    """Subprocess executor for Git commands."""

    def __init__(self, git_path: str = "git", max_workers: int = 4):
        self.git_path = git_path
        self._history: List[CommandResult] = []
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="GitRunner")
        self._listeners: List[Callable[[CommandResult], None]] = []

    def add_listener(self, listener: Callable[[CommandResult], None]) -> None:
        """Register a callback for when commands finish executing."""
        with self._lock:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[CommandResult], None]) -> None:
        """Unregister a command listener."""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def _notify(self, result: CommandResult) -> None:
        with self._lock:
            self._history.append(result)
            listeners_copy = list(self._listeners)
        for listener in listeners_copy:
            try:
                listener(result)
            except Exception:
                pass

    def get_history(self) -> List[CommandResult]:
        """Return a copy of the command execution history."""
        with self._lock:
            return list(self._history)

    def clear_history(self) -> None:
        """Clear execution history."""
        with self._lock:
            self._history.clear()

    def run(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = 60.0,
        stdin_input: Optional[str] = None,
    ) -> CommandResult:
        """Execute a git CLI command synchronously.

        Credentials: Uses the host environment as-is without modification.
        """
        full_cmd = [self.git_path] + args
        start_time = time.time()
        start_mono = time.monotonic()

        # Merge environment with host os.environ to guarantee SSH_AUTH_SOCK,
        # GIT_SSH, HOME, and credential helpers are strictly preserved.
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        try:
            proc = subprocess.run(
                full_cmd,
                cwd=cwd,
                env=process_env,
                input=stdin_input,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout,
            )
            stdout = proc.stdout
            stderr = proc.stderr
            returncode = proc.returncode
        except subprocess.TimeoutExpired as te:
            stdout = te.stdout or ""
            stderr = (te.stderr or "") + f"\n[Clankit Timeout]: Command timed out after {timeout} seconds."
            returncode = -1
        except Exception as e:
            stdout = ""
            stderr = f"[Clankit Execution Error]: {e}"
            returncode = -1

        duration_ms = (time.monotonic() - start_mono) * 1000.0
        result = CommandResult(
            command=full_cmd,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timestamp=start_time,
            cwd=cwd or os.getcwd(),
        )

        self._notify(result)
        return result

    def run_async(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        callback: Optional[Callable[[CommandResult], None]] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = 120.0,
    ) -> None:
        """Execute a git CLI command asynchronously in the background thread pool."""
        def _worker():
            res = self.run(args, cwd=cwd, env=env, timeout=timeout)
            if callback:
                callback(res)

        self._executor.submit(_worker)

    def find_repo_root(self, path: Optional[str] = None) -> Optional[str]:
        """Find the root directory of the Git repository for a path."""
        target_path = path or os.getcwd()
        res = self.run(["rev-parse", "--show-toplevel"], cwd=target_path)
        if res.success and res.stdout.strip():
            return res.stdout.strip()
        return None
