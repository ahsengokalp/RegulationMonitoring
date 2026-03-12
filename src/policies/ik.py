from __future__ import annotations

import re
from typing import List

from src.core.models import GazetteItem
from src.policies.base import DepartmentPolicy, PolicyDecision


HIGH_SIGNAL = [
    r"\bçalışma\s*hayatı\b",
    r"\bsgk\b",
    r"\bsosyal\s*güvenlik\b",
    r"\bistihdam\b",
    r"\bmesai\b|\bfazla\s*çalışma\b",
    r"\bizin\b|\byıllık\s*izin\b",
    r"\bücret\b|\basgari\s*ücret\b",
    r"\bpersonel\b",
    r"\biş\s*kanunu\b|\b4857\b",
    r"\byabancı\s*çalışma\b|\bçalışma\s*izni\b",
    r"\biş\s*sözleşmesi\b",
    r"\bkıdem\s*tazminatı\b",
    r"\bihbar\s*tazminatı\b",
    r"\bsendika\b|\btoplu\s*iş\s*sözleşmesi\b",
    r"\bişten\s*çıkarma\b|\bfesih\b",
    r"\bişe\s*iade\b",
    r"\bemeklilik\b|\bemekli\b",
    r"\bprim\b|\bsigorta\s*prim\b",
    r"\bözürlü\b|\bengelli\b|\bengelli\s*istihdamı\b",
    r"\bstajyer\b|\bstaj\b",
    r"\bçırak\b|\bçıraklık\b",
    r"\bmesleki\s*yeterlilik\b",
    r"\bmesleki\s*eğitim\b",
    r"\bdisiplin\b",
    r"\bişçi\b|\bişveren\b",
    r"\bİŞKUR\b",
    r"\biş\s*mahkemesi\b",
    r"\barabuluculuk\b",
    r"\bkısa\s*çalışma\b",
    r"\bücretsiz\s*izin\b",
    r"\bbordrolu\b|\bbordro\b",
]

MID_SIGNAL = [
    r"\bgenelge\b",
    r"\byönetmelik\b",
    r"\btebliğ\b",
    r"\bkurul\b",
    r"\bçalışma\b",
    r"\bçalışan\b",
    r"\binsan\s*kaynakları\b",
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


class IkPolicy(DepartmentPolicy):
    @property
    def name(self) -> str:
        return "ik"

    def evaluate_title(self, item: GazetteItem) -> PolicyDecision:
        if item.section and "İLAN" in item.section.upper():
            return PolicyDecision(False, 0, ["section_excluded: İLAN BÖLÜMÜ"])

        haystack = " ".join([x for x in [item.section, item.subsection, item.title] if x])
        score, reasons = _score(haystack)
        return PolicyDecision(is_relevant=score >= 10, score=score, reasons=reasons)
