"""Commit DAG graph layout and visual branch track generator."""

from __future__ import annotations
from typing import Dict, List, Tuple
from clankit.git.models import CommitNode


# Distinct visual palette for commit lanes (matching SourceTree's vibrant tracks)
LANE_COLORS: List[Tuple[int, int, int]] = [
    (80, 160, 255),   # Blue
    (80, 220, 120),   # Green
    (255, 170, 50),   # Orange
    (230, 80, 200),   # Magenta
    (170, 100, 255),  # Purple
    (255, 220, 60),   # Yellow
    (50, 210, 210),   # Cyan
    (255, 100, 100),  # Coral Red
]


class CommitGraphLayout:
    """Computes branch lanes and topological graph tracks for commit nodes."""

    @classmethod
    def layout(cls, commits: List[CommitNode]) -> None:
        """Assigns lanes and routes to each CommitNode in place."""
        if not commits:
            return

        lanes: List[str | None] = []  # lane index -> commit hash expected next

        for node in commits:
            # 1. Determine which lane this node occupies
            assigned_lane = -1
            for idx, expected_hash in enumerate(lanes):
                if expected_hash == node.hash:
                    assigned_lane = idx
                    break

            if assigned_lane == -1:
                # Find first empty lane or create new lane
                try:
                    assigned_lane = lanes.index(None)
                    lanes[assigned_lane] = node.hash
                except ValueError:
                    assigned_lane = len(lanes)
                    lanes.append(node.hash)

            node.lane = assigned_lane

            # 2. Update lanes for parents
            parents = node.parents
            if not parents:
                # Root commit: clear this lane
                lanes[assigned_lane] = None
            else:
                # First parent continues on this lane
                lanes[assigned_lane] = parents[0]

                # Subsequent parents (merges) need lanes
                for p_hash in parents[1:]:
                    if p_hash not in lanes:
                        # Find an empty slot or append
                        try:
                            empty_idx = lanes.index(None)
                            lanes[empty_idx] = p_hash
                        except ValueError:
                            lanes.append(p_hash)

            # Trim trailing None lanes
            while lanes and lanes[-1] is None:
                lanes.pop()

    @classmethod
    def get_lane_color(cls, lane: int) -> Tuple[int, int, int]:
        """Returns RGB color tuple for a branch lane."""
        return LANE_COLORS[lane % len(LANE_COLORS)]

    @classmethod
    def format_ascii_graph(cls, node: CommitNode, max_lane_count: int = 5) -> str:
        """Generate a concise visual ASCII glyph representation of the node's position."""
        lane = node.lane
        chars = []
        for i in range(max(lane + 1, min(max_lane_count, 8))):
            if i == lane:
                chars.append("●")
            else:
                chars.append("│" if i < lane else " ")
        return " ".join(chars)
