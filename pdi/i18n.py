"""Per-tenant language for the vault's user-facing strings.

PDI generates no free text — its responses are structured facts plus a small
set of fixed explanatory notes. Those notes are hand-translated here for
every supported language and swapped in by a response middleware whenever
the calling tenant has set a language: any known string anywhere in a JSON
response is replaced with its translation, unknown strings pass through
untouched. Deterministic, and nothing is ever machine-mangled.
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

# Every supported language carries hand-translated note strings.
HAND_TRANSLATED = tuple(code for code in SUPPORTED if code != "en")


# "pre": known note strings are swapped in every response (default).
# "on_demand": responses keep English; POST /translate serves lookups.
MODES = ("pre", "on_demand")


def get_pref(tenant_id: str) -> tuple[str, str]:
    from . import db
    row = db.connect().execute(
        "SELECT language, mode FROM language_prefs WHERE tenant_id=?",
        (tenant_id,)).fetchone()
    return (row["language"], row["mode"]) if row else (DEFAULT, "pre")


def get_language(tenant_id: str) -> str:
    return get_pref(tenant_id)[0]


def effective_language(tenant_id: str) -> str:
    language, mode = get_pref(tenant_id)
    return language if mode == "pre" else DEFAULT


def set_language(tenant_id: str, language: str, mode: str = "pre") -> str:
    if language not in SUPPORTED:
        raise ValueError(f"unknown language {language!r}")
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    from . import db
    conn = db.connect()
    conn.execute(
        "INSERT INTO language_prefs (tenant_id, language, mode, updated_at)"
        " VALUES (?,?,?,?)"
        " ON CONFLICT(tenant_id) DO UPDATE SET language=excluded.language,"
        " mode=excluded.mode, updated_at=excluded.updated_at",
        (tenant_id, language, mode, db.utcnow()))
    conn.commit()
    return language


def translate(tenant_id: str, text: str, to: str | None = None) -> dict:
    """Dictionary-only translation: PDI runs no model, so it translates
    exactly its own note strings and says so for anything else — never a
    machine-mangled guess."""
    target = to or get_language(tenant_id)
    if target not in SUPPORTED:
        raise ValueError(f"unknown language {target!r}")
    if target == DEFAULT:
        return {"text": text, "translation": text, "language": target,
                "engine": "none", "note": "target language is English"}
    hand = tr(text, target)
    if hand != text:
        return {"text": text, "translation": hand, "language": target,
                "engine": "hand"}
    return {"text": text, "translation": text, "language": target,
            "engine": "none",
            "note": "PDI performs no machine translation — only its own "
                    "note strings are translated"}


_STRINGS: dict[str, dict[str, str]] = {
    "collected items are encrypted at rest in the vault": {
        "es": "los elementos recopilados se almacenan cifrados en la bóveda",
        "fr": "les éléments collectés sont chiffrés au repos dans le coffre",
        "de": "gesammelte Elemente werden im Tresor verschlüsselt "
              "gespeichert",
        "pt": "os itens coletados são armazenados criptografados no cofre",
        "it": "gli elementi raccolti sono conservati cifrati nel caveau",
        "ja": "収集されたデータは保管庫内で暗号化されて保存されます",
        "zh": "采集的数据在保险库中加密存储",
        "hi": "एकत्र किए गए आइटम वॉल्ट में एन्क्रिप्ट करके संग्रहीत होते हैं",
        "ar": "تُخزَّن العناصر المجمعة مشفرةً في الخزنة",
    },
    "your file was sealed in the vault, encrypted at rest": {
        "es": "su archivo fue sellado en la bóveda, cifrado en reposo",
        "fr": "votre fichier a été scellé dans le coffre, chiffré au repos",
        "de": "Ihre Datei wurde im Tresor versiegelt und verschlüsselt "
              "gespeichert",
        "pt": "seu arquivo foi selado no cofre, criptografado em repouso",
        "it": "il suo file è stato sigillato nel caveau, cifrato a riposo",
        "ja": "ファイルは保管庫に封印され、暗号化されて保存されました",
        "zh": "您的文件已在保险库中封存并加密存储",
        "hi": "आपकी फ़ाइल वॉल्ट में सील कर दी गई है, एन्क्रिप्टेड रूप में",
        "ar": "خُتم ملفك في الخزنة وخُزِّن مشفرًا",
    },
    "robot data is encrypted at rest in the vault": {
        "es": "los datos del robot se almacenan cifrados en la bóveda",
        "fr": "les données du robot sont chiffrées au repos dans le coffre",
        "de": "Roboterdaten werden im Tresor verschlüsselt gespeichert",
        "pt": "os dados do robô são armazenados criptografados no cofre",
        "it": "i dati del robot sono conservati cifrati nel caveau",
        "ja": "ロボットのデータは保管庫内で暗号化されて保存されます",
        "zh": "机器人数据在保险库中加密存储",
        "hi": "रोबोट का डेटा वॉल्ट में एन्क्रिप्ट करके संग्रहीत होता है",
        "ar": "تُخزَّن بيانات الروبوت مشفرةً في الخزنة",
    },
    "sealed data remains in the vault under tenant control": {
        "es": "los datos sellados permanecen en la bóveda bajo control del "
              "titular",
        "fr": "les données scellées restent dans le coffre sous le contrôle "
              "du titulaire",
        "de": "versiegelte Daten verbleiben im Tresor unter Kontrolle des "
              "Mandanten",
        "pt": "os dados selados permanecem no cofre sob controle do titular",
        "it": "i dati sigillati restano nel caveau sotto il controllo del "
              "titolare",
        "ja": "封印されたデータは、契約者の管理下で保管庫に残ります",
        "zh": "封存的数据仍保留在保险库中，由租户控制",
        "hi": "सील किया गया डेटा किरायेदार के नियंत्रण में वॉल्ट में रहता है",
        "ar": "تبقى البيانات المختومة في الخزنة تحت سيطرة المستأجر",
    },
    "Advisory automation opportunities. Not a staffing decision.": {
        "es": "Oportunidades de automatización a título consultivo. No es "
              "una decisión de personal.",
        "fr": "Opportunités d'automatisation à titre consultatif. Ce n'est "
              "pas une décision de dotation.",
        "de": "Beratende Automatisierungsvorschläge. Keine "
              "Personalentscheidung.",
        "pt": "Oportunidades de automação em caráter consultivo. Não é uma "
              "decisão de pessoal.",
        "it": "Opportunità di automazione a titolo consultivo. Non è una "
              "decisione sul personale.",
        "ja": "自動化の提案は参考情報です。人事上の決定ではありません。",
        "zh": "自动化建议仅供参考，并非人事决定。",
        "hi": "स्वचालन के सुझाव केवल परामर्श हेतु हैं। यह कोई स्टाफ़िंग निर्णय नहीं है।",
        "ar": "فرص أتمتة استشارية فقط، وليست قرارًا يتعلق بالتوظيف.",
    },
    "These decisions keep a human accountable regardless of automation.": {
        "es": "Estas decisiones mantienen a una persona responsable, "
              "independientemente de la automatización.",
        "fr": "Ces décisions maintiennent une personne responsable, quelle "
              "que soit l'automatisation.",
        "de": "Diese Entscheidungen halten unabhängig von der "
              "Automatisierung einen Menschen verantwortlich.",
        "pt": "Essas decisões mantêm um humano responsável, "
              "independentemente da automação.",
        "it": "Queste decisioni mantengono una persona responsabile, "
              "indipendentemente dall'automazione.",
        "ja": "これらの決定では、自動化の有無にかかわらず人間が責任を負います。",
        "zh": "无论自动化程度如何，这些决定始终由人负责。",
        "hi": "ये निर्णय स्वचालन की परवाह किए बिना एक मानव को जवाबदेह रखते हैं।",
        "ar": "تُبقي هذه القرارات إنسانًا مسؤولًا بصرف النظر عن الأتمتة.",
    },
    "access revoked; the sealed record is retained until the ": {
        # partial-sentence key kept verbatim from transfers.py; translated
        # continuations are handled by the caller staying English.
        "es": "acceso revocado; el registro sellado se conserva hasta que ",
        "fr": "accès révoqué ; l'enregistrement scellé est conservé "
              "jusqu'à ce que ",
        "de": "Zugriff widerrufen; der versiegelte Datensatz wird "
              "aufbewahrt bis ",
        "pt": "acesso revogado; o registro selado é mantido até ",
        "it": "accesso revocato; il record sigillato è conservato fino a ",
        "ja": "アクセスは取り消されました。封印された記録は次の時点まで保持されます：",
        "zh": "访问已撤销；封存记录将保留至",
        "hi": "पहुँच रद्द कर दी गई; सील किया गया रिकॉर्ड तब तक रखा जाएगा जब तक ",
        "ar": "أُلغي الوصول؛ يُحتفظ بالسجل المختوم حتى ",
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
