from __future__ import annotations

import json
from fpylll import CVP, LLL, IntegerMatrix
from pwn import context, remote


HOST = "127.0.0.1"
PORT = 1342

context.log_level = "error"


class Client:
    def __init__(self, host: str, port: int):
        self.io = remote(host, port)
        self.io.recvuntil(b"> ")

    def close(self) -> None:
        self.io.sendline(b"exit")
        self.io.close()

    def call(self, cmd: str, payload: dict | None = None) -> dict:
        if payload is None:
            line = cmd
        else:
            line = f"{cmd} {json.dumps(payload, separators=(',', ':'))}"

        self.io.sendline(line.encode())
        data = self.io.recvuntil(b"> ", drop=True).strip()
        return json.loads(data.splitlines()[-1])


def is_square(x: int, p: int) -> bool:
    x %= p
    if x == 0:
        return True
    return pow(x, (p - 1) // 2, p) == 1


def sqrt_mod(x: int, p: int) -> int:
    x %= p
    if x == 0:
        return 0
    if not is_square(x, p):
        raise ValueError("not a square")

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
    t = pow(x, q, p)
    r = pow(x, (q + 1) // 2, p)

    while t != 1:
        i = 1
        t2 = (t * t) % p
        while t2 != 1:
            t2 = (t2 * t2) % p
            i += 1

        b = pow(c, 1 << (m - i - 1), p)
        m = i
        c = (b * b) % p
        t = (t * c) % p
        r = (r * b) % p

    assert (r * r) % p == x
    return r


def find_relation(p: int, window: int, item_limit: int, account_id: int, a: int) -> tuple[int, int, int]:
    bound = window * item_limit
    scale = item_limit
    ainv = pow(a, -1, p)
    base = (ainv * account_id * window) % p

    basis = IntegerMatrix.from_matrix([[ainv, scale], [-p, 0]])
    LLL.reduction(basis)

    for i in range(129):
        center = (window * i) // 128
        closest = CVP.closest_vector(basis, [-base, scale * center])
        k2 = int(closest[1] // scale)

        if not (0 <= k2 < window):
            continue

        x1 = (base + ainv * k2) % p
        if x1 >= bound:
            continue

        m1, k1 = divmod(x1, window)
        if (a * x1 - (account_id * window + k2)) % p == 0:
            return int(m1), int(k1), int(k2)

    raise RuntimeError("short relation not found")


def find_witness(p: int, b: int, x: int) -> tuple[int, int]:
    rhs = (pow(x, 3, p) + b) % p
    y = sqrt_mod(rhs, p)

    if not is_square(y, p):
        y = (-y) % p

    z = sqrt_mod(y, p)
    return int(y), int(z)


def main() -> None:
    client = Client(HOST, PORT)
    try:
        params = client.call("params")
        assert params["ok"], params

        p = params["p"]
        b = params["b"]
        window = params["window"]
        item_limit = params["item_limit"]
        account_id = params["account_id"]
        a = ((sqrt_mod(-3, p) - 1) * pow(2, -1, p)) % p
        m1, k1, k2 = find_relation(p, window, item_limit, account_id, a)

        x1 = m1 * window + k1
        x2 = account_id * window + k2
        assert (a * x1 - x2) % p == 0

        y, z = find_witness(p, b, x1)
        sign_resp = client.call(
            "sign",
            {
                "m": m1,
                "x": x1,
                "y": y,
                "k": k1,
                "z": z,
            },
        )
        assert sign_resp.get("ok"), sign_resp

        token = sign_resp["token"]
        token2 = {
            "x": (a * token["x"]) % p,
            "y": token["y"],
        }

        verify_resp = client.call(
            "verify",
            {
                "x": x2,
                "y": y,
                "k": k2,
                "z": z,
                "sx": token2["x"],
                "sy": token2["y"],
            },
        )
        assert verify_resp.get("ok"), verify_resp
        print(verify_resp["flag"])
    finally:
        client.close()


if __name__ == "__main__":
    main()
