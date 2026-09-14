"""Lexical tree and the LCA-based semantic distance metric (SEC-03 / WP01).

Implements the tree metric over lowest common ancestors:

    d_T(x, y) = depth(x) + depth(y) - 2 * depth(LCA(x, y))

computed in O(depth) time by walking each node's ancestor chain to its
tree root, rather than via floating-point embedding similarity.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass


@dataclass
class LexicalNode:
    """A rooted node in the semantic lexicon tree.

    Corresponds to the formal lexical object L_x = (x, D_x, C_x, R_x, P_x, Q_x);
    R_x (relational edges) is realised as tree parent/child structure here.
    Provenance/qualification (P_x, Q_x) are left to callers — this class
    only models the tree structure the distance metric needs.
    """

    symbol: str
    definition: str = ""
    context: str = ""
    parent: str | None = None


class LexicalTree:
    """A rooted tree (or forest) of LexicalNode, with O(depth) LCA distance."""

    def __init__(self) -> None:
        self._nodes: dict[str, LexicalNode] = {}

    def add_root(self, symbol: str, definition: str = "", context: str = "") -> None:
        if symbol in self._nodes:
            raise ValueError(f"node already exists: {symbol}")
        self._nodes[symbol] = LexicalNode(symbol=symbol, definition=definition, context=context, parent=None)

    def add_child(self, symbol: str, parent: str, definition: str = "", context: str = "") -> None:
        if symbol in self._nodes:
            raise ValueError(f"node already exists: {symbol}")
        if parent not in self._nodes:
            raise KeyError(f"no such parent node: {parent}")
        self._nodes[symbol] = LexicalNode(symbol=symbol, definition=definition, context=context, parent=parent)

    def __contains__(self, symbol: str) -> bool:
        return symbol in self._nodes

    def _get(self, symbol: str) -> LexicalNode:
        """Internal accessor returning the LIVE node — never expose this
        return value to callers outside the class; use `get()` instead.
        """
        try:
            return self._nodes[symbol]
        except KeyError as exc:
            raise KeyError(f"no such lexical node: {symbol}") from exc

    def get(self, symbol: str) -> LexicalNode:
        """A defensive copy of the node. Mutating it (e.g. reassigning
        `.parent`) cannot corrupt the tree or create a cycle, since the
        tree never reads this object back — internal traversal uses its
        own accessor.
        """
        return dataclasses.replace(self._get(symbol))

    def depth(self, symbol: str) -> int:
        """Distance from `symbol` up to its root. O(depth)."""
        node = self._get(symbol)
        d = 0
        while node.parent is not None:
            node = self._get(node.parent)
            d += 1
        return d

    def ancestors(self, symbol: str) -> list[str]:
        """`symbol`'s ancestor chain, symbol first, root last. O(depth)."""
        node = self._get(symbol)
        chain = [symbol]
        while node.parent is not None:
            chain.append(node.parent)
            node = self._get(node.parent)
        return chain

    def lca(self, x: str, y: str) -> str:
        """Lowest common ancestor of x and y. O(depth)."""
        self._get(x)
        self._get(y)
        x_ancestors = self.ancestors(x)
        y_ancestor_set = set(self.ancestors(y))
        for ancestor in x_ancestors:
            if ancestor in y_ancestor_set:
                return ancestor
        raise ValueError(f"{x!r} and {y!r} are not in the same tree (no common ancestor)")

    def distance(self, x: str, y: str) -> int:
        """d_T(x, y) = depth(x) + depth(y) - 2 * depth(LCA(x, y))."""
        if x == y:
            self.get(x)
            return 0
        common = self.lca(x, y)
        return self.depth(x) + self.depth(y) - 2 * self.depth(common)
