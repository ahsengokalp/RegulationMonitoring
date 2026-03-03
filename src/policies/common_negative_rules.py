from __future__ import annotations

from src.policies.negative_filter import compile_negative_rules

NEGATIVE_RULES = compile_negative_rules([
    # Üniversite / akademik iç işler (çoğu fabrika dışı)
    (r"\büniversite\b", -20, "üniversite", False),
    (r"\brektörlük\b", -40, "rektörlük", True),
    (r"\bfakülte\b", -20, "fakülte", False),
    (r"\benstitü\b", -15, "enstitü", False),
    (r"\bakademik\b", -20, "akademik", False),
    (r"\böğrenci\b", -15, "öğrenci", False),

    # Kültür/sanat/spor etkinlik duyuruları (çoğu ilan)
    (r"\bkonser\b|\bsergi\b|\bfestival\b|\bturnuva\b", -30, "etkinlik", False),

    # Belediye / yerel etkinlik duyuruları (çoğu ilan)
    (r"\bbelediye\b", -10, "belediye", False),

    # Kişisel ilan / vefat vb. (çoğu ilan)
    (r"\bvefat\b|\btaziye\b", -50, "vefat", True),
])