from __future__ import annotations

import json
import sys
from typing import Any

from service_core import Service


MAX_LINE = 20000

_SERVICE = Service()


def handle_request(req: dict[str, Any]) -> dict[str, Any]:
    return _SERVICE.handle(req)


def banner() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "short-relation-token-service",
        "usage": {"cmd": "params | sign | verify"},
    }


def main() -> None:
    print("== Token Service ahhhgain ==")
    print(json.dumps(handle_request({"cmd": "params"}), separators=(",", ":")))
    print("Commands:")
    print("  params")
    print('  sign {"m": <int>, "x": <int>, "y": <int>, "k": <int>, "z": <int>}')
    print('  verify {"x": <int>, "y": <int>, "k": <int>, "z": <int>, "sx": <int>, "sy": <int>}')
    print("  exit")

    while True:
        sys.stdout.write("> ")
        sys.stdout.flush()
        line = sys.stdin.readline()
        if not line:
            break
        if len(line.encode()) > MAX_LINE:
            print(json.dumps({"ok": False, "error": "request too large"}, separators=(",", ":")), flush=True)
            continue

        line = line.strip()
        if not line:
            continue
        if line == "exit":
            break

        try:
            if line == "params":
                req = {"cmd": "params"}
            elif line.startswith("{"):
                req = json.loads(line)
            else:
                cmd, payload_raw = line.split(" ", 1)
                req = json.loads(payload_raw)
                if not isinstance(req, dict):
                    raise TypeError
                req["cmd"] = cmd

            res = handle_request(req)
        except Exception:
            res = {"ok": False, "error": "bad request"}

        print(json.dumps(res, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
