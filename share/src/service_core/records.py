from __future__ import annotations

from dataclasses import dataclass

from .curve import Curve, Point


@dataclass(frozen=True)
class Metadata:
    k: int
    z: int


class RecordFormat:
    def __init__(self, curve: Curve, window: int, item_limit: int):
        self.curve = curve
        self.window = window
        self.item_limit = item_limit

    def encode_x(self, m: int, k: int) -> int:
        self._check_message_and_k(m, k)
        x = m * self.window + k
        if x >= self.curve.F.p:
            raise ValueError("record out of range")
        return x

    def check(self, m: int, P: Point, metadata: Metadata) -> None:
        x = self.encode_x(m, metadata.k)

        if P.x != x:
            raise ValueError("invalid record")

        self.curve.F.check(metadata.z, "z")
        if P.y != (metadata.z * metadata.z) % self.curve.F.p:
            raise ValueError("invalid metadata")

        if not self.curve.is_on_curve(P):
            raise ValueError("invalid point")

    def _check_message_and_k(self, m: int, k: int) -> None:
        if not isinstance(m, int) or isinstance(m, bool):
            raise TypeError("m must be an integer")
        if not isinstance(k, int) or isinstance(k, bool):
            raise TypeError("k must be an integer")

        if not (0 <= m < self.item_limit):
            raise ValueError("m out of range")
        if not (0 <= k < self.window):
            raise ValueError("k out of range")
