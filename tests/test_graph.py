"""Unit tests for Git commit graph layout."""

from clankit.git.models import CommitNode
from clankit.ui.graph_renderer import CommitGraphLayout


def test_linear_commit_graph():
    c1 = CommitNode(hash="aaa", short_hash="aaa", parents=[], author_name="", author_email="", date="", subject="")
    c2 = CommitNode(hash="bbb", short_hash="bbb", parents=["aaa"], author_name="", author_email="", date="", subject="")
    c3 = CommitNode(hash="ccc", short_hash="ccc", parents=["bbb"], author_name="", author_email="", date="", subject="")

    commits = [c3, c2, c1]  # topo order: latest first
    CommitGraphLayout.layout(commits)

    # In a linear history, every commit should be in lane 0
    assert c3.lane == 0
    assert c2.lane == 0
    assert c1.lane == 0


def test_divergent_branch_commit_graph():
    # c1 (root) -> c2 (branch A)
    #           -> c3 (branch B)
    # c4 (merge of c2 and c3)
    c1 = CommitNode(hash="c1", short_hash="c1", parents=[], author_name="", author_email="", date="", subject="")
    c2 = CommitNode(hash="c2", short_hash="c2", parents=["c1"], author_name="", author_email="", date="", subject="")
    c3 = CommitNode(hash="c3", short_hash="c3", parents=["c1"], author_name="", author_email="", date="", subject="")
    c4 = CommitNode(hash="c4", short_hash="c4", parents=["c2", "c3"], author_name="", author_email="", date="", subject="")

    commits = [c4, c3, c2, c1]
    CommitGraphLayout.layout(commits)

    assert c4.lane == 0
    # c3 should be placed in another lane (e.g. 1)
    assert c3.lane != c4.lane or c2.lane != c3.lane


def test_ascii_glyphs():
    c = CommitNode(hash="c1", short_hash="c1", parents=[], author_name="", author_email="", date="", subject="", lane=1)
    glyph = CommitGraphLayout.format_ascii_graph(c, max_lane_count=3)
    assert "●" in glyph
