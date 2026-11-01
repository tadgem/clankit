"""Unit tests for Git subprocess runner."""

from clankit.git.runner import GitRunner


def test_runner_git_version():
    runner = GitRunner()
    result = runner.run(["--version"])
    assert result.success is True
    assert "git version" in result.stdout
    assert result.returncode == 0
    assert result.duration_ms > 0


def test_runner_history_and_listeners():
    runner = GitRunner()
    events = []

    def _listener(res):
        events.append(res)

    runner.add_listener(_listener)
    res = runner.run(["--version"])

    assert len(events) == 1
    assert events[0].command[1] == "--version"
    assert len(runner.get_history()) == 1

    runner.clear_history()
    assert len(runner.get_history()) == 0


def test_runner_invalid_command():
    runner = GitRunner()
    res = runner.run(["__non_existent_subcommand__"])
    assert res.success is False
    assert res.returncode != 0
    assert "not a git command" in res.stderr.lower() or "is not a git command" in res.stderr.lower()
