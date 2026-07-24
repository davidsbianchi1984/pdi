"""Per-tenant language for the vault's user-facing strings.

PDI generates no free text — its responses are structured facts plus a small
set of fixed explanatory notes. Those notes are hand-translated here (es, fr)
and swapped in by a response middleware whenever the calling tenant has set a
language: any known string anywhere in a JSON response is replaced with its
translation, unknown strings pass through untouched. Deterministic, and
nothing is ever machine-mangled.
"""

from __future__ import annotations

SUPPORTED: dict[str, str] = {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "pt": "Português",
    "it": "Italiano",
    "ja": "日本語",
    "zh": "中文",
    "hi": "हिन्दी",
    "ar": "العربية",
}

DEFAULT = "en"

# Languages with hand-translated note strings; others fall back to English.
HAND_TRANSLATED = ("es", "fr")


def get_language(tenant_id: str) -> str:
    from . import db
    row = db.connect().execute(
        "SELECT language FROM language_prefs WHERE tenant_id=?",
        (tenant_id,)).fetchone()
    return row["language"] if row else DEFAULT


def set_language(tenant_id: str, language: str) -> str:
    if language not in SUPPORTED:
        raise ValueError(f"unknown language {language!r}")
    from . import db
    conn = db.connect()
    conn.execute(
        "INSERT INTO language_prefs (tenant_id, language, updated_at)"
        " VALUES (?,?,?)"
        " ON CONFLICT(tenant_id) DO UPDATE SET language=excluded.language,"
        " updated_at=excluded.updated_at",
        (tenant_id, language, db.utcnow()))
    conn.commit()
    return language


_STRINGS: dict[str, dict[str, str]] = {
    "collected items are encrypted at rest in the vault": {
        "es": "los elementos recopilados se almacenan cifrados en la bóveda",
        "fr": "les éléments collectés sont chiffrés au repos dans le coffre",
    },
    "your file was sealed in the vault, encrypted at rest": {
        "es": "su archivo fue sellado en la bóveda, cifrado en reposo",
        "fr": "votre fichier a été scellé dans le coffre, chiffré au repos",
    },
    "robot data is encrypted at rest in the vault": {
        "es": "los datos del robot se almacenan cifrados en la bóveda",
        "fr": "les données du robot sont chiffrées au repos dans le coffre",
    },
    "sealed data remains in the vault under tenant control": {
        "es": "los datos sellados permanecen en la bóveda bajo control del "
              "titular",
        "fr": "les données scellées restent dans le coffre sous le contrôle "
              "du titulaire",
    },
    "Advisory automation opportunities. Not a staffing decision.": {
        "es": "Oportunidades de automatización a título consultivo. No es "
              "una decisión de personal.",
        "fr": "Opportunités d'automatisation à titre consultatif. Ce n'est "
              "pas une décision de dotation.",
    },
    "These decisions keep a human accountable regardless of automation.": {
        "es": "Estas decisiones mantienen a una persona responsable, "
              "independientemente de la automatización.",
        "fr": "Ces décisions maintiennent une personne responsable, quelle "
              "que soit l'automatisation.",
    },
    "access revoked; the sealed record is retained until the ": {
        # partial-sentence key kept verbatim from transfers.py; translated
        # continuations are handled by the caller staying English.
        "es": "acceso revocado; el registro sellado se conserva hasta que ",
        "fr": "accès révoqué ; l'enregistrement scellé est conservé "
              "jusqu'à ce que ",
    },
}


def tr(text: str, language: str) -> str:
    if language == DEFAULT:
        return text
    return _STRINGS.get(text, {}).get(language, text)


def localize(obj, language: str):
    """Walk a JSON-shaped structure, replacing exactly the strings we have
    hand translations for. Everything else — keys, data, unknown strings —
    passes through untouched."""
    if language == DEFAULT:
        return obj
    if isinstance(obj, dict):
        return {k: localize(v, language) for k, v in obj.items()}
    if isinstance(obj, list):
        return [localize(v, language) for v in obj]
    if isinstance(obj, str):
        return tr(obj, language)
    return obj
