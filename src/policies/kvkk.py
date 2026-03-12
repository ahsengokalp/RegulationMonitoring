from __future__ import annotations

import re
from typing import List

from src.core.models import GazetteItem
from src.policies.base import DepartmentPolicy, PolicyDecision


HIGH_SIGNAL = [
    r"\bKVKK\b",
    r"\b6698\b",
    r"\bkişisel\s*veri\b",
    r"\bkişisel\s*verilerin\s*korunması\b",
    r"\bveri\s*sorumlusu\b",
    r"\bveri\s*işleyen\b",
    r"\baçık\s*rıza\b",
    r"\baydınlatma\s*yükümlülüğü\b",
    r"\bveri\s*ihlali\b",
    r"\bveri\s*koruma\b",
    r"\bKişisel\s*Verileri\s*Koruma\s*Kurulu\b",
    r"\bKişisel\s*Verileri\s*Koruma\s*Kurumu\b",
    r"\bveri\s*aktarımı\b",
    r"\banonimleştirme\b",
    r"\bveri\s*silme\b|\bveri\s*yok\s*etme\b",
    r"\bmahremiyet\b",
    r"\bgizlilik\s*politikası\b",
    r"\bçerez\s*politikası\b",
    r"\bGDPR\b",
    r"\bveri\s*güvenliği\b",
    r"\bveri\s*işleme\b",
    r"\bbiyometrik\s*veri\b",
    r"\bözel\s*nitelikli\s*kişisel\s*veri\b",
    r"\bkayıt\s*sistemi\b",
    r"\belektronik\s*kimlik\b",
    r"\bkimlik\s*doğrulama\b",
]

MID_SIGNAL = [
    r"\bgizlilik\b",
    r"\brıza\b",
    r"\byönetmelik\b",
    r"\btebliğ\b",
    r"\bkurul\s*kararı\b",
    r"\bsicil\b",
    r"\bkişisel\s*bilgi\b",
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


class KvkkPolicy(DepartmentPolicy):
    @property
    def name(self) -> str:
        return "kvkk"

    def evaluate_title(self, item: GazetteItem) -> PolicyDecision:
        if item.section and "İLAN" in item.section.upper():
            return PolicyDecision(False, 0, ["section_excluded: İLAN BÖLÜMÜ"])

        haystack = " ".join([x for x in [item.section, item.subsection, item.title] if x])
        score, reasons = _score(haystack)
        return PolicyDecision(is_relevant=score >= 10, score=score, reasons=reasons)
