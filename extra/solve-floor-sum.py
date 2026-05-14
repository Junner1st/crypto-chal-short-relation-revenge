from __future__ import annotations

import json
from typing import Iterable

from pwn import context, remote

HOST = "127.0.0.1"
PORT = 1342

context.log_level = "error"

def call(io, cmd: str, payload: dict | None = None) -> dict:
    if payload is None:
        io.sendline(cmd.encode())
    else:
        line = cmd + " " + json.dumps(payload, separators=(",", ":"))
        io.sendline(line.encode())

    res = json.loads(io.recvline().decode())
    io.recvuntil(b"> ")
    return res


def floor_sum(n: int, m: int, a: int, b: int) -> int:
    """Return sum_{0 <= i < n} floor((a*i + b) / m)."""
    assert n >= 0 and m > 0 and a >= 0 and b >= 0
    ans = 0
    while True:
        if a >= m:
            ans += (n - 1) * n * (a // m) // 2
            a %= m
        if b >= m:
            ans += n * (b // m)
            b %= m

        y = a * n + b
        if y < m:
            return ans

        n = y // m
        b = y % m
        a, m = m, a


def count_mod_lt(n: int, mod: int, a: int, b: int, limit: int) -> int:
    """
    Count i in [0, n) such that (a*i + b) mod mod < limit.

    Indicator trick:
        r < limit iff floor((s + mod - limit) / mod) - floor(s / mod) == 0
    """
    assert 0 <= limit <= mod
    return n + floor_sum(n, mod, a, b) - floor_sum(n, mod, a, b + mod - limit)


def find_interval_hits(
    *,
    p: int,
    d: int,
    base: int,
    k_bound: int,
    x_bound: int,
    max_hits: int = 32,
) -> list[int]:
    """
    Find k in [0, k_bound) with (base + d*k) mod p < x_bound.

    This is the short-relation step.  It avoids scanning k_bound values by
    using floor-sum counting and recursively locating the sparse hits.
    """

    def count_range(lo: int, hi: int) -> int:
        n = hi - lo
        b = (base + d * lo) % p
        return count_mod_lt(n, p, d, b, x_bound)

    total = count_range(0, k_bound)
    hits: list[int] = []

    def rec(lo: int, hi: int, cnt: int) -> None:
        if cnt == 0 or len(hits) >= max_hits:
            return
        if hi - lo == 1:
            hits.append(lo)
            return

        mid = (lo + hi) // 2
        left = count_range(lo, mid)
        rec(lo, mid, left)
        rec(mid, hi, cnt - left)

    rec(0, k_bound, total)
    return hits


def is_square(a: int, p: int) -> bool:
    a %= p
    return a == 0 or pow(a, (p - 1) // 2, p) == 1


def sqrt_mod(a: int, p: int) -> int:
    """Tonelli-Shanks square root modulo an odd prime."""
    a %= p
    if a == 0:
        return 0
    if not is_square(a, p):
        raise ValueError("not a square")

    if p % 4 == 3:
        r = pow(a, (p + 1) // 4, p)
        if (r * r) % p != a:
            raise ValueError("not a square")
        return r

    q = p - 1
    s = 0
    while q % 2 == 0:
        s += 1
        q //= 2

    z = 2
    while is_square(z, p):
        z += 1

    m = s
    c = pow(z, q, p)
    t = pow(a, q, p)
    r = pow(a, (q + 1) // 2, p)

    while t != 1:
        i = 1
        t2 = (t * t) % p
        while t2 != 1:
            t2 = (t2 * t2) % p
            i += 1
            if i >= m:
                raise ValueError("not a square")

        b = pow(c, 1 << (m - i - 1), p)
        m = i
        c = (b * b) % p
        t = (t * c) % p
        r = (r * b) % p

    if (r * r) % p != a:
        raise ValueError("not a square")
    return r


def cube_root_unity_candidates(p: int) -> list[int]:
    """Recover the two non-trivial cube roots of unity from sqrt(-3)."""
    inv2 = pow(2, -1, p)
    s = sqrt_mod(-3, p)

    out: list[int] = []
    for root in (s, (-s) % p):
        a = ((root - 1) * inv2) % p
        if a != 1 and pow(a, 3, p) == 1 and a not in out:
            out.append(a)
    return out


def fourth_root_record_y(rhs: int, p: int) -> Iterable[tuple[int, int]]:
    """
    Yield (y, z) such that y^2 = rhs and y = z^2.

    The record format requires y to be a square, not merely that the curve RHS
    is a square.
    """
    try:
        y0 = sqrt_mod(rhs, p)
    except ValueError:
        return

    for y in (y0, (-y0) % p):
        if is_square(y, p):
            z = sqrt_mod(y, p)
            yield y, z


def solve_relation(params: dict) -> Iterable[tuple[int, int, int, int, int, int, int]]:
    p = int(params["p"])
    b = int(params["b"])
    window = int(params["window"])
    item_limit = int(params["item_limit"])
    account_id = int(params["account_id"])

    x_bound = item_limit * window
    x_admin_base = account_id * window

    for a in cube_root_unity_candidates(p):
        d = pow(a, -1, p)
        base = (d * x_admin_base) % p

        for k_admin in find_interval_hits(
            p=p,
            d=d,
            base=base,
            k_bound=window,
            x_bound=x_bound,
        ):
            x_admin = x_admin_base + k_admin
            x_user = (d * x_admin) % p
            if not (0 <= x_user < x_bound):
                continue

            m_user, k_user = divmod(x_user, window)
            if not (0 <= m_user < item_limit and 0 <= k_user < window):
                continue
            if m_user == account_id:
                continue

            rhs = (pow(x_admin, 3, p) + b) % p
            for y, z in fourth_root_record_y(rhs, p):
                yield a, m_user, k_user, x_user, k_admin, x_admin, y, z


def main() -> None:
    io = remote(HOST, PORT)
    io.recvuntil(b"> ")

    params = call(io, "params")
    if not params.get("ok"):
        raise RuntimeError(f"params failed: {params}")

    p = int(params["p"])

    for a, m_user, k_user, x_user, k_admin, x_admin, y, z in solve_relation(params):
        sign_res = call(
            io,
            "sign",
            {
                "m": m_user,
                "x": x_user,
                "y": y,
                "k": k_user,
                "z": z,
            },
        )
        if not sign_res.get("ok"):
            continue

        token = sign_res["token"]
        verify_res = call(
            io,
            "verify",
            {
                "x": x_admin,
                "y": y,
                "k": k_admin,
                "z": z,
                "sx": (a * int(token["x"])) % p,
                "sy": int(token["y"]),
            },
        )

        print(json.dumps(verify_res, separators=(",", ":")))
        if verify_res.get("ok"):
            io.close()
            return

    io.close()
    raise RuntimeError("no valid forgery found")


if __name__ == "__main__":
    main()
