from __future__ import annotations

import re
from typing import List

from src.core.models import GazetteItem
from src.policies.base import DepartmentPolicy, PolicyDecision


HIGH_SIGNAL = [
    r"\bgümrük\b",
    r"\bithalat\b|\bihracat\b",
    r"\bgtip\b|\bgümrük\s*tarife\b",
    r"\blojistik\b",
    r"\btaşımacılık\b|\bnakliye\b",
    r"\btransit\b",
    r"\bdepo\b|\bantrepo\b",
    r"\bliman\b",
    r"\badr\b|\btehlikeli\s*madde\b",
    r"\bmenşe\b",
    r"\bdış\s*ticaret\b",
    r"\ba\.tr\b|\beur\.1\b",
    r"\bnavlun\b",
    r"\bkonşimento\b",
    r"\bkonteyner\b",
    r"\bserbest\s*ticaret\b",
    r"\bticaret\s*anlaşması\b",
    r"\banti-damping\b|\bdamping\b",
    r"\bkorunma\s*önlemi\b",
    r"\bkota\b",
    r"\bürün\s*güvenliği\b",
    r"\bce\s*işareti\b|\bCE\b",
    r"\bstandart\s*tebliğ\b",
    r"\btse\b|\btürk\s*standart\b",
    r"\btedarik\s*zinciri\b",
    r"\bkabotaj\b",
    r"\bdeniz\s*ticareti\b",
    r"\bhavayolu\b|\bhavacılık\b",
    r"\bdemiryolu\b",
    r"\bkarayolu\b|\bkarayolları\b",
    r"\btaşıma\s*belgesi\b",
    r"\bözet\s*beyan\b",
]

MID_SIGNAL = [
    r"\byönetmelik\b",
    r"\btebliğ\b",
    r"\bkarar\b",
    r"\btaşıma\b",
    r"\bticaret\b",
]


def _score(text: str) -> tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []
    for pat in HIGH_SIGNAL:
        if re.search(pat, text, flags=re.IGNORECASE):
            score += 10
            reasons.append(f"high:{pat}")
    for pat in MID_SIGNAL:
        if re.search(pat, text, flags=re.IGNORECASE):
            score += 3
            reasons.append(f"mid:{pat}")
    return score, reasons


class LojistikPolicy(DepartmentPolicy):
    @property
    def name(self) -> str:
        return "lojistik"

    def evaluate_title(self, item: GazetteItem) -> PolicyDecision:
        if item.section and "İLAN" in item.section.upper():
            return PolicyDecision(False, 0, ["section_excluded: İLAN BÖLÜMÜ"])

        haystack = " ".join([x for x in [item.section, item.subsection, item.title] if x])
        score, reasons = _score(haystack)
        return PolicyDecision(is_relevant=score >= 10, score=score, reasons=reasons)
