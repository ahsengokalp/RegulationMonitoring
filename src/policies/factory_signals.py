from __future__ import annotations

import re

FACTORY_OVERRIDES = [
    r"\biş\s*sağlığı\b",
    r"\biş\s*güvenliği\b",
    r"\bİSG\b",
    r"\bsgk\b",
    r"\bgümrük\b",
    r"\bvergi\b",
    r"\bkdv\b",
    r"\bithalat\b|\bihracat\b",
    r"\bmuhasebe\b",
]


def has_factory_override(text: str) -> bool:
    for rx in FACTORY_OVERRIDES:
        if re.search(rx, text, flags=re.IGNORECASE):
            return True
    return False