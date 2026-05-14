from __future__ import annotations

import os

P_FIELD = 2**255 - 19
B_CURVE = (-17) % P_FIELD

WINDOW = 2**64
ITEM_LIMIT = 2**127

RESERVED_NAME = b"admin"
RESERVED_ID = 36189653048003025375317383004032890484

FLAG = os.environ.get("FLAG", "flag{test}")
