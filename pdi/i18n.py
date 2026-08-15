"""Per-tenant language for the vault's user-facing strings.

PDI generates no free text — its responses are structured facts plus a small
set of fixed explanatory notes. Those notes are hand-translated here for
every supported language and swapped in by a response middleware whenever
the calling tenant has set a language: any known string anywhere in a JSON
response is replaced with its translation, unknown strings pass through
untouched. Deterministic, and nothing is ever machine-mangled.
"""

from __future__ import annotations

import re

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



# --------------------------------------------------------------------------- #
# The pages a stranger reads
# --------------------------------------------------------------------------- #
#
# Deliberately a separate table from `_STRINGS`, with its own lookup, because
# the two are consumed by different machinery. `_STRINGS` feeds `localize`,
# which walks whole JSON responses swapping *any* string it recognises — safe
# for a long compliance note that could not plausibly be a data value, and not
# safe for the short words a page is made of. "State", "Download" and "Ring"
# are page furniture here and could be somebody's field value there, and a
# middleware cannot tell the difference. So these translate only where they
# are asked for, through `tr_page`, and `localize` never sees them.

_PAGE_STRINGS: dict[str, dict[str, str]] = {
    'Nothing here': {
        'es': 'Nada aquí',
        'fr': 'Rien ici',
        'de': 'Nichts hier',
        'pt': 'Nada aqui',
        'it': 'Niente qui',
        'ja': '何もありません',
        'zh': '这里没有内容',
        'hi': 'यहाँ कुछ नहीं',
        'ar': 'لا شيء هنا',
    },
    "This code doesn't resolve to anything": {
        'es': 'Este código no corresponde a nada',
        'fr': 'Ce code ne correspond à rien',
        'de': 'Dieser Code führt zu nichts',
        'pt': 'Este código não corresponde a nada',
        'it': 'Questo codice non corrisponde a nulla',
        'ja': 'このコードは何にも結びついていません',
        'zh': '此代码未对应任何内容',
        'hi': 'यह कोड किसी चीज़ से मेल नहीं खाता',
        'ar': 'هذا الرمز لا يقابل أي شيء',
    },
    'It may have been retired, or it may never have been one of ours. Either way there is nothing here to see, and nothing you need to do.': {
        'es': 'Puede haber sido retirado, o puede que nunca haya sido nuestro. En cualquier caso, aquí no hay nada que ver ni nada que deba hacer.',
        'fr': "Il a pu être retiré, ou il n'a peut-être jamais été l'un des nôtres. Dans les deux cas, il n'y a rien à voir ici et rien à faire.",
        'de': 'Er wurde vielleicht zurückgezogen, oder er war nie einer von unseren. So oder so gibt es hier nichts zu sehen und nichts zu tun.',
        'pt': 'Pode ter sido retirado, ou pode nunca ter sido nosso. De qualquer forma, não há nada aqui para ver nem nada que precise fazer.',
        'it': "Può essere stato ritirato, o può non essere mai stato nostro. In ogni caso qui non c'è nulla da vedere e nulla da fare.",
        'ja': '使用が終了したか、そもそも当方のものではなかった可能性があります。いずれにせよ、ここに見るものはなく、行うべきこともありません。',
        'zh': '它可能已停用，也可能从来就不属于我们。无论如何，这里没有可看的内容，您也无需做任何事。',
        'hi': 'हो सकता है इसे वापस ले लिया गया हो, या यह कभी हमारा रहा ही न हो। किसी भी हाल में यहाँ देखने को कुछ नहीं है और आपको कुछ करने की ज़रूरत नहीं।',
        'ar': 'ربما جرى سحبه، أو ربما لم يكن من عندنا أصلًا. في الحالتين لا شيء هنا لتراه ولا شيء عليك فعله.',
    },
    'Sealed carrier': {
        'es': 'Contenedor sellado',
        'fr': 'Contenant scellé',
        'de': 'Versiegelter Behälter',
        'pt': 'Recipiente selado',
        'it': 'Contenitore sigillato',
        'ja': '封印された輸送物',
        'zh': '封存的载具',
        'hi': 'सीलबंद वाहक',
        'ar': 'حاوية مختومة',
    },
    'This is under custody': {
        'es': 'Esto está bajo custodia',
        'fr': 'Ceci est sous garde',
        'de': 'Dies steht unter Verwahrung',
        'pt': 'Isto está sob custódia',
        'it': 'Questo è sotto custodia',
        'ja': 'これは管理下にあります',
        'zh': '此物处于保管之下',
        'hi': 'यह अभिरक्षा में है',
        'ar': 'هذا تحت الحفظ',
    },
    'State': {
        'es': 'Estado',
        'fr': 'État',
        'de': 'Status',
        'pt': 'Estado',
        'it': 'Stato',
        'ja': '状態',
        'zh': '状态',
        'hi': 'स्थिति',
        'ar': 'الحالة',
    },
    'Governed by': {
        'es': 'Regido por',
        'fr': 'Régi par',
        'de': 'Geregelt durch',
        'pt': 'Regido por',
        'it': 'Regolato da',
        'ja': '適用規制',
        'zh': '适用法规',
        'hi': 'किसके अधीन',
        'ar': 'يخضع لـ',
    },
    'Held by': {
        'es': 'En poder de',
        'fr': 'Détenu par',
        'de': 'Verwahrt von',
        'pt': 'Em poder de',
        'it': 'Detenuto da',
        'ja': '保持者',
        'zh': '持有方',
        'hi': 'किसके पास',
        'ar': 'بحوزة',
    },
    'This belongs to {holder}.': {
        'es': 'Esto pertenece a {holder}.',
        'fr': 'Ceci appartient à {holder}.',
        'de': 'Dies gehört {holder}.',
        'pt': 'Isto pertence a {holder}.',
        'it': 'Questo appartiene a {holder}.',
        'ja': 'これは {holder} のものです。',
        'zh': '此物属于 {holder}。',
        'hi': 'यह {holder} का है।',
        'ar': 'هذا يخص {holder}.',
    },
    "Report it here and the holder will be told — you won't learn whose it is, and you don't need to.": {
        'es': 'Repórtelo aquí y se avisará a quien lo tenga: usted no sabrá de quién es, y no necesita saberlo.',
        'fr': "Signalez-le ici et le détenteur sera prévenu — vous n'apprendrez pas à qui il appartient, et vous n'en avez pas besoin.",
        'de': 'Melden Sie es hier, dann wird der Verwahrer benachrichtigt — Sie erfahren nicht, wem es gehört, und müssen es auch nicht.',
        'pt': 'Relate aqui e quem o detém será avisado — você não saberá de quem é, e não precisa saber.',
        'it': 'Segnalalo qui e il detentore sarà avvisato — non saprai di chi è, e non ti serve saperlo.',
        'ja': 'ここから報告すると保持者に通知されます。誰のものかは分かりませんし、知る必要もありません。',
        'zh': '在此报告即可通知持有方 — 您不会知道它属于谁，也无需知道。',
        'hi': 'यहाँ रिपोर्ट करें, धारक को सूचित कर दिया जाएगा — यह किसका है यह आपको पता नहीं चलेगा, और न ही जानने की ज़रूरत है।',
        'ar': 'أبلغ من هنا وسيُخطَر حائزه — لن تعرف لمن هو، ولا تحتاج إلى ذلك.',
    },
    'This code cannot open it, and neither can whoever is holding it. It says the thing is sealed — never what is inside.': {
        'es': 'Este código no puede abrirlo, y quien lo tenga tampoco. Dice que está sellado, nunca qué contiene.',
        'fr': "Ce code ne peut pas l'ouvrir, et son détenteur non plus. Il dit que la chose est scellée — jamais ce qu'elle contient.",
        'de': 'Dieser Code kann es nicht öffnen, und wer es verwahrt, auch nicht. Er sagt, dass die Sache versiegelt ist — nie, was darin ist.',
        'pt': 'Este código não pode abri-lo, nem quem o detém. Ele diz que a coisa está selada — nunca o que há dentro.',
        'it': "Questo codice non può aprirlo, e nemmeno chi lo detiene. Dice che la cosa è sigillata — mai cosa c'è dentro.",
        'ja': 'このコードでは開けられず、保持している人にも開けられません。封印されていることを示すだけで、中身は決して示しません。',
        'zh': '此代码无法打开它，持有者同样无法打开。它只表明该物已封存 — 从不表明里面是什么。',
        'hi': 'यह कोड इसे नहीं खोल सकता, और न ही वह जिसके पास यह है। यह बताता है कि वस्तु सीलबंद है — कभी नहीं कि उसके भीतर क्या है।',
        'ar': 'هذا الرمز لا يفتحه، ولا من يحمله. إنه يقول إن الشيء مختوم — لا ما بداخله أبدًا.',
    },
    'Where is it?': {
        'es': '¿Dónde está?',
        'fr': 'Où se trouve-t-il ?',
        'de': 'Wo ist es?',
        'pt': 'Onde está?',
        'it': 'Dove si trova?',
        'ja': 'どこにありますか',
        'zh': '它在哪里？',
        'hi': 'यह कहाँ है?',
        'ar': 'أين هو؟',
    },
    'depot 3, Oakland': {
        'es': 'depósito 3, Oakland',
        'fr': 'dépôt 3, Oakland',
        'de': 'Depot 3, Oakland',
        'pt': 'depósito 3, Oakland',
        'it': 'deposito 3, Oakland',
        'ja': '第3デポ、オークランド',
        'zh': '奥克兰 3 号仓库',
        'hi': 'डिपो 3, ओकलैंड',
        'ar': 'المستودع 3، أوكلاند',
    },
    'How can you be reached? (optional)': {
        'es': '¿Cómo podemos contactarle? (opcional)',
        'fr': 'Comment vous joindre ? (facultatif)',
        'de': 'Wie sind Sie erreichbar? (optional)',
        'pt': 'Como podemos contactá-lo? (opcional)',
        'it': 'Come possiamo contattarti? (facoltativo)',
        'ja': '連絡先（任意）',
        'zh': '如何联系到您？（可选）',
        'hi': 'आपसे कैसे संपर्क करें? (वैकल्पिक)',
        'ar': 'كيف يمكن الوصول إليك؟ (اختياري)',
    },
    'name, phone': {
        'es': 'nombre, teléfono',
        'fr': 'nom, téléphone',
        'de': 'Name, Telefon',
        'pt': 'nome, telefone',
        'it': 'nome, telefono',
        'ja': '氏名、電話番号',
        'zh': '姓名、电话',
        'hi': 'नाम, फ़ोन',
        'ar': 'الاسم، الهاتف',
    },
    'I found this': {
        'es': 'Encontré esto',
        'fr': "J'ai trouvé ceci",
        'de': 'Ich habe das gefunden',
        'pt': 'Encontrei isto',
        'it': 'Ho trovato questo',
        'ja': 'これを見つけました',
        'zh': '我发现了此物',
        'hi': 'मुझे यह मिला',
        'ar': 'لقد وجدت هذا',
    },
    "Your report is timestamped and hash-chained into this carrier's chain of custody. It cannot be altered afterwards — including by us.": {
        'es': 'Su reporte queda fechado y encadenado por hash a la cadena de custodia de este contenedor. No puede alterarse después, tampoco por nosotros.',
        'fr': 'Votre signalement est horodaté et chaîné par hachage à la chaîne de traçabilité de ce contenant. Il ne peut être modifié ensuite — pas même par nous.',
        'de': 'Ihre Meldung wird mit Zeitstempel versehen und per Hash in die Verwahrkette dieses Behälters eingebunden. Sie kann danach nicht geändert werden — auch nicht von uns.',
        'pt': 'Seu relato é datado e encadeado por hash à cadeia de custódia deste recipiente. Não pode ser alterado depois — nem por nós.',
        'it': 'La tua segnalazione viene marcata temporalmente e concatenata per hash alla catena di custodia di questo contenitore. Non può essere modificata in seguito — nemmeno da noi.',
        'ja': 'あなたの報告にはタイムスタンプが付き、この輸送物の管理連鎖にハッシュ連結されます。後から変更することはできません — 当方にもできません。',
        'zh': '您的报告带有时间戳，并以哈希方式链入此载具的保管链。事后无法更改 — 包括我们在内。',
        'hi': 'आपकी रिपोर्ट पर समय-मुहर लगती है और वह इस वाहक की अभिरक्षा शृंखला में हैश-जुड़ जाती है। बाद में इसे बदला नहीं जा सकता — हमारे द्वारा भी नहीं।',
        'ar': 'يُختم بلاغك بالوقت ويُربط تجزئيًا بسلسلة حفظ هذه الحاوية. لا يمكن تغييره بعد ذلك — ولا من جانبنا.',
    },
    'Controlled facility': {
        'es': 'Instalación controlada',
        'fr': 'Site à accès contrôlé',
        'de': 'Kontrollierte Anlage',
        'pt': 'Instalação controlada',
        'it': 'Struttura ad accesso controllato',
        'ja': '管理区域',
        'zh': '受控场所',
        'hi': 'नियंत्रित परिसर',
        'ar': 'منشأة خاضعة للرقابة',
    },
    'What are you here for?': {
        'es': '¿A qué viene?',
        'fr': 'Que venez-vous faire ?',
        'de': 'Weshalb sind Sie hier?',
        'pt': 'A que veio?',
        'it': 'Per cosa è qui?',
        'ja': 'ご用件',
        'zh': '您来办什么事？',
        'hi': 'आप किस लिए आए हैं?',
        'ar': 'ما سبب حضورك؟',
    },
    'A delivery': {
        'es': 'Una entrega',
        'fr': 'Une livraison',
        'de': 'Eine Lieferung',
        'pt': 'Uma entrega',
        'it': 'Una consegna',
        'ja': '配達',
        'zh': '送货',
        'hi': 'एक डिलीवरी',
        'ar': 'تسليم',
    },
    'A collection': {
        'es': 'Una recogida',
        'fr': 'Un enlèvement',
        'de': 'Eine Abholung',
        'pt': 'Uma recolha',
        'it': 'Un ritiro',
        'ja': '集荷',
        'zh': '取货',
        'hi': 'एक पिकअप',
        'ar': 'استلام',
    },
    'Access to the site': {
        'es': 'Acceso al sitio',
        'fr': 'Accès au site',
        'de': 'Zutritt zum Gelände',
        'pt': 'Acesso ao local',
        'it': 'Accesso al sito',
        'ja': '敷地への立ち入り',
        'zh': '进入场地',
        'hi': 'परिसर में प्रवेश',
        'ar': 'الدخول إلى الموقع',
    },
    'Something else': {
        'es': 'Otra cosa',
        'fr': 'Autre chose',
        'de': 'Etwas anderes',
        'pt': 'Outra coisa',
        'it': 'Altro',
        'ja': 'その他',
        'zh': '其他事项',
        'hi': 'कुछ और',
        'ar': 'شيء آخر',
    },
    'Anything else we should know?': {
        'es': '¿Algo más que debamos saber?',
        'fr': 'Autre chose à nous signaler ?',
        'de': 'Sonst noch etwas, das wir wissen sollten?',
        'pt': 'Mais alguma coisa que devamos saber?',
        'it': "Qualcos'altro che dovremmo sapere?",
        'ja': '他にお伝えいただくことはありますか',
        'zh': '还有什么需要我们知道的吗？',
        'hi': 'क्या हमें कुछ और जानना चाहिए?',
        'ar': 'هل من شيء آخر ينبغي أن نعرفه؟',
    },
    'who you are, who you were expecting to meet': {
        'es': 'quién es usted, con quién esperaba reunirse',
        'fr': 'qui vous êtes, qui vous deviez rencontrer',
        'de': 'wer Sie sind, mit wem Sie verabredet waren',
        'pt': 'quem é você, quem esperava encontrar',
        'it': 'chi sei, chi ti aspettavi di incontrare',
        'ja': 'お名前、面会予定の相手',
        'zh': '您是谁，您原本要见谁',
        'hi': 'आप कौन हैं, आप किससे मिलने वाले थे',
        'ar': 'من أنت، ومن كنت تتوقع مقابلته',
    },
    'Ring': {
        'es': 'Llamar',
        'fr': 'Sonner',
        'de': 'Klingeln',
        'pt': 'Chamar',
        'it': 'Suona',
        'ja': '呼び出す',
        'zh': '呼叫',
        'hi': 'घंटी बजाएँ',
        'ar': 'اطرق',
    },
    "Whoever answers cannot let anyone in — that decision always belongs to a person. This exchange is recorded in the facility's audit chain.": {
        'es': 'Quien responda no puede dejar entrar a nadie: esa decisión siempre corresponde a una persona. Este intercambio queda registrado en la cadena de auditoría de la instalación.',
        'fr': "Celui qui répond ne peut laisser entrer personne — cette décision revient toujours à une personne. Cet échange est enregistré dans la chaîne d'audit du site.",
        'de': 'Wer antwortet, kann niemanden einlassen — diese Entscheidung liegt immer bei einem Menschen. Dieser Austausch wird in der Prüfkette der Anlage festgehalten.',
        'pt': 'Quem responde não pode deixar ninguém entrar — essa decisão pertence sempre a uma pessoa. Esta troca fica registrada na cadeia de auditoria da instalação.',
        'it': 'Chi risponde non può far entrare nessuno — quella decisione spetta sempre a una persona. Questo scambio è registrato nella catena di audit della struttura.',
        'ja': '応答する側が入場を許可することはできません。その判断は常に人間が行います。このやり取りは施設の監査連鎖に記録されます。',
        'zh': '应答方无权放行任何人 — 该决定始终由人作出。此次交互会记录在该场所的审计链中。',
        'hi': 'जो उत्तर देता है वह किसी को अंदर नहीं आने दे सकता — वह निर्णय हमेशा एक व्यक्ति का होता है। यह आदान-प्रदान परिसर की ऑडिट शृंखला में दर्ज होता है।',
        'ar': 'من يرد لا يستطيع السماح لأحد بالدخول — فذلك القرار يعود دائمًا إلى إنسان. تُسجَّل هذه المحادثة في سلسلة تدقيق المنشأة.',
    },
    'A file was sealed for you': {
        'es': 'Se selló un archivo para usted',
        'fr': 'Un fichier a été scellé pour vous',
        'de': 'Eine Datei wurde für Sie versiegelt',
        'pt': 'Um arquivo foi selado para você',
        'it': 'Un file è stato sigillato per te',
        'ja': 'あなた宛てにファイルが封印されました',
        'zh': '有一份文件为您封存',
        'hi': 'आपके लिए एक फ़ाइल सील की गई है',
        'ar': 'خُتم ملف من أجلك',
    },
    "It was sent through PDI under a compliance program. Collecting it is recorded in the sender's chain of custody — that record is the point of sending it this way, and it names the collection, not you.": {
        'es': 'Se envió a través de PDI bajo un programa de cumplimiento. La recogida queda registrada en la cadena de custodia del remitente: ese registro es el motivo de enviarlo así, y nombra la recogida, no a usted.',
        'fr': "Il a été envoyé via PDI dans le cadre d'un programme de conformité. Sa récupération est inscrite dans la chaîne de traçabilité de l'expéditeur — c'est tout l'intérêt de cet envoi, et elle nomme la récupération, pas vous.",
        'de': 'Sie wurde über PDI im Rahmen eines Compliance-Programms gesendet. Das Abholen wird in der Verwahrkette des Absenders festgehalten — dieser Eintrag ist der Zweck dieses Versandwegs, und er benennt den Abruf, nicht Sie.',
        'pt': 'Foi enviado através do PDI sob um programa de conformidade. A coleta fica registrada na cadeia de custódia do remetente — esse registro é o motivo de enviar assim, e nomeia a coleta, não você.',
        'it': "È stato inviato tramite PDI nell'ambito di un programma di conformità. Il ritiro viene registrato nella catena di custodia del mittente — quel record è il motivo di questo invio, e nomina il ritiro, non te.",
        'ja': 'コンプライアンス制度のもと、PDI を通じて送信されました。受け取りは送信者の管理連鎖に記録されます。その記録こそがこの送信方法の目的であり、記録されるのは受け取り行為であって、あなたではありません。',
        'zh': '它是在合规计划下通过 PDI 发送的。领取行为会记入发送方的保管链 — 该记录正是以此方式发送的意义所在，它记录的是这次领取，而不是您。',
        'hi': 'इसे एक अनुपालन कार्यक्रम के तहत PDI के माध्यम से भेजा गया था। इसे लेना भेजने वाले की अभिरक्षा शृंखला में दर्ज होता है — वही रिकॉर्ड इस तरह भेजने का उद्देश्य है, और वह संग्रहण को दर्ज करता है, आपको नहीं।',
        'ar': 'أُرسل عبر PDI ضمن برنامج امتثال. يُسجَّل استلامه في سلسلة حفظ المرسِل — وهذا السجل هو الغاية من الإرسال بهذه الطريقة، وهو يذكر عملية الاستلام لا يذكرك أنت.',
    },
    'Your receive token': {
        'es': 'Su token de recepción',
        'fr': 'Votre jeton de réception',
        'de': 'Ihr Empfangs-Token',
        'pt': 'Seu token de recebimento',
        'it': 'Il tuo token di ricezione',
        'ja': '受け取りトークン',
        'zh': '您的领取令牌',
        'hi': 'आपका प्राप्ति टोकन',
        'ar': 'رمز الاستلام الخاص بك',
    },
    'from the message that sent you here': {
        'es': 'del mensaje que le trajo aquí',
        'fr': 'du message qui vous a envoyé ici',
        'de': 'aus der Nachricht, die Sie hierher geschickt hat',
        'pt': 'da mensagem que o trouxe aqui',
        'it': 'dal messaggio che ti ha portato qui',
        'ja': 'ここへ案内したメッセージに記載',
        'zh': '来自把您带到这里的那条消息',
        'hi': 'उस संदेश से जो आपको यहाँ लाया',
        'ar': 'من الرسالة التي أرسلتك إلى هنا',
    },
    'Collect it': {
        'es': 'Recogerlo',
        'fr': 'Le récupérer',
        'de': 'Abholen',
        'pt': 'Recolher',
        'it': 'Ritiralo',
        'ja': '受け取る',
        'zh': '领取',
        'hi': 'इसे प्राप्त करें',
        'ar': 'استلمه',
    },
    'Download': {
        'es': 'Descargar',
        'fr': 'Télécharger',
        'de': 'Herunterladen',
        'pt': 'Baixar',
        'it': 'Scarica',
        'ja': 'ダウンロード',
        'zh': '下载',
        'hi': 'डाउनलोड',
        'ar': 'تنزيل',
    },
    "Keep the link if you need it again — the token stays good, and every collection is written into the sender's chain of custody, so a second one is visible rather than silent.": {
        'es': 'Conserve el enlace por si lo necesita otra vez: el token sigue siendo válido, y cada recogida se escribe en la cadena de custodia del remitente, de modo que una segunda es visible y no silenciosa.',
        'fr': "Conservez le lien si vous en avez encore besoin — le jeton reste valable, et chaque récupération est inscrite dans la chaîne de traçabilité de l'expéditeur : une seconde est donc visible et non silencieuse.",
        'de': 'Behalten Sie den Link, falls Sie ihn erneut brauchen — das Token bleibt gültig, und jeder Abruf wird in die Verwahrkette des Absenders geschrieben, ein zweiter ist also sichtbar und nicht stumm.',
        'pt': 'Guarde o link caso precise novamente — o token continua válido, e cada coleta é escrita na cadeia de custódia do remetente, de modo que uma segunda é visível e não silenciosa.',
        'it': 'Conserva il link se ti serve ancora — il token resta valido, e ogni ritiro viene scritto nella catena di custodia del mittente, quindi un secondo è visibile e non silenzioso.',
        'ja': '再度必要になる場合に備えてリンクを保管してください。トークンは有効なままで、受け取りはそのつど送信者の管理連鎖に記録されるため、2 回目も見える形で残ります。',
        'zh': '如需再次使用，请保留该链接 — 令牌仍然有效，且每次领取都会写入发送方的保管链，因此第二次领取是可见的，而非无声进行。',
        'hi': 'यदि दोबारा ज़रूरत पड़े तो लिंक सँभाल कर रखें — टोकन वैध बना रहता है, और हर बार लेना भेजने वाले की अभिरक्षा शृंखला में लिखा जाता है, इसलिए दूसरी बार लेना चुपचाप नहीं, दिखाई देकर होता है।',
        'ar': 'احتفظ بالرابط إن احتجته مجددًا — يظل الرمز صالحًا، وكل عملية استلام تُكتب في سلسلة حفظ المرسِل، فتكون المرة الثانية ظاهرة لا صامتة.',
    },
    'Recording…': {
        'es': 'Registrando…',
        'fr': 'Enregistrement…',
        'de': 'Wird erfasst…',
        'pt': 'Registrando…',
        'it': 'Registrazione…',
        'ja': '記録しています…',
        'zh': '正在记录…',
        'hi': 'दर्ज किया जा रहा है…',
        'ar': 'جارٍ التسجيل…',
    },
    'Recorded. Thank you.': {
        'es': 'Registrado. Gracias.',
        'fr': 'Enregistré. Merci.',
        'de': 'Erfasst. Danke.',
        'pt': 'Registrado. Obrigado.',
        'it': 'Registrato. Grazie.',
        'ja': '記録しました。ありがとうございます。',
        'zh': '已记录。谢谢。',
        'hi': 'दर्ज हो गया। धन्यवाद।',
        'ar': 'تم التسجيل. شكرًا لك.',
    },
    'That did not go through.': {
        'es': 'Eso no se envió.',
        'fr': "Cela n'est pas passé.",
        'de': 'Das ist nicht durchgegangen.',
        'pt': 'Isso não foi enviado.',
        'it': 'Non è andato a buon fine.',
        'ja': '送信できませんでした。',
        'zh': '未能提交。',
        'hi': 'यह नहीं भेजा जा सका।',
        'ar': 'لم يتم الإرسال.',
    },
    'No connection — try again in a moment.': {
        'es': 'Sin conexión: inténtelo de nuevo en un momento.',
        'fr': 'Pas de connexion — réessayez dans un instant.',
        'de': 'Keine Verbindung — versuchen Sie es gleich noch einmal.',
        'pt': 'Sem conexão — tente novamente em instantes.',
        'it': 'Nessuna connessione — riprova tra un momento.',
        'ja': '接続がありません。少ししてからもう一度お試しください。',
        'zh': '无网络连接 — 请稍后重试。',
        'hi': 'कोई कनेक्शन नहीं — थोड़ी देर में फिर कोशिश करें।',
        'ar': 'لا يوجد اتصال — أعد المحاولة بعد لحظات.',
    },
    'Passed to': {
        'es': 'Pasado a',
        'fr': 'Transmis à',
        'de': 'Weitergeleitet an',
        'pt': 'Passado a',
        'it': 'Passato a',
        'ja': '取り次ぎ先',
        'zh': '已转交',
        'hi': 'किसे सौंपा गया',
        'ar': 'أُحيل إلى',
    },
    'Ringing…': {
        'es': 'Llamando…',
        'fr': 'Sonnerie…',
        'de': 'Klingelt…',
        'pt': 'Chamando…',
        'it': 'Sto suonando…',
        'ja': '呼び出しています…',
        'zh': '正在呼叫…',
        'hi': 'घंटी बज रही है…',
        'ar': 'جارٍ الطرق…',
    },
    'AI REPLY': {
        'es': 'RESPUESTA DE IA',
        'fr': 'RÉPONSE IA',
        'de': 'KI-ANTWORT',
        'pt': 'RESPOSTA DE IA',
        'it': 'RISPOSTA IA',
        'ja': 'AI による応答',
        'zh': 'AI 回复',
        'hi': 'AI उत्तर',
        'ar': 'رد آلي بالذكاء الاصطناعي',
    },
    'AUTOMATED': {
        'es': 'AUTOMATIZADO',
        'fr': 'AUTOMATIQUE',
        'de': 'AUTOMATISCH',
        'pt': 'AUTOMATIZADO',
        'it': 'AUTOMATICO',
        'ja': '自動応答',
        'zh': '自动应答',
        'hi': 'स्वचालित',
        'ar': 'آلي',
    },
    'Fetching…': {
        'es': 'Obteniendo…',
        'fr': 'Récupération…',
        'de': 'Wird abgerufen…',
        'pt': 'Buscando…',
        'it': 'Recupero in corso…',
        'ja': '取得しています…',
        'zh': '正在获取…',
        'hi': 'लाया जा रहा है…',
        'ar': 'جارٍ الجلب…',
    },
    'That did not work.': {
        'es': 'Eso no funcionó.',
        'fr': "Cela n'a pas fonctionné.",
        'de': 'Das hat nicht geklappt.',
        'pt': 'Isso não funcionou.',
        'it': 'Non ha funzionato.',
        'ja': 'うまくいきませんでした。',
        'zh': '没有成功。',
        'hi': 'यह काम नहीं आया।',
        'ar': 'لم ينجح ذلك.',
    },
    'No connection — the link is still good, try again.': {
        'es': 'Sin conexión: el enlace sigue siendo válido, inténtelo de nuevo.',
        'fr': 'Pas de connexion — le lien reste valable, réessayez.',
        'de': 'Keine Verbindung — der Link gilt weiterhin, versuchen Sie es erneut.',
        'pt': 'Sem conexão — o link continua válido, tente novamente.',
        'it': 'Nessuna connessione — il link è ancora valido, riprova.',
        'ja': '接続がありません。リンクは有効なままです。もう一度お試しください。',
        'zh': '无网络连接 — 链接仍然有效，请重试。',
        'hi': 'कोई कनेक्शन नहीं — लिंक अब भी वैध है, फिर कोशिश करें।',
        'ar': 'لا يوجد اتصال — الرابط ما زال صالحًا، أعد المحاولة.',
    },
    'that token does not open anything here': {
        'es': 'ese código no abre nada aquí',
        'fr': "ce jeton n'ouvre rien ici",
        'de': 'dieses Token öffnet hier nichts',
        'pt': 'esse token não abre nada aqui',
        'it': 'quel token non apre nulla qui',
        'ja': 'そのトークンではここで何も開けません',
        'zh': '该令牌在此无法打开任何内容',
        'hi': 'यह टोकन यहाँ कुछ नहीं खोलता',
        'ar': 'هذا الرمز لا يفتح شيئًا هنا',
    },
    'this transfer has been revoked': {
        'es': 'esta transferencia ha sido revocada',
        'fr': 'ce transfert a été révoqué',
        'de': 'diese Übertragung wurde widerrufen',
        'pt': 'esta transferência foi revogada',
        'it': 'questo trasferimento è stato revocato',
        'ja': 'この転送は取り消されました',
        'zh': '此传输已被撤销',
        'hi': 'यह स्थानांतरण रद्द कर दिया गया है',
        'ar': 'أُلغي هذا النقل',
    },
    'this retrieval was recorded in the audit chain': {
        'es': 'esta recogida quedó registrada en la cadena de auditoría',
        'fr': "cette récupération a été inscrite dans la chaîne d'audit",
        'de': 'dieser Abruf wurde in der Prüfkette festgehalten',
        'pt': 'esta coleta ficou registrada na cadeia de auditoria',
        'it': 'questo ritiro è stato registrato nella catena di audit',
        'ja': 'この受け取りは監査連鎖に記録されました',
        'zh': '此次领取已记入审计链',
        'hi': 'यह प्राप्ति ऑडिट शृंखला में दर्ज कर ली गई',
        'ar': 'سُجّل هذا الاستلام في سلسلة التدقيق',
    },
    "recorded in this carrier's chain of custody, timestamped and hash-chained; the holder can see it and you cannot change it": {
        'es': 'registrado en la cadena de custodia de este contenedor, con fecha y encadenado por hash; quien lo tiene puede verlo y usted no puede cambiarlo',
        'fr': 'inscrit dans la chaîne de traçabilité de ce contenant, horodaté et chaîné par hachage ; le détenteur peut le voir et vous ne pouvez pas le modifier',
        'de': 'in der Verwahrkette dieses Behälters festgehalten, mit Zeitstempel und per Hash verkettet; der Verwahrer kann es sehen und Sie können es nicht ändern',
        'pt': 'registado na cadeia de custódia deste recipiente, datado e encadeado por hash; quem o detém pode vê-lo e você não pode alterá-lo',
        'it': 'registrato nella catena di custodia di questo contenitore, con marca temporale e concatenato per hash; chi lo detiene può vederlo e tu non puoi modificarlo',
        'ja': 'この輸送物の管理連鎖に、タイムスタンプ付きでハッシュ連結して記録しました。保持者は閲覧でき、あなたは変更できません。',
        'zh': '已记入此载具的保管链，带时间戳并以哈希链接；持有方可以看到，您无法更改。',
        'hi': 'इस वाहक की अभिरक्षा शृंखला में समय-मुहर और हैश-शृंखला सहित दर्ज कर लिया गया; धारक इसे देख सकता है और आप इसे बदल नहीं सकते',
        'ar': 'سُجّل في سلسلة حفظ هذه الحاوية بختم زمني ومرتبط تجزئيًا؛ يمكن لحائزها رؤيته ولا يمكنك تغييره',
    },
    'this carrier was already reported in the last hour; the holder has been told and nothing is lost by your not reporting it again': {
        'es': 'este contenedor ya se reportó en la última hora; quien lo tiene ya fue avisado y no se pierde nada si usted no lo reporta otra vez',
        'fr': "ce contenant a déjà été signalé dans la dernière heure ; le détenteur a été prévenu et rien n'est perdu si vous ne le signalez pas à nouveau",
        'de': 'dieser Behälter wurde in der letzten Stunde bereits gemeldet; der Verwahrer ist benachrichtigt und es geht nichts verloren, wenn Sie ihn nicht noch einmal melden',
        'pt': 'este recipiente já foi relatado na última hora; quem o detém já foi avisado e nada se perde se não o relatar de novo',
        'it': "questo contenitore è già stato segnalato nell'ultima ora; chi lo detiene è stato avvisato e non si perde nulla se non lo segnali di nuovo",
        'ja': 'この輸送物は 1 時間以内にすでに報告されています。保持者には通知済みで、あらためて報告しなくても失われるものはありません。',
        'zh': '此载具在过去一小时内已被报告；持有方已收到通知，您不再报告也不会有任何损失。',
        'hi': 'यह वाहक पिछले एक घंटे में पहले ही रिपोर्ट किया जा चुका है; धारक को सूचित कर दिया गया है और दोबारा रिपोर्ट न करने से कुछ नहीं बिगड़ता',
        'ar': 'أُبلغ عن هذه الحاوية بالفعل خلال الساعة الماضية؛ وقد أُخطر حائزها ولا شيء يضيع إن لم تبلّغ عنها مجددًا',
    },
    "I couldn't reach anyone just now, so please don't wait on somebody coming out. If there's a number on the door, call it.": {
        'es': 'No he podido contactar con nadie ahora mismo, así que por favor no espere a que salga alguien. Si hay un número en la puerta, llámelo.',
        'fr': "Je n'ai joint personne à l'instant, alors n'attendez pas que quelqu'un sorte. S'il y a un numéro sur la porte, appelez-le.",
        'de': 'Ich habe gerade niemanden erreicht, warten Sie also bitte nicht darauf, dass jemand herauskommt. Wenn eine Nummer an der Tür steht, rufen Sie sie an.',
        'pt': 'Não consegui contactar ninguém agora, por isso não espere que alguém saia. Se houver um número na porta, ligue.',
        'it': "Non sono riuscito a raggiungere nessuno adesso, quindi per favore non aspettare che esca qualcuno. Se c'è un numero sulla porta, chiamalo.",
        'ja': 'ただいま誰にもつながりませんでした。人が出てくるのを待たないでください。扉に番号があれば、そちらにおかけください。',
        'zh': '我此刻没有联系上任何人，请不要在此等人出来。如果门上有号码，请拨打它。',
        'hi': 'इस समय मैं किसी से संपर्क नहीं कर सका, इसलिए कृपया किसी के बाहर आने का इंतज़ार न करें। यदि दरवाज़े पर कोई नंबर है, तो उस पर कॉल करें।',
        'ar': 'لم أتمكن من الوصول إلى أحد الآن، فلا تنتظر خروج أحد من فضلك. إن كان على الباب رقم، فاتصل به.',
    },
    'this code does not resolve to anything': {
        'es': 'este código no corresponde a nada',
        'fr': 'ce code ne correspond à rien',
        'de': 'dieser Code führt zu nichts',
        'pt': 'este código não corresponde a nada',
        'it': 'questo codice non corrisponde a nulla',
        'ja': 'このコードは何にも結びついていません',
        'zh': '此代码未对应任何内容',
        'hi': 'यह कोड किसी चीज़ से मेल नहीं खाता',
        'ar': 'هذا الرمز لا يقابل أي شيء',
    },
    'a gate is not a carrier — ring it instead': {
        'es': 'una puerta no es un contenedor: llame al timbre',
        'fr': "un portail n'est pas un contenant — sonnez plutôt",
        'de': 'ein Tor ist kein Behälter — klingeln Sie stattdessen',
        'pt': 'um portão não é um recipiente — toque à campainha',
        'it': 'un cancello non è un contenitore — suona invece',
        'ja': 'ここは輸送物ではなくゲートです。呼び出しをお使いください。',
        'zh': '这是门禁，不是载具 — 请改用呼叫。',
        'hi': 'यह वाहक नहीं, एक गेट है — इसके बजाय घंटी बजाएँ',
        'ar': 'هذه بوابة لا حاوية — استخدم الطرق بدلًا من ذلك',
    },
    'this code is on a carrier, not a gate': {
        'es': 'este código está en un contenedor, no en una puerta',
        'fr': 'ce code est sur un contenant, pas sur un portail',
        'de': 'dieser Code ist auf einem Behälter, nicht auf einem Tor',
        'pt': 'este código está num recipiente, não num portão',
        'it': 'questo codice è su un contenitore, non su un cancello',
        'ja': 'このコードはゲートではなく輸送物に付いています',
        'zh': '此代码贴在载具上，而不是门禁上',
        'hi': 'यह कोड एक वाहक पर है, गेट पर नहीं',
        'ar': 'هذا الرمز على حاوية، لا على بوابة',
    },
}


def negotiate(header: str | None) -> str:
    """Pick a supported language from an ``Accept-Language`` header.

    Every other localization path in this vault keys off a tenant:
    :func:`get_pref` takes a ``tenant_id``, and the response middleware asks
    the calling tenant what language it reads in. That is right for the API,
    whose callers are all tenants. It has nothing to say about the pages PDI
    serves to people who are not tenants and never will be — a courier
    holding a phone at a sealed carrier, somebody standing at a facility
    gate, and the recipient of a sealed transfer, who the receive route's own
    docstring describes as carrying "no tenant credential".

    Those people's browsers have been sending the answer on every request.
    Nothing read it, so the pages built for the person with no account were
    also the pages with no language.

    Deliberately small: quality values are honoured, the region is dropped
    (``es-419`` and ``es-ES`` are both ``es``), and anything unrecognised
    falls back to English rather than guessing.
    """
    if not header:
        return DEFAULT
    ranked: list[tuple[float, int, str]] = []
    for index, part in enumerate(header.split(",")):
        piece = part.strip()
        if not piece:
            continue
        tag, _, params = piece.partition(";")
        quality = 1.0
        for param in params.split(";"):
            key, _, value = param.partition("=")
            if key.strip() == "q":
                try:
                    quality = float(value)
                except ValueError:
                    quality = 0.0
        base = tag.strip().split("-")[0].lower()
        if base in SUPPORTED and quality > 0:
            # The header's own order is the tie-break, so "fr,es" gives
            # French rather than whichever happens to sort first.
            ranked.append((-quality, index, base))
    if not ranked:
        return DEFAULT
    return min(ranked)[2]


def tr(text: str, language: str) -> str:
    if language == DEFAULT:
        return text
    return _STRINGS.get(text, {}).get(language, text)


def tr_page(text: str, language: str) -> str:
    """Translate a string that belongs to one of the public pages.

    Separate from :func:`tr` on purpose — see the note above
    ``_PAGE_STRINGS``. Unknown text falls through as English rather than
    raising, so a page that grows a sentence renders words in every language
    instead of blank space, and the test beside this module is what notices
    the sentence has no translations yet.
    """
    if language == DEFAULT:
        return text
    return _PAGE_STRINGS.get(text, {}).get(language, text)


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


# --------------------------------------------------------------------------- #
# The vault's own refusals
# --------------------------------------------------------------------------- #
#
# A tenant picks a language. `_STRINGS` honours it in the console's chrome,
# `_PAGE_STRINGS` honours a stranger's browser on the recipient's page, and the
# recipient's own two refusals are localized at their route — `tr_page` on
# `RECEIVE_NO` and `RECEIVE_REVOKED`, from the round that gave the recipient a
# door at all.
#
# The tenant's refusals were English. All sixty of them, on an account where
# the language picker had been answered and every other surface honoured it.
#
#     asked     is the stranger answered in their language
#     mattered  is the tenant
#
# The direction is worth naming because it is the reverse of the usual one.
# Three rounds in these repositories found a stranger being served the
# language of somebody who had an account. Here the stranger's page was
# already right and the account-holder's was not — because the stranger's page
# was *built* as a localization problem and the vault's refusals were never
# looked at as text a person reads.
#
# ## Whose language, and which stored value
#
# The bearer token names the tenant, and the tenant's stored setting is the
# answer. No token — a recipient, an unauthenticated caller — means the
# browser header, which is all they carry.
#
# `get_language`, not `effective_language`: the latter answers English whenever
# the mode is `on_demand`, and that mode is a statement about how *stored
# records* come back ("keep the original wording, I will translate what I
# choose"). A record is not a refusal.


#: What a slot may hold and still be dropped into a translated frame.
#:
#: The rule is whitespace. A token — `en`, `openai`, `usr_9f2`, `12.00` — has
#: none. English prose has spaces in it, and so does every other language's.
#: The one allowed exception is a comma-separated list of tokens, because the
#: refusals this exists for are "must be one of".
#:
#: Conservative in one direction only: it refuses some slots that would have
#: been safe and never accepts one that is not. A refused slot costs an English
#: sentence, which is the state everything was already in. An accepted prose
#: slot costs a sentence half in one language and half in another, in front of
#: somebody who is already being told no.
_SLOT_TOKEN = re.compile(r"^\S*$")


def _is_token(value) -> bool:
    return all(_SLOT_TOKEN.match(part.strip())
               for part in str(value).split(","))


class Templated(str):
    """A refusal whose English text is not a constant, carried so it can be.

    `f"language must be one of {', '.join(SUPPORTED)}"` cannot be keyed on its
    English source, because at the moment it is raised there is no English
    source — only a result. `tests/refusals_untranslated.txt` named these and
    counted none of them.

        asked     is the refusal a constant we can translate
        mattered  is every part of it something we can translate

    This is a `str`, and its value is the finished English sentence, so
    everything that already treats a detail as text keeps working unchanged.
    What it adds is a memory of how it was built, so `localize_detail` can look
    up the *template* and refill it in the reader's language.

    A slot that does not look like a token sets `translatable = False` and the
    whole sentence stays English — the state it was in before, chosen rather
    than stumbled into. Nothing raises: a refusal path is the last place to add
    a way to fail.

    The known limit, stated because a rule this simple has one: a *single*
    English word has no whitespace either, and is indistinguishable from an
    identifier. QRME's copy of this carries a `Term` marker and a translated
    vocabulary for the closed sets it interpolates; this product has no refusal
    that interpolates one, and the guard fails if that stops being true.
    """

    template: str
    slots: dict
    translatable: bool

    def __new__(cls, template: str, **slots):
        text = template.format(**slots)
        self = super().__new__(cls, text)
        self.template = template
        self.slots = slots
        self.translatable = all(_is_token(v) for v in slots.values())
        return self


def fill(template: str, **slots) -> Templated:
    """`raise HTTPException(422, i18n.fill(TEMPLATE, field=..., choices=...))`.

    A function rather than the class directly, so a raise site reads as a
    sentence being built and not as an object being constructed.
    """
    return Templated(template, **slots)


#: Several routes said this about several different fields. One sentence, one
#: translation, `field` as a slot: the field name is the API's own and is the
#: same string in every language.
MUST_BE_ONE_OF = "{field} must be one of {choices}"

#: Derived from the table below rather than repeated.
TEMPLATES = (MUST_BE_ONE_OF,)

_TEMPLATES: dict[str, dict[str, str]] = {
    MUST_BE_ONE_OF: {
        'es': '{field} debe ser uno de {choices}',
        'fr': "{field} doit être l'un de {choices}",
        'de': '{field} muss eines von {choices} sein',
        'pt': '{field} deve ser um de {choices}',
        'it': '{field} deve essere uno tra {choices}',
        'ja': '{field} は次のいずれかにしてください: {choices}',
        'zh': '{field} 必须是以下之一：{choices}',
        'hi': '{field} इनमें से एक होना चाहिए: {choices}',
        'ar': '{field} يجب أن يكون أحد التالي: {choices}',
    },
}


def tr_refusal(text: str, language: str) -> str:
    """Translate one of the sentences this vault refuses with.

    All three tables, one lookup. `RECEIVE_NO` already lives in
    `_PAGE_STRINGS`; a second copy here would be two translations of one
    sentence, free to drift, with nothing to say which reader got which.
    """
    if language == DEFAULT:
        return text
    return (_REFUSALS.get(text) or _TEMPLATES.get(text)
            or _VALIDATION.get(text)
            or _STRINGS.get(text) or _PAGE_STRINGS.get(text, {})).get(
                language, text)


def localize_detail(detail, language: str):
    """A refusal payload, translated in whichever shape it arrives.

    Only the sentence. Everything beside it is the API's own vocabulary and
    the console branches on it: what a person reads is translated, what a
    client compares is not.
    """
    if language == DEFAULT:
        return detail
    # Before the plain-string branch: a Templated *is* a str, and its value is
    # the finished English sentence, which is not a key in any table. Looking
    # it up would find nothing and return the English — silently, and
    # indistinguishably from a sentence nobody has translated yet.
    if isinstance(detail, Templated):
        if not detail.translatable:
            return str(detail)
        frame = tr_refusal(detail.template, language)
        try:
            return frame.format(**detail.slots)
        except (KeyError, IndexError, ValueError):
            # A translation whose braces do not match the template's. The
            # English sentence is correct and complete; a half-formatted one
            # in the reader's language is not.
            return str(detail)
    if isinstance(detail, str):
        return tr_refusal(detail, language)
    if isinstance(detail, dict) and isinstance(detail.get("detail"), str):
        return {**detail, "detail": tr_refusal(detail["detail"], language)}
    if isinstance(detail, dict) and isinstance(detail.get("message"), str):
        return {**detail, "message": tr_refusal(detail["message"], language)}
    # One level further in. `api.py` wraps every `HTTPException` as
    # `{"detail": exc.detail}` before this runs, so a structured refusal would
    # arrive as a dict inside a dict and the branches above would see an outer
    # dict whose `detail` is neither a string nor carrying a `message`. This
    # product has no structured refusal today; the branch is here so the first
    # one does not ship untranslated, which is how it happened in the sibling.
    #
    #     asked     is a structured refusal localized
    #     mattered  is it localized where the wrapper actually puts it
    if isinstance(detail, dict) and isinstance(detail.get("detail"), dict):
        return {**detail,
                "detail": localize_detail(detail["detail"], language)}
    return detail


def refusal_language(request) -> str:
    """The language the person receiving this refusal reads.

    Never raises. This runs inside exception handlers, and a diagnostic that
    can fail turns a refusal into a 500 — telling somebody the vault broke
    when it was really telling them no.
    """
    try:
        header = request.headers.get("authorization", "")
        if header.startswith("Bearer "):
            from . import vault
            tenant = vault.tenant_by_token(header[len("Bearer "):])
            if tenant:
                return get_language(tenant["id"])
    except Exception:
        pass
    try:
        return negotiate(request.headers.get("accept-language"))
    except Exception:
        return DEFAULT


def sentence_of(detail) -> str | None:
    """The part of a refusal a person is meant to read, whatever shape it has.

    `detail` is a string for most refusals, a dict for the plan gate, and a
    list of rows for a 422. Three shapes, and every client had to know which
    one it was looking at — which is why the plan gate reached three of the
    four as a bare status code.

        asked     does the sentence ride beside the structure
        mattered  does every structured refusal put it in the same place

    Returns `None` when there is nothing readable rather than inventing
    something: a bare status is more honest than a sentence this module made
    up.

    The 422's list is deliberately not handled here. Its sentence needs the
    reader's language and the field-name rules, which is `validation_message`'s
    job, and its handler passes the result in directly.
    """
    if isinstance(detail, str):
        return detail or None
    if isinstance(detail, dict):
        said = detail.get("message")
        return said if isinstance(said, str) and said else None
    return None


def refuse(request, status: int, content, headers: dict | None = None):
    """The one place a refusal becomes a response.

    Every exception handler in `pdi/api.py` returns through here. Before this
    there were three, and they built their responses three different ways —
    two hand-rolled `Response`s with `json.dumps`, one `JSONResponse` — which
    is how a fourth would have arrived with a fourth shape and no translation.
    """
    from fastapi.responses import JSONResponse
    body = localize_detail(content, refusal_language(request))
    # One place the sentence is, whatever shape the structure has.
    #
    # The plan gate raises a dict whose `message` sits *inside* it, and the
    # handler wraps that as `{"detail": {...}}`. The three native shells look
    # for a top-level `message` and then for a string `detail`; a dict is
    # neither, so the one refusal that stands between somebody and a decision
    # to pay rendered as the status code alone — no price, no plan name.
    #
    #     asked     does the sentence ride beside the structure
    #     mattered  does every structured refusal put it in the same place
    #
    # Lifted here rather than at each raise site, for the reason this function
    # exists at all: a refusal shape added later cannot forget to do it.
    # `detail` is untouched — the console reads the dict to build the upgrade
    # card with its price and button.
    if isinstance(body, dict) and not isinstance(body.get("message"), str):
        said = sentence_of(body.get("detail"))
        if said is not None:
            body = {**body, "message": said}
    return JSONResponse(status_code=status, content=body, headers=headers)


#: The one sentence a person can meet on any route in this product,
#: because it is the answer to a route that failed. Named here so
#: `_REFUSALS` can carry it and the middleware can look it up — a
#: refusal built inline is a refusal in English.
SERVER_ERROR = ("Something went wrong on our side. "
                "Nothing you sent was recorded.")


#: Keyed on the English source, so editing the English falls back loudly to
#: the new English rather than quietly serving the old sentence in nine
#: languages. What is not here is recorded in
#: `pdi/tests/refusals_untranslated.txt` and ratcheted.
_REFUSALS: dict[str, dict[str, str]] = {
    "there is no keyring here to rotate — nothing has been sealed yet": {
        'es': "aquí no hay ningún llavero que rotar: todavía no se ha sellado nada",
        'fr': "il n'y a ici aucun trousseau à faire tourner : rien n'a encore été scellé",
        'de': "hier gibt es keinen Schlüsselbund zum Rotieren — es wurde noch nichts versiegelt",
        'pt': "não há aqui nenhum chaveiro para rodar — ainda nada foi selado",
        'it': "qui non c'è alcun portachiavi da ruotare: non è ancora stato sigillato nulla",
        'ja': "ここには回転させる鍵束がありません。まだ何も封印されていません",
        'zh': "这里没有可轮换的密钥环 —— 还没有任何东西被封存",
        'hi': "यहाँ घुमाने के लिए कोई कीरिंग नहीं है — अभी तक कुछ भी सील नहीं हुआ",
        'ar': "لا توجد هنا حلقة مفاتيح لتدويرها — لم يُختم أي شيء بعد",
    },
    'Something went wrong on our side. Nothing you sent was recorded.': {
        'es': 'Algo falló de nuestro lado. No se registró nada de lo que envió.',
        'fr': "Quelque chose a échoué de notre côté. Rien de ce que vous avez envoyé n'a été enregistré.",
        'de': 'Auf unserer Seite ist etwas schiefgegangen. Nichts von dem, was Sie gesendet haben, wurde gespeichert.',
        'pt': 'Algo correu mal do nosso lado. Nada do que enviou ficou registado.',
        'it': 'Qualcosa è andato storto dalla nostra parte. Nulla di ciò che ha inviato è stato registrato.',
        'ja': 'こちら側で問題が発生しました。送信された内容は記録されていません。',
        'zh': '我们这边出了问题。您发送的内容没有被记录。',
        'hi': 'हमारी ओर से कुछ गड़बड़ हो गई। आपने जो भेजा, वह दर्ज नहीं हुआ।',
        'ar': 'حدث خطأ من جانبنا. لم يُسجَّل أي شيء أرسلته.',
    },
    'reading the failure map requires the PDI_PROBLEMS_KEY bearer token': {
        'es': 'leer el mapa de fallos requiere el token portador '
              'PDI_PROBLEMS_KEY',
        'fr': 'lire la carte des échecs exige le jeton porteur '
              'PDI_PROBLEMS_KEY',
        'de': 'das Lesen der Fehlerkarte erfordert das '
              'PDI_PROBLEMS_KEY-Bearer-Token',
        'pt': 'ler o mapa de falhas requer o token portador '
              'PDI_PROBLEMS_KEY',
        'it': 'leggere la mappa dei guasti richiede il token bearer '
              'PDI_PROBLEMS_KEY',
        'ja': '障害マップの閲覧には PDI_PROBLEMS_KEY のベアラートークンが必要です',
        'zh': '读取故障图需要 PDI_PROBLEMS_KEY 持有者令牌',
        'hi': 'विफलता मानचित्र पढ़ने के लिए PDI_PROBLEMS_KEY बियरर टोकन चाहिए',
        'ar': 'قراءة خريطة الأعطال تتطلب رمز PDI_PROBLEMS_KEY الحامل',
    },
    'wrong problems key': {
        'es': 'clave de problemas incorrecta',
        'fr': 'mauvaise clé des problèmes',
        'de': 'falscher Problems-Schlüssel',
        'pt': 'chave de problemas errada',
        'it': 'chiave dei problemi sbagliata',
        'ja': 'problemsキーが違います',
        'zh': '问题密钥不正确',
        'hi': 'समस्याओं की कुंजी ग़लत है',
        'ar': 'مفتاح المشاكل خاطئ',
    },
    'the failure aggregate is readable from this machine only until '
    'PDI_PROBLEMS_KEY is set — behind a proxy, set it': {
        'es': 'el agregado de fallos solo se puede leer desde esta máquina '
              'hasta que se fije PDI_PROBLEMS_KEY — tras un proxy, fíjala',
        'fr': "l'agrégat des échecs n'est lisible que depuis cette machine "
              "tant que PDI_PROBLEMS_KEY n'est pas définie — derrière un "
              'proxy, définissez-la',
        'de': 'das Fehleraggregat ist nur von dieser Maschine lesbar, bis '
              'PDI_PROBLEMS_KEY gesetzt ist — hinter einem Proxy: setzen',
        'pt': 'o agregado de falhas só pode ser lido a partir desta máquina '
              'até PDI_PROBLEMS_KEY estar definida — atrás de um proxy, '
              'defina-a',
        'it': "l'aggregato dei guasti è leggibile solo da questa macchina "
              'finché PDI_PROBLEMS_KEY non è impostata — dietro un proxy, '
              'impostala',
        'ja': '障害の集計は PDI_PROBLEMS_KEY を設定するまでこの機械からしか読めません — '
              'プロキシの背後では設定してください',
        'zh': '在设置 PDI_PROBLEMS_KEY 之前，故障汇总只能从本机读取——在代理之后请务必设置',
        'hi': 'जब तक PDI_PROBLEMS_KEY निर्धारित नहीं होती, विफलता समग्र केवल इसी '
              'मशीन से पढ़ा जा सकता है — प्रॉक्सी के पीछे इसे निर्धारित करें',
        'ar': 'لا يمكن قراءة مجمّع الأعطال إلا من هذا الجهاز حتى يُعيَّن '
              'PDI_PROBLEMS_KEY — خلف وكيل، عيِّنه',
    },
    'this deployment is offline — nothing leaves this machine, so the page cannot be fetched. Paste the content into ingest instead.': {
        'es': 'este despliegue está sin conexión: nada sale de esta máquina, así que la página no puede traerse. Pega el contenido en ingerir en su lugar.',
        'fr': "ce déploiement est hors ligne — rien ne quitte cette machine, la page ne peut donc pas être récupérée. Collez plutôt le contenu dans l'ingestion.",
        'de': 'diese Installation ist offline — nichts verlässt diesen Rechner, also kann die Seite nicht geholt werden. Füge den Inhalt stattdessen in die Aufnahme ein.',
        'pt': 'esta instalação está offline — nada sai desta máquina, então a página não pode ser buscada. Cole o conteúdo na ingestão em vez disso.',
        'it': 'questa installazione è offline — nulla esce da questa macchina, quindi la pagina non può essere recuperata. Incolla invece il contenuto nell\'acquisizione.',
        'ja': 'この環境はオフラインです — このマシンから何も出ないため、ページを取得できません。代わりに内容を取り込みに貼り付けてください。',
        'zh': '此部署处于离线状态 — 任何内容都不会离开这台机器，因此无法抓取页面。请改为将内容粘贴到摄取中。',
        'hi': 'यह परिनियोजन ऑफ़लाइन है — इस मशीन से कुछ बाहर नहीं जाता, इसलिए पेज नहीं लाया जा सकता। इसके बजाय सामग्री को इनजेस्ट में चिपकाएँ।',
        'ar': 'هذا النشر دون اتصال — لا شيء يغادر هذا الجهاز، لذا لا يمكن جلب الصفحة. الصق المحتوى في الإدخال بدلًا من ذلك.',
    },
    'say what you were trying to do and what stood in the way': {
        'es': 'di qué intentabas hacer y qué se interpuso',
        'fr': "dites ce que vous essayiez de faire et ce qui s'y est opposé",
        'de': 'sag, was du versucht hast und was im Weg stand',
        'pt': 'diga o que você estava tentando fazer e o que ficou no caminho',
        'it': 'di\' cosa stavi cercando di fare e cosa ti ha ostacolato',
        'ja': '何をしようとして、何が妨げになったかを書いてください',
        'zh': '请写出你想做什么，以及是什么挡住了你',
        'hi': 'बताइए कि आप क्या करने की कोशिश कर रहे थे और क्या आड़े आया',
        'ar': 'اذكر ما كنت تحاول فعله وما الذي وقف في طريقك',
    },
    # --- 0.40.2: the 48 recorded in pdi/tests/refusals_untranslated.txt ----
    #
    # Every one of these was a sentence the vault said when it said no, in
    # English, to somebody who had chosen otherwise — including the recipient
    # of a handoff, who has no account and never chose English.
    #
    #     asked     is the refusal translated
    #     mattered  is every refusal translated
    #
    # The forty-ninth stays English by the decision its own record argues:
    # PDI_ADMIN_TOKEN names an environment variable to an operator.
    #
    # Field names, header names and modes stay as they are: `x-tenant-key`,
    # `handle`, `soft`/`wipe`.
    'a beacon needs a label so its owner can tell their codes apart once several are printed and stuck to different things': {
        'es': 'una baliza necesita una etiqueta para que su propietario distinga sus códigos una vez impresos y pegados en cosas distintas',
        'fr': 'une balise a besoin d\'un libellé pour que son propriétaire distingue ses codes une fois imprimés et collés sur différentes choses',
        'de': 'ein Beacon braucht eine Bezeichnung, damit die Inhaberin oder der Inhaber die Codes auseinanderhalten kann, sobald mehrere gedruckt und auf verschiedene Dinge geklebt sind',
        'pt': 'uma baliza precisa de uma etiqueta para que o seu proprietário distinga os seus códigos depois de vários serem impressos e colados em coisas diferentes',
        'it': 'un beacon ha bisogno di un\'etichetta perché il suo proprietario distingua i codici una volta stampati e attaccati a cose diverse',
        'ja': 'ビーコンにはラベルが必要です。複数を印刷していろいろな物に貼ったとき、持ち主が見分けられるようにするためです',
        'zh': '信标需要一个标签，以便其所有者在打印多个并贴到不同物件上后能加以区分',
        'hi': 'बीकन को एक लेबल चाहिए ताकि कई कोड छपकर अलग-अलग चीज़ों पर लगने के बाद स्वामी उन्हें पहचान सके',
        'ar': 'تحتاج المنارة إلى تسمية كي يميّز مالكها بين رموزه بعد طباعة عدة منها ولصقها على أشياء مختلفة',
    },
    'a bequest names at least one key prefix — an unbounded grant is not a bequest': {
        'es': 'un legado nombra al menos un prefijo de clave — una concesión sin límites no es un legado',
        'fr': 'un legs désigne au moins un préfixe de clé — une autorisation sans limite n\'est pas un legs',
        'de': 'ein Vermächtnis benennt mindestens ein Schlüsselpräfix — eine unbegrenzte Freigabe ist kein Vermächtnis',
        'pt': 'um legado nomeia pelo menos um prefixo de chave — uma concessão sem limites não é um legado',
        'it': 'un lascito indica almeno un prefisso di chiave — una concessione illimitata non è un lascito',
        'ja': '遺贈は少なくとも一つの鍵の接頭辞を指定します — 無制限の許可は遺贈ではありません',
        'zh': '遗赠须指明至少一个键前缀 — 无边界的授权不是遗赠',
        'hi': 'विरासत कम से कम एक कुंजी उपसर्ग नामित करती है — असीमित अनुदान विरासत नहीं है',
        'ar': 'تُسمّي الوصية بادئة مفتاح واحدة على الأقل — والتفويض غير المحدود ليس وصية',
    },
    'a bequest names its grantee': {
        'es': 'un legado nombra a su beneficiario',
        'fr': 'un legs désigne son bénéficiaire',
        'de': 'ein Vermächtnis benennt seine begünstigte Person',
        'pt': 'um legado nomeia o seu beneficiário',
        'it': 'un lascito indica il proprio beneficiario',
        'ja': '遺贈は受遺者を指定します',
        'zh': '遗赠须指明其受赠人',
        'hi': 'विरासत अपने अनुदानग्राही को नामित करती है',
        'ar': 'تُسمّي الوصية المستفيد منها',
    },
    'a message is required': {
        'es': 'se requiere un mensaje',
        'fr': 'un message est requis',
        'de': 'eine Nachricht ist erforderlich',
        'pt': 'é necessária uma mensagem',
        'it': 'è richiesto un messaggio',
        'ja': 'メッセージが必要です',
        'zh': '需要填写消息内容',
        'hi': 'संदेश आवश्यक है',
        'ar': 'الرسالة مطلوبة',
    },
    'a pane with no faces is the helper button on its own — set the state to \'handle\' instead': {
        'es': 'un panel sin caras es solo el botón del asistente — ponga el estado en \'handle\' en su lugar',
        'fr': 'un volet sans visages n\'est que le bouton d\'aide — mettez plutôt l\'état à \'handle\'',
        'de': 'ein Bereich ohne Gesichter ist nur die Helfer-Schaltfläche — setzen Sie den Zustand stattdessen auf \'handle\'',
        'pt': 'um painel sem rostos é apenas o botão do assistente — defina antes o estado para \'handle\'',
        'it': 'un pannello senza volti è solo il pulsante dell\'assistente — imposta invece lo stato su \'handle\'',
        'ja': '顔のないペインはヘルパーのボタンそのものです — 代わりに状態を \'handle\' にしてください',
        'zh': '没有面孔的面板就只是助手按钮本身 — 请改将状态设为 \'handle\'',
        'hi': 'बिना चेहरों वाला फलक केवल सहायक बटन है — इसके बजाय स्थिति \'handle\' पर सेट करें',
        'ar': 'اللوح الخالي من الوجوه هو زر المساعد وحده — اضبط الحالة على \'handle\' بدلًا من ذلك',
    },
    'a roster entry needs a name': {
        'es': 'una entrada de la lista necesita un nombre',
        'fr': 'une entrée du tableau a besoin d\'un nom',
        'de': 'ein Eintrag im Dienstplan braucht einen Namen',
        'pt': 'uma entrada da lista precisa de um nome',
        'it': 'una voce dell\'elenco richiede un nome',
        'ja': '名簿の項目には名前が必要です',
        'zh': '名册条目需要一个名字',
        'hi': 'रोस्टर प्रविष्टि को एक नाम चाहिए',
        'ar': 'يحتاج مُدخل القائمة إلى اسم',
    },
    'a shift needs at least one day': {
        'es': 'un turno necesita al menos un día',
        'fr': 'un créneau a besoin d\'au moins un jour',
        'de': 'eine Schicht braucht mindestens einen Tag',
        'pt': 'um turno precisa de pelo menos um dia',
        'it': 'un turno richiede almeno un giorno',
        'ja': 'シフトには少なくとも一日が必要です',
        'zh': '排班至少需要一天',
        'hi': 'शिफ़्ट को कम से कम एक दिन चाहिए',
        'ar': 'تحتاج المناوبة إلى يوم واحد على الأقل',
    },
    'activation requires a reference — what attested the condition (a vigil event id, a succession verification, a certificate number)': {
        'es': 'la activación requiere una referencia — lo que acreditó la condición (un id de evento de vigilia, una verificación de sucesión, un número de certificado)',
        'fr': 'l\'activation requiert une référence — ce qui atteste la condition (un identifiant d\'événement de veille, une vérification de succession, un numéro de certificat)',
        'de': 'die Aktivierung erfordert eine Referenz — das, was die Bedingung belegt (eine Wache-Ereigniskennung, eine Nachfolgeprüfung, eine Urkundennummer)',
        'pt': 'a ativação requer uma referência — aquilo que atestou a condição (um id de evento de vigília, uma verificação de sucessão, um número de certidão)',
        'it': 'l\'attivazione richiede un riferimento — ciò che ha attestato la condizione (un id di evento di veglia, una verifica di successione, un numero di certificato)',
        'ja': '有効化には参照が必要です — その条件を裏づけたもの（見守りイベントの id、承継の確認、証明書番号など）',
        'zh': '激活需要一个凭据 — 即证明该条件的依据（守候事件 id、继承核验、证书编号）',
        'hi': 'सक्रियण हेतु एक संदर्भ चाहिए — जिसने उस स्थिति को प्रमाणित किया (विजिल इवेंट आईडी, उत्तराधिकार सत्यापन, प्रमाणपत्र संख्या)',
        'ar': 'يتطلّب التفعيل مرجعًا — ما أثبت الحالة (معرّف حدث سهر، أو تحقّق خلافة، أو رقم شهادة)',
    },
    'already activated — an activated grant is revoked by the deployment admin, not the tenant token, which may be in an estate\'s hands by now': {
        'es': 'ya activado — una concesión activada la revoca el administrador de la instalación, no el token del inquilino, que para entonces puede estar en manos de una sucesión',
        'fr': 'déjà activé — une autorisation activée est révoquée par l\'administrateur du déploiement, non par le jeton du locataire, qui peut désormais être entre les mains d\'une succession',
        'de': 'bereits aktiviert — eine aktivierte Freigabe widerruft die Administration der Installation, nicht das Mandanten-Token, das inzwischen in den Händen eines Nachlasses sein kann',
        'pt': 'já ativado — uma concessão ativada é revogada pelo administrador da instalação e não pelo token do inquilino, que a esta altura pode estar nas mãos de um espólio',
        'it': 'già attivata — una concessione attivata viene revocata dall\'amministratore dell\'installazione, non dal token del tenant, che ormai potrebbe essere nelle mani di un\'eredità',
        'ja': '既に有効化済みです — 有効化された許可を取り消すのは環境の管理者であり、テナントのトークンではありません。そのトークンはこの時点で遺産管理者の手にあるかもしれません',
        'zh': '已激活 — 已激活的授权由部署管理员撤销，而非租户令牌；此时该令牌可能已在遗产管理方手中',
        'hi': 'पहले से सक्रिय — सक्रिय अनुदान परिनियोजन व्यवस्थापक रद्द करता है, टेनेंट टोकन नहीं, जो अब तक किसी संपदा के हाथ में हो सकता है',
        'ar': 'مُفعَّل بالفعل — التفويض المُفعَّل يُلغيه مسؤول النشر، لا رمز المستأجر الذي قد يكون الآن بين يدي ورثة',
    },
    'already activated — the grant token was shown once, at activation': {
        'es': 'ya activado — el token de concesión se mostró una sola vez, en la activación',
        'fr': 'déjà activé — le jeton d\'autorisation n\'a été affiché qu\'une fois, à l\'activation',
        'de': 'bereits aktiviert — das Freigabe-Token wurde einmalig bei der Aktivierung angezeigt',
        'pt': 'já ativado — o token de concessão foi mostrado uma única vez, na ativação',
        'it': 'già attivata — il token della concessione è stato mostrato una sola volta, all\'attivazione',
        'ja': '既に有効化済みです — 許可トークンは有効化時に一度だけ表示されました',
        'zh': '已激活 — 授权令牌仅在激活时显示过一次',
        'hi': 'पहले से सक्रिय — अनुदान टोकन केवल एक बार, सक्रियण के समय दिखाया गया था',
        'ar': 'مُفعَّل بالفعل — عُرض رمز التفويض مرة واحدة عند التفعيل',
    },
    'app connector not found': {
        'es': 'conector de aplicación no encontrado',
        'fr': 'connecteur d\'application introuvable',
        'de': 'App-Connector nicht gefunden',
        'pt': 'conector de aplicação não encontrado',
        'it': 'connettore dell\'app non trovato',
        'ja': 'アプリコネクタが見つかりません',
        'zh': '未找到应用连接器',
        'hi': 'ऐप कनेक्टर नहीं मिला',
        'ar': 'لم يُعثر على موصّل التطبيق',
    },
    'beacon not found': {
        'es': 'baliza no encontrada',
        'fr': 'balise introuvable',
        'de': 'Beacon nicht gefunden',
        'pt': 'baliza não encontrada',
        'it': 'beacon non trovato',
        'ja': 'ビーコンが見つかりません',
        'zh': '未找到信标',
        'hi': 'बीकन नहीं मिला',
        'ar': 'لم يُعثر على المنارة',
    },
    'beacons are for publish connectors': {
        'es': 'las balizas son para conectores de publicación',
        'fr': 'les balises servent aux connecteurs de publication',
        'de': 'Beacons sind für Veröffentlichungs-Connectoren',
        'pt': 'as balizas são para conectores de publicação',
        'it': 'i beacon sono per i connettori di pubblicazione',
        'ja': 'ビーコンは公開用のコネクタに使うものです',
        'zh': '信标用于发布类连接器',
        'hi': 'बीकन प्रकाशन कनेक्टरों के लिए हैं',
        'ar': 'المنارات مخصّصة لموصّلات النشر',
    },
    'connector has been revoked': {
        'es': 'el conector ha sido revocado',
        'fr': 'le connecteur a été révoqué',
        'de': 'der Connector wurde widerrufen',
        'pt': 'o conector foi revogado',
        'it': 'il connettore è stato revocato',
        'ja': 'このコネクタは取り消されました',
        'zh': '该连接器已被撤销',
        'hi': 'कनेक्टर रद्द कर दिया गया है',
        'ar': 'تم إلغاء الموصّل',
    },
    'connector not found': {
        'es': 'conector no encontrado',
        'fr': 'connecteur introuvable',
        'de': 'Connector nicht gefunden',
        'pt': 'conector não encontrado',
        'it': 'connettore non trovato',
        'ja': 'コネクタが見つかりません',
        'zh': '未找到连接器',
        'hi': 'कनेक्टर नहीं मिला',
        'ar': 'لم يُعثر على الموصّل',
    },
    'intake not found': {
        'es': 'recepción no encontrada',
        'fr': 'admission introuvable',
        'de': 'Aufnahme nicht gefunden',
        'pt': 'receção não encontrada',
        'it': 'acquisizione non trovata',
        'ja': '受付が見つかりません',
        'zh': '未找到接收单',
        'hi': 'इनटेक नहीं मिला',
        'ar': 'لم يُعثر على الاستلام',
    },
    'invalid submit token': {
        'es': 'token de envío no válido',
        'fr': 'jeton de dépôt invalide',
        'de': 'Übermittlungstoken ungültig',
        'pt': 'token de envio inválido',
        'it': 'token di invio non valido',
        'ja': '送信トークンが無効です',
        'zh': '提交令牌无效',
        'hi': 'सबमिट टोकन अमान्य',
        'ar': 'رمز الإرسال غير صالح',
    },
    'mode must be \'soft\' or \'wipe\'': {
        'es': 'mode debe ser \'soft\' o \'wipe\'',
        'fr': 'mode doit être \'soft\' ou \'wipe\'',
        'de': 'mode muss \'soft\' oder \'wipe\' sein',
        'pt': 'mode deve ser \'soft\' ou \'wipe\'',
        'it': 'mode deve essere \'soft\' o \'wipe\'',
        'ja': 'mode は \'soft\' か \'wipe\' である必要があります',
        'zh': 'mode 必须为 \'soft\' 或 \'wipe\'',
        'hi': 'mode का मान \'soft\' या \'wipe\' होना चाहिए',
        'ar': 'يجب أن تكون قيمة mode إما \'soft\' أو \'wipe\'',
    },
    'no active grant for this token': {
        'es': 'no hay ninguna concesión activa para este token',
        'fr': 'aucune autorisation active pour ce jeton',
        'de': 'keine aktive Freigabe für dieses Token',
        'pt': 'não há nenhuma concessão ativa para este token',
        'it': 'nessuna concessione attiva per questo token',
        'ja': 'このトークンに有効な許可はありません',
        'zh': '此令牌没有有效的授权',
        'hi': 'इस टोकन हेतु कोई सक्रिय अनुदान नहीं',
        'ar': 'لا يوجد تفويض نشط لهذا الرمز',
    },
    'no contribution with that ref': {
        'es': 'no hay ninguna contribución con esa referencia',
        'fr': 'aucune contribution avec cette référence',
        'de': 'kein Beitrag mit dieser Referenz',
        'pt': 'não há nenhuma contribuição com essa referência',
        'it': 'nessun contributo con quel riferimento',
        'ja': 'その参照の寄与はありません',
        'zh': '不存在具有该引用的贡献',
        'hi': 'उस संदर्भ वाला कोई योगदान नहीं',
        'ar': 'لا توجد مساهمة بهذا المرجع',
    },
    'no executed BAA on file for this tenant': {
        'es': 'no hay ningún BAA firmado en el expediente de este inquilino',
        'fr': 'aucun accord de sous-traitance signé au dossier pour ce locataire',
        'de': 'für diesen Mandanten liegt kein abgeschlossener Auftragsverarbeitungsvertrag vor',
        'pt': 'não há nenhum BAA celebrado em arquivo para este inquilino',
        'it': 'nessun BAA sottoscritto agli atti per questo tenant',
        'ja': 'このテナントについて、締結済みの BAA が保管されていません',
        'zh': '此租户档案中没有已签署的 BAA',
        'hi': 'इस टेनेंट हेतु फ़ाइल पर कोई निष्पादित BAA नहीं',
        'ar': 'لا توجد اتفاقية شريك أعمال منفَّذة في سجل هذا المستأجر',
    },
    'no lesson covers that screen': {
        'es': 'ninguna lección cubre esa pantalla',
        'fr': 'aucune leçon ne couvre cet écran',
        'de': 'keine Lektion behandelt diesen Bildschirm',
        'pt': 'nenhuma lição cobre esse ecrã',
        'it': 'nessuna lezione copre quella schermata',
        'ja': 'その画面を扱うレッスンはありません',
        'zh': '没有课程涵盖该屏幕',
        'hi': 'उस स्क्रीन को कोई पाठ नहीं समेटता',
        'ar': 'لا يغطّي أي درس تلك الشاشة',
    },
    'no notification channel is configured': {
        'es': 'no hay ningún canal de notificación configurado',
        'fr': 'aucun canal de notification n\'est configuré',
        'de': 'es ist kein Benachrichtigungskanal konfiguriert',
        'pt': 'não há nenhum canal de notificação configurado',
        'it': 'nessun canale di notifica configurato',
        'ja': '通知チャネルが設定されていません',
        'zh': '未配置通知渠道',
        'hi': 'कोई सूचना चैनल कॉन्फ़िगर नहीं है',
        'ar': 'لا توجد قناة إشعار مُهيّأة',
    },
    'no record at that key': {
        'es': 'no hay ningún registro en esa clave',
        'fr': 'aucun enregistrement à cette clé',
        'de': 'kein Datensatz unter diesem Schlüssel',
        'pt': 'não há nenhum registo nessa chave',
        'it': 'nessun record a quella chiave',
        'ja': 'そのキーにレコードはありません',
        'zh': '该键下没有记录',
        'hi': 'उस कुंजी पर कोई अभिलेख नहीं',
        'ar': 'لا يوجد سجلّ عند هذا المفتاح',
    },
    'no such bequest': {
        'es': 'no existe ese legado',
        'fr': 'aucun legs de ce nom',
        'de': 'kein solches Vermächtnis',
        'pt': 'não existe esse legado',
        'it': 'nessun lascito di questo tipo',
        'ja': 'そのような遺贈はありません',
        'zh': '没有该遗赠',
        'hi': 'ऐसी कोई विरासत नहीं',
        'ar': 'لا توجد وصية بهذا الوصف',
    },
    'no transcript for this ring': {
        'es': 'no hay transcripción para este timbre',
        'fr': 'aucune transcription pour cette sonnerie',
        'de': 'kein Protokoll für dieses Klingeln',
        'pt': 'não há transcrição para este toque',
        'it': 'nessuna trascrizione per questa chiamata',
        'ja': 'この呼び出しの記録はありません',
        'zh': '此呼叫没有记录文本',
        'hi': 'इस घंटी हेतु कोई प्रतिलेख नहीं',
        'ar': 'لا يوجد نص لهذا الرنين',
    },
    'not your tenant': {
        'es': 'no es su inquilino',
        'fr': 'ce n\'est pas votre locataire',
        'de': 'nicht Ihr Mandant',
        'pt': 'não é o seu inquilino',
        'it': 'non è il tuo tenant',
        'ja': 'あなたのテナントではありません',
        'zh': '这不是您的租户',
        'hi': 'यह आपका टेनेंट नहीं है',
        'ar': 'ليس مستأجرك',
    },
    'nothing has been submitted to this intake yet': {
        'es': 'todavía no se ha enviado nada a esta recepción',
        'fr': 'rien n\'a encore été déposé dans cette admission',
        'de': 'zu dieser Aufnahme wurde noch nichts eingereicht',
        'pt': 'ainda não foi enviado nada para esta receção',
        'it': 'non è ancora stato inviato nulla a questa acquisizione',
        'ja': 'この受付には、まだ何も提出されていません',
        'zh': '此接收单尚未收到任何提交',
        'hi': 'इस इनटेक में अभी तक कुछ भी जमा नहीं किया गया',
        'ar': 'لم يُقدَّم شيء إلى هذا الاستلام بعد',
    },
    'page not found': {
        'es': 'página no encontrada',
        'fr': 'page introuvable',
        'de': 'Seite nicht gefunden',
        'pt': 'página não encontrada',
        'it': 'pagina non trovata',
        'ja': 'ページが見つかりません',
        'zh': '未找到页面',
        'hi': 'पृष्ठ नहीं मिला',
        'ar': 'لم يُعثر على الصفحة',
    },
    'position not found': {
        'es': 'puesto no encontrado',
        'fr': 'poste introuvable',
        'de': 'Position nicht gefunden',
        'pt': 'posição não encontrada',
        'it': 'posizione non trovata',
        'ja': 'ポジションが見つかりません',
        'zh': '未找到岗位',
        'hi': 'पद नहीं मिला',
        'ar': 'لم يُعثر على المنصب',
    },
    'rating must be 1–5': {
        'es': 'la valoración debe estar entre 1 y 5',
        'fr': 'la note doit être comprise entre 1 et 5',
        'de': 'die Bewertung muss zwischen 1 und 5 liegen',
        'pt': 'a avaliação deve estar entre 1 e 5',
        'it': 'la valutazione deve essere compresa tra 1 e 5',
        'ja': '評価は1〜5の範囲で指定してください',
        'zh': '评分必须为 1–5',
        'hi': 'रेटिंग 1–5 के बीच होनी चाहिए',
        'ar': 'يجب أن يكون التقييم بين 1 و5',
    },
    'record not found': {
        'es': 'registro no encontrado',
        'fr': 'enregistrement introuvable',
        'de': 'Datensatz nicht gefunden',
        'pt': 'registo não encontrado',
        'it': 'record non trovato',
        'ja': 'レコードが見つかりません',
        'zh': '未找到记录',
        'hi': 'अभिलेख नहीं मिला',
        'ar': 'لم يُعثر على السجل',
    },
    'ring not found': {
        'es': 'timbre no encontrado',
        'fr': 'sonnerie introuvable',
        'de': 'Klingeln nicht gefunden',
        'pt': 'toque não encontrado',
        'it': 'chiamata non trovata',
        'ja': '呼び出しが見つかりません',
        'zh': '未找到呼叫',
        'hi': 'घंटी नहीं मिली',
        'ar': 'لم يُعثر على الرنين',
    },
    'robot has been unbound': {
        'es': 'el robot ha sido desvinculado',
        'fr': 'le robot a été dissocié',
        'de': 'der Roboter wurde entkoppelt',
        'pt': 'o robô foi desassociado',
        'it': 'il robot è stato scollegato',
        'ja': 'このロボットは紐づけを解除されました',
        'zh': '该机器人已解绑',
        'hi': 'रोबोट को अनबाइंड कर दिया गया है',
        'ar': 'تم فكّ ارتباط الروبوت',
    },
    'robot not found': {
        'es': 'robot no encontrado',
        'fr': 'robot introuvable',
        'de': 'Roboter nicht gefunden',
        'pt': 'robô não encontrado',
        'it': 'robot non trovato',
        'ja': 'ロボットが見つかりません',
        'zh': '未找到机器人',
        'hi': 'रोबोट नहीं मिला',
        'ar': 'لم يُعثر على الروبوت',
    },
    'roster entry not found': {
        'es': 'entrada de la lista no encontrada',
        'fr': 'entrée du tableau introuvable',
        'de': 'Dienstplaneintrag nicht gefunden',
        'pt': 'entrada da lista não encontrada',
        'it': 'voce dell\'elenco non trovata',
        'ja': '名簿の項目が見つかりません',
        'zh': '未找到名册条目',
        'hi': 'रोस्टर प्रविष्टि नहीं मिली',
        'ar': 'لم يُعثر على مُدخل القائمة',
    },
    'tenant not found': {
        'es': 'inquilino no encontrado',
        'fr': 'locataire introuvable',
        'de': 'Mandant nicht gefunden',
        'pt': 'inquilino não encontrado',
        'it': 'tenant non trovato',
        'ja': 'テナントが見つかりません',
        'zh': '未找到租户',
        'hi': 'टेनेंट नहीं मिला',
        'ar': 'لم يُعثر على المستأجر',
    },
    'that is not the key this tenant\'s records are sealed under — refusing before use, so a wrong key cannot write records that nothing can open later': {
        'es': 'esa no es la clave con la que están sellados los registros de este inquilino — se rechaza antes de usarla, para que una clave equivocada no pueda escribir registros que después nada pueda abrir',
        'fr': 'ce n\'est pas la clé sous laquelle les enregistrements de ce locataire sont scellés — refus avant utilisation, pour qu\'une mauvaise clé ne puisse pas écrire des enregistrements que plus rien n\'ouvrira ensuite',
        'de': 'das ist nicht der Schlüssel, unter dem die Datensätze dieses Mandanten versiegelt sind — Ablehnung vor der Verwendung, damit ein falscher Schlüssel keine Datensätze schreibt, die später nichts mehr öffnen kann',
        'pt': 'essa não é a chave sob a qual os registos deste inquilino estão selados — recusa antes de usar, para que uma chave errada não possa escrever registos que depois nada consiga abrir',
        'it': 'non è la chiave sotto cui sono sigillati i record di questo tenant — rifiuto prima dell\'uso, così una chiave sbagliata non può scrivere record che poi nulla potrà aprire',
        'ja': 'このテナントのレコードが封印されている鍵ではありません — 使用前に拒否します。誤った鍵で、あとから何も開けられないレコードを書き込ませないためです',
        'zh': '这不是此租户记录所使用的封存密钥 — 在使用前即予拒绝，以免错误的密钥写入日后无法打开的记录',
        'hi': 'यह वह कुंजी नहीं है जिसके अंतर्गत इस टेनेंट के अभिलेख सील हैं — उपयोग से पहले ही अस्वीकार, ताकि गलत कुंजी ऐसे अभिलेख न लिखे जिन्हें बाद में कुछ भी न खोल सके',
        'ar': 'ليس هذا المفتاح الذي خُتمت به سجلات هذا المستأجر — نرفض قبل الاستخدام كي لا يكتب مفتاح خاطئ سجلات لا يستطيع شيء فتحها لاحقًا',
    },
    'that key is outside this bequest\'s scope': {
        'es': 'esa clave está fuera del alcance de este legado',
        'fr': 'cette clé est hors de la portée de ce legs',
        'de': 'dieser Schlüssel liegt außerhalb des Umfangs dieses Vermächtnisses',
        'pt': 'essa chave está fora do âmbito deste legado',
        'it': 'quella chiave è fuori dall\'ambito di questo lascito',
        'ja': 'その鍵は、この遺贈の範囲外です',
        'zh': '该键不在此遗赠的范围内',
        'hi': 'वह कुंजी इस विरासत के दायरे से बाहर है',
        'ar': 'ذلك المفتاح خارج نطاق هذه الوصية',
    },
    'this vault has been closed by its owner; the bequest cannot be read': {
        'es': 'esta bóveda ha sido cerrada por su propietario; el legado no se puede leer',
        'fr': 'ce coffre a été fermé par son propriétaire ; le legs ne peut pas être lu',
        'de': 'dieser Tresor wurde von seiner Inhaberin oder seinem Inhaber geschlossen; das Vermächtnis kann nicht gelesen werden',
        'pt': 'este cofre foi encerrado pelo seu proprietário; o legado não pode ser lido',
        'it': 'questo caveau è stato chiuso dal suo proprietario; il lascito non può essere letto',
        'ja': 'この保管庫は所有者によって閉じられました。遺贈を読み取ることはできません',
        'zh': '此保管库已被其所有者关闭，无法读取该遗赠',
        'hi': 'यह तिजोरी इसके स्वामी द्वारा बंद कर दी गई है; यह विरासत पढ़ी नहीं जा सकती',
        'ar': 'أُغلقت هذه الخزنة من مالكها؛ لا يمكن قراءة هذه الوصية',
    },
    'this bequest was revoked by its owner': {
        'es': 'este legado fue revocado por su propietario',
        'fr': 'ce legs a été révoqué par son propriétaire',
        'de': 'dieses Vermächtnis wurde von seiner Inhaberin oder seinem Inhaber widerrufen',
        'pt': 'este legado foi revogado pelo seu proprietário',
        'it': 'questo lascito è stato revocato dal suo proprietario',
        'ja': 'この遺贈は、その所有者によって取り消されました',
        'zh': '此遗赠已被其所有者撤销',
        'hi': 'यह विरासत इसके स्वामी द्वारा रद्द कर दी गई',
        'ar': 'أُلغيت هذه الوصية من مالكها',
    },
    'this connector is for collecting, not publishing': {
        'es': 'este conector es para recopilar, no para publicar',
        'fr': 'ce connecteur sert à collecter, pas à publier',
        'de': 'dieser Connector dient dem Sammeln, nicht dem Veröffentlichen',
        'pt': 'este conector é para recolher e não para publicar',
        'it': 'questo connettore serve a raccogliere, non a pubblicare',
        'ja': 'このコネクタは収集用であり、公開用ではありません',
        'zh': '此连接器用于收集，而非发布',
        'hi': 'यह कनेक्टर एकत्र करने के लिए है, प्रकाशन के लिए नहीं',
        'ar': 'هذا الموصّل للجمع لا للنشر',
    },
    'this connector is for publishing, not collecting': {
        'es': 'este conector es para publicar, no para recopilar',
        'fr': 'ce connecteur sert à publier, pas à collecter',
        'de': 'dieser Connector dient dem Veröffentlichen, nicht dem Sammeln',
        'pt': 'este conector é para publicar e não para recolher',
        'it': 'questo connettore serve a pubblicare, non a raccogliere',
        'ja': 'このコネクタは公開用であり、収集用ではありません',
        'zh': '此连接器用于发布，而非收集',
        'hi': 'यह कनेक्टर प्रकाशन के लिए है, एकत्र करने के लिए नहीं',
        'ar': 'هذا الموصّل للنشر لا للجمع',
    },
    'this intake is no longer open': {
        'es': 'esta recepción ya no está abierta',
        'fr': 'cette admission n\'est plus ouverte',
        'de': 'diese Aufnahme ist nicht mehr geöffnet',
        'pt': 'esta receção já não está aberta',
        'it': 'questa acquisizione non è più aperta',
        'ja': 'この受付は既に閉じられています',
        'zh': '此接收单已不再开放',
        'hi': 'यह इनटेक अब खुला नहीं है',
        'ar': 'لم يعد هذا الاستلام مفتوحًا',
    },
    'this page was already delivered': {
        'es': 'esta página ya fue entregada',
        'fr': 'cette page a déjà été remise',
        'de': 'diese Seite wurde bereits zugestellt',
        'pt': 'esta página já foi entregue',
        'it': 'questa pagina è già stata consegnata',
        'ja': 'このページは既に届けられました',
        'zh': '此页面已送达',
        'hi': 'यह पृष्ठ पहले ही पहुँचाया जा चुका है',
        'ar': 'سبق أن سُلّمت هذه الصفحة',
    },
    'this ring has already been answered': {
        'es': 'este timbre ya ha sido atendido',
        'fr': 'cette sonnerie a déjà reçu une réponse',
        'de': 'dieses Klingeln wurde bereits beantwortet',
        'pt': 'este toque já foi atendido',
        'it': 'questa chiamata ha già ricevuto risposta',
        'ja': 'この呼び出しには既に応答済みです',
        'zh': '此呼叫已被应答',
        'hi': 'इस घंटी का उत्तर पहले ही दिया जा चुका है',
        'ar': 'سبق الردّ على هذا الرنين',
    },
    'this tenant\'s records are sealed under a customer-managed key; present it in the x-tenant-key header (base64 of 32 bytes)': {
        'es': 'los registros de este inquilino están sellados con una clave gestionada por el cliente; preséntela en la cabecera x-tenant-key (base64 de 32 bytes)',
        'fr': 'les enregistrements de ce locataire sont scellés sous une clé gérée par le client ; présentez-la dans l\'en-tête x-tenant-key (base64 de 32 octets)',
        'de': 'die Datensätze dieses Mandanten sind mit einem kundenverwalteten Schlüssel versiegelt; legen Sie ihn im Header x-tenant-key vor (Base64 von 32 Bytes)',
        'pt': 'os registos deste inquilino estão selados com uma chave gerida pelo cliente; apresente-a no cabeçalho x-tenant-key (base64 de 32 bytes)',
        'it': 'i record di questo tenant sono sigillati con una chiave gestita dal cliente; presentala nell\'intestazione x-tenant-key (base64 di 32 byte)',
        'ja': 'このテナントのレコードは顧客管理の鍵で封印されています。x-tenant-key ヘッダーで提示してください（32 バイトの base64）',
        'zh': '此租户的记录以客户自管密钥封存；请通过 x-tenant-key 标头出示（32 字节的 base64）',
        'hi': 'इस टेनेंट के अभिलेख ग्राहक-प्रबंधित कुंजी से सील हैं; इसे x-tenant-key हेडर में प्रस्तुत करें (32 बाइट का base64)',
        'ar': 'سجلات هذا المستأجر مختومة بمفتاح يديره العميل؛ قدِّمه في ترويسة x-tenant-key (base64 لـ 32 بايت)',
    },
    'token not found': {
        'es': 'token no encontrado',
        'fr': 'jeton introuvable',
        'de': 'Token nicht gefunden',
        'pt': 'token não encontrado',
        'it': 'token non trovato',
        'ja': 'トークンが見つかりません',
        'zh': '未找到令牌',
        'hi': 'टोकन नहीं मिला',
        'ar': 'لم يُعثر على الرمز',
    },
    'transfer not found': {
        'es': 'transferencia no encontrada',
        'fr': 'transfert introuvable',
        'de': 'Übertragung nicht gefunden',
        'pt': 'transferência não encontrada',
        'it': 'trasferimento non trovato',
        'ja': '転送が見つかりません',
        'zh': '未找到传输',
        'hi': 'स्थानांतरण नहीं मिला',
        'ar': 'لم يُعثر على النقل',
    },
    'missing tenant bearer token': {
        'es': 'falta el token bearer del inquilino',
        'fr': 'jeton bearer du locataire manquant',
        'de': 'Bearer-Token des Mandanten fehlt',
        'pt': 'falta o token bearer do inquilino',
        'it': 'manca il token bearer del tenant',
        'ja': 'テナントのベアラートークンがありません',
        'zh': '缺少租户 bearer 令牌',
        'hi': 'टेनेंट का bearer टोकन गायब है',
        'ar': 'رمز bearer الخاص بالمستأجر مفقود',
    },
    'invalid tenant token': {
        'es': 'token de inquilino no válido',
        'fr': 'jeton de locataire invalide',
        'de': 'ungültiges Mandanten-Token',
        'pt': 'token de inquilino inválido',
        'it': 'token del tenant non valido',
        'ja': 'テナントトークンが無効です',
        'zh': '租户令牌无效',
        'hi': 'टेनेंट टोकन अमान्य है',
        'ar': 'رمز المستأجر غير صالح',
    },
    'this token is read-only': {
        'es': 'este token es de solo lectura',
        'fr': 'ce jeton est en lecture seule',
        'de': 'dieses Token ist schreibgeschützt',
        'pt': 'este token é apenas de leitura',
        'it': 'questo token è di sola lettura',
        'ja': 'このトークンは読み取り専用です',
        'zh': '此令牌为只读',
        'hi': 'यह टोकन केवल पढ़ने के लिए है',
        'ar': 'هذا الرمز للقراءة فقط',
    },
    'admin bearer token required': {
        'es': 'se requiere un token bearer de administración',
        'fr': "jeton bearer d'administration requis",
        'de': 'Admin-Bearer-Token erforderlich',
        'pt': 'é necessário um token bearer de administração',
        'it': 'è richiesto un token bearer di amministrazione',
        'ja': '管理用のベアラートークンが必要です',
        'zh': '需要管理员 bearer 令牌',
        'hi': 'व्यवस्थापक bearer टोकन आवश्यक है',
        'ar': 'رمز bearer الإداري مطلوب',
    },
    'invalid admin token': {
        'es': 'token de administración no válido',
        'fr': "jeton d'administration invalide",
        'de': 'ungültiges Admin-Token',
        'pt': 'token de administração inválido',
        'it': 'token di amministrazione non valido',
        'ja': '管理トークンが無効です',
        'zh': '管理员令牌无效',
        'hi': 'व्यवस्थापक टोकन अमान्य है',
        'ar': 'رمز الإدارة غير صالح',
    },
    'grant token required': {
        'es': 'se requiere el token de concesión',
        'fr': "jeton d'accès requis",
        'de': 'Zugriffstoken erforderlich',
        'pt': 'é necessário o token de concessão',
        'it': 'è richiesto il token di concessione',
        'ja': '付与トークンが必要です',
        'zh': '需要授权令牌',
        'hi': 'अनुदान टोकन आवश्यक है',
        'ar': 'رمز المنح مطلوب',
    },
    'customer key must be base64': {
        'es': 'la clave del cliente debe estar en base64',
        'fr': 'la clé client doit être en base64',
        'de': 'der Kundenschlüssel muss base64 sein',
        'pt': 'a chave do cliente tem de estar em base64',
        'it': 'la chiave del cliente deve essere in base64',
        'ja': '顧客キーは base64 で指定してください',
        'zh': '客户密钥必须是 base64',
        'hi': 'ग्राहक कुंजी base64 में होनी चाहिए',
        'ar': 'يجب أن يكون مفتاح العميل بترميز base64',
    },
    'customer key must be base64 of 32 bytes': {
        'es': 'la clave del cliente debe ser base64 de 32 bytes',
        'fr': 'la clé client doit être du base64 de 32 octets',
        'de': 'der Kundenschlüssel muss base64 von 32 Bytes sein',
        'pt': 'a chave do cliente tem de ser base64 de 32 bytes',
        'it': 'la chiave del cliente deve essere base64 di 32 byte',
        'ja': '顧客キーは 32 バイトを base64 にしたものにしてください',
        'zh': '客户密钥必须是 32 字节的 base64',
        'hi': 'ग्राहक कुंजी 32 बाइट का base64 होनी चाहिए',
        'ar': 'يجب أن يكون مفتاح العميل base64 لـ 32 بايت',
    },
}


# --------------------------------------------------------------------------- #
# The refusal that handed the body back
# --------------------------------------------------------------------------- #
#
# The round before this one put every refusal this product *writes* into the
# reader's language, through three handlers that all return by one door. It
# missed every refusal this product *returns*.
#
#     asked     is every refusal this product writes translated
#     mattered  is every refusal this product returns
#
# `RequestValidationError` is not an `HTTPException` and is not a domain error
# either. FastAPI raises it before routing finishes and
# renders it with its own handler, so a 422 — the refusal a person meets most
# often, because it is what a mistyped form produces — went out past all
# three.
#
# ## The larger half
#
# Pydantic's error rows carry an `input` key holding **the value that failed**,
# which for a missing field is the entire submitted body. So a journal entry
# came straight back out:
#
#     {"type": "missing", "loc": ["body", "key"], "msg": "Field required",
#      "input": {"k": "patient-1", "v": "HIV positive, disclosed 2019"}}
#
# Every other part of this product's error design refuses to carry content.
# `app/src/errors.ts` and the three `Problems` shells record a method, a
# redacted path and a status, and have no parameter a message could arrive
# through. `cloudgw` refuses a report whole if it finds prose in it rather
# than sanitising it. The one place content left the process was the
# framework's default renderer, because nobody had looked at it as ours.
#
#     asked     does this product record anything private
#     mattered  does this product return anything private
#
# ## What is returned now
#
# `type` and `loc`, which are the console's vocabulary — it highlights the
# field `loc` names — and `msg`. Not `input`, and not `ctx`: `ctx` carries a
# validator's own exception on `value_error`, which is a second door into the
# same room.
#
# Two narrower rules, both for text that comes from *our* code rather than
# pydantic's fixed catalogue:
#
# * `value_error` and `assertion_error` messages are replaced outright. Their
#   text is whatever a validator raised, and a validator that quotes the value
#   it rejected is the same leak wearing a different key.
# * On `extra_forbidden`, the last element of `loc` is the caller's own key
#   name rather than a field this product declares — so it is echoed only when
#   it is *shaped* like a field name. Naming the key is the point of that
#   refusal; a key with spaces in it is not a typo, it is content.


#: What is said instead of a validator's own words. Deliberately useless as a
#: hint: `loc` still names the field, and a sentence that explained more would
#: be quoting the thing this exists to stop quoting.
UNSPECIFIED_VALUE_ERROR = "that value is not acceptable here"

#: Where a caller's own key name would otherwise be echoed.
UNRECOGNISED_FIELD = "<unrecognised field>"

#: What a mistyped field name looks like. A key matching this is echoed back on
#: `extra_forbidden`, because naming it is the whole value of that refusal:
#: `test_a_write_that_answers_200_did_something` exists because two routes used
#: to accept `dials` for `values` and `years` for `period`, discard them, and
#: answer 200. A round was spent making those strict so the caller is *told*
#: which key was wrong, and the first version of this file redacted it away
#: again — caught by that guard, which is what it was written for.
#:
#:     asked     can a key carry content
#:     mattered  does this key look like content
#:
#: Anything else — a key with spaces in it, a sentence, something longer than a
#: field name has any business being — is replaced. A client that builds an
#: object keyed on what somebody typed produces exactly that shape.
_FIELD_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,39}$")

_OUR_OWN_WORDS = ("value_error", "assertion_error")


def validation_detail(errors, language: str) -> list[dict]:
    """Pydantic's error rows, with everything the caller sent taken out.

    Built by allowing three keys rather than by removing `input`. A denylist
    would have to be revisited every time pydantic adds a key; this cannot
    grow a leak by someone else's release.
    """
    rows = []
    for error in errors:
        kind = str(error.get("type", ""))
        where = list(error.get("loc", ()))
        if (kind == "extra_forbidden" and where
                and not _FIELD_NAME.match(str(where[-1]))):
            where[-1] = UNRECOGNISED_FIELD
        message = (UNSPECIFIED_VALUE_ERROR if kind in _OUR_OWN_WORDS
                   else str(error.get("msg", "")))
        rows.append({
            "type": kind,
            "loc": [p if isinstance(p, int) else str(p) for p in where],
            "msg": tr_refusal(message, language),
        })
    return rows


#: The first element of a pydantic `loc`, naming which part of the request the
#: field was in rather than naming a field. Dropped when composing the
#: sentence: a person reading "body.display_name" learns nothing from "body"
#: that the form they are looking at has not already told them.
_WHERE_MARKERS = ("body", "query", "path", "header", "cookie")


#: The label the form shows, for the fields a person types into one.
#:
#: `validation_message` used to render pydantic's own field name, so a mistyped
#: form said `display_name — Field required` while the form beside it said
#: something a person could read, in ten languages.
#:
#:     asked     is the refusal a sentence in the reader's language
#:     mattered  does it name the field the reader can see
#:
#: Server-side, where the sentence is composed, for the reason it is composed
#: here at all: nine clients rendering it is nine chances to render it
#: differently.
#:
#: The rows shared with the sibling products carry the sibling products'
#: wording, byte for byte. One vocabulary across three products is one thing to
#: keep right; three is three, and the drift shows up first in the language
#: nobody here reads.
#:
#: A field with no row keeps its identifier — an identifier a reader can match
#: to the form beats a word invented for them — and is recorded in
#: `pdi/tests/field_labels_unmapped.txt`.
_FIELD_LABELS: dict[str, dict[str, str]] = {
    # The accessibility report's three questions, worded as the form asks
    # them — a refusal that names one of these should read like the form.
    'doing': {'en': 'What were you trying to do?', 'es': '¿Qué intentabas hacer?', 'fr': 'Qu’essayiez-vous de faire ?', 'de': 'Was hast du versucht zu tun?', 'pt': 'O que você estava tentando fazer?', 'it': 'Cosa stavi cercando di fare?', 'ja': '何をしようとしていましたか？', 'zh': '你当时想做什么？', 'hi': 'आप क्या करने की कोशिश कर रहे थे?', 'ar': 'ما الذي كنت تحاول فعله؟'},
    'wall': {'en': 'What stood in the way?', 'es': '¿Qué se interpuso?', 'fr': 'Qu’est-ce qui a fait obstacle ?', 'de': 'Was stand im Weg?', 'pt': 'O que ficou no caminho?', 'it': 'Cosa ti ha ostacolato?', 'ja': '何が妨げになりましたか？', 'zh': '是什么挡住了你？', 'hi': 'क्या आड़े आया?', 'ar': 'ما الذي وقف في الطريق؟'},
    'help': {'en': 'What would help?', 'es': '¿Qué ayudaría?', 'fr': 'Qu’est-ce qui aiderait ?', 'de': 'Was würde helfen?', 'pt': 'O que ajudaria?', 'it': 'Cosa aiuterebbe?', 'ja': '何があれば助かりますか？', 'zh': '什么会有帮助？', 'hi': 'क्या मदद करेगा?', 'ar': 'ما الذي قد يساعد؟'},
    'lang': {'en': 'Language', 'es': 'Idioma', 'fr': 'Langue', 'de': 'Sprache', 'pt': 'Idioma', 'it': 'Lingua', 'ja': '言語', 'zh': '语言', 'hi': 'भाषा', 'ar': 'اللغة'},
    'content': {'en': 'Content', 'es': 'Contenido', 'fr': 'Contenu', 'de': 'Inhalt', 'pt': 'Conteúdo', 'it': 'Contenuto', 'ja': '内容', 'zh': '内容', 'hi': 'सामग्री', 'ar': 'المحتوى'},
    'grantee_name': {'en': 'Grantee', 'es': 'Beneficiario', 'fr': 'Bénéficiaire', 'de': 'Begünstigte Person', 'pt': 'Beneficiário', 'it': 'Beneficiario', 'ja': '受贈者', 'zh': '受赠人', 'hi': 'अनुदानग्राही', 'ar': 'المستفيد'},
    'handle': {'en': 'Handle', 'es': 'Identificador', 'fr': 'Identifiant', 'de': 'Kürzel', 'pt': 'Identificador', 'it': 'Handle', 'ja': 'ハンドル名', 'zh': '账号名', 'hi': 'हैंडल', 'ar': 'المعرّف'},
    'key': {'en': 'Key', 'es': 'Clave', 'fr': 'Clé', 'de': 'Schlüssel', 'pt': 'Chave', 'it': 'Chiave', 'ja': 'キー', 'zh': '键', 'hi': 'कुंजी', 'ar': 'المفتاح'},
    'key_prefixes': {'en': 'Key prefixes', 'es': 'Prefijos de clave', 'fr': 'Préfixes de clé', 'de': 'Schlüsselpräfixe', 'pt': 'Prefixos de chave', 'it': 'Prefissi di chiave', 'ja': 'キーの接頭辞', 'zh': '键前缀', 'hi': 'कुंजी उपसर्ग', 'ar': 'بادئات المفاتيح'},
    'message': {'en': 'Message', 'es': 'Mensaje', 'fr': 'Message', 'de': 'Nachricht', 'pt': 'Mensagem', 'it': 'Messaggio', 'ja': 'メッセージ', 'zh': '消息', 'hi': 'संदेश', 'ar': 'الرسالة'},
    'name': {'en': 'Name', 'es': 'Nombre', 'fr': 'Nom', 'de': 'Name', 'pt': 'Nome', 'it': 'Nome', 'ja': '名前', 'zh': '名称', 'hi': 'नाम', 'ar': 'الاسم'},
    'note': {'en': 'Note', 'es': 'Nota', 'fr': 'Note', 'de': 'Notiz', 'pt': 'Nota', 'it': 'Nota', 'ja': 'メモ', 'zh': '备注', 'hi': 'टिप्पणी', 'ar': 'ملاحظة'},
    'purpose': {'en': 'Purpose', 'es': 'Propósito', 'fr': 'Objectif', 'de': 'Zweck', 'pt': 'Finalidade', 'it': 'Scopo', 'ja': '目的', 'zh': '用途', 'hi': 'उद्देश्य', 'ar': 'الغرض'},
    'topic': {'en': 'Topic', 'es': 'Tema', 'fr': 'Sujet', 'de': 'Thema', 'pt': 'Tema', 'it': 'Argomento', 'ja': 'トピック', 'zh': '主题', 'hi': 'विषय', 'ar': 'الموضوع'},    'comfortable_automation': {'en': 'Comfortable with phased automation', 'es': 'Cómodo con una automatización por fases', 'fr': 'À l’aise avec une automatisation progressive', 'de': 'Einverstanden mit schrittweiser Automatisierung', 'pt': 'Confortável com automatização faseada', 'it': 'A proprio agio con un’automazione graduale', 'ja': '段階的な自動化に前向き', 'zh': '接受分阶段自动化', 'hi': 'चरणबद्ध स्वचालन से सहज', 'ar': 'مرتاح لأتمتة تدريجية'},
    'compliance_accountable': {'en': 'Accountable for safety / regulatory compliance', 'es': 'Responsable del cumplimiento de seguridad / normativa', 'fr': 'Responsable de la conformité sécurité / réglementaire', 'de': 'Verantwortlich für Sicherheits- / Regelkonformität', 'pt': 'Responsável pela conformidade de segurança / regulamentar', 'it': 'Responsabile della conformità in materia di sicurezza / normativa', 'ja': '安全・規制順守の責任を負う', 'zh': '对安全／合规负责', 'hi': 'सुरक्षा / नियामक अनुपालन के लिए उत्तरदायी', 'ar': 'مسؤول عن الامتثال للسلامة / اللوائح'},
    'customer_legal_name': {'en': 'Customer legal name', 'es': 'Razón social del cliente', 'fr': 'Raison sociale du client', 'de': 'Rechtlicher Name des Kunden', 'pt': 'Denominação legal do cliente', 'it': 'Ragione sociale del cliente', 'ja': '顧客の法人名', 'zh': '客户法定名称', 'hi': 'ग्राहक का कानूनी नाम', 'ar': 'الاسم القانوني للعميل'},
    'department': {'en': 'Department', 'es': 'Departamento', 'fr': 'Service', 'de': 'Abteilung', 'pt': 'Departamento', 'it': 'Reparto', 'ja': '部署', 'zh': '部门', 'hi': 'विभाग', 'ar': 'القسم'},
    'direction': {'en': 'Direction', 'es': 'Sentido', 'fr': 'Sens', 'de': 'Richtung', 'pt': 'Direção', 'it': 'Direzione', 'ja': '方向', 'zh': '方向', 'hi': 'दिशा', 'ar': 'الاتجاه'},
    'disclose': {'en': 'What a scan discloses', 'es': 'Qué revela un escaneo', 'fr': 'Ce qu’un scan révèle', 'de': 'Was ein Scan preisgibt', 'pt': 'O que uma leitura revela', 'it': 'Che cosa rivela una scansione', 'ja': 'スキャンで開示される内容', 'zh': '扫描会透露什么', 'hi': 'स्कैन क्या बताता है', 'ar': 'ما يكشفه المسح'},
    'documents_incidents': {'en': 'Documents incidents / maintenance', 'es': 'Documenta incidentes / mantenimiento', 'fr': 'Documente incidents / maintenance', 'de': 'Dokumentiert Vorfälle / Wartung', 'pt': 'Documenta incidentes / manutenção', 'it': 'Documenta incidenti / manutenzione', 'ja': 'インシデント・保守の記録', 'zh': '记录事故／维护', 'hi': 'घटनाएँ / रखरखाव दर्ज करता है', 'ar': 'يوثّق الحوادث / الصيانة'},
    'effective_date': {'en': 'Effective date', 'es': 'Fecha de entrada en vigor', 'fr': 'Date d’entrée en vigueur', 'de': 'Datum des Inkrafttretens', 'pt': 'Data de entrada em vigor', 'it': 'Data di decorrenza', 'ja': '発効日', 'zh': '生效日期', 'hi': 'प्रभावी तिथि', 'ar': 'تاريخ السريان'},
    'filename': {'en': 'Filename', 'es': 'Nombre del archivo', 'fr': 'Nom du fichier', 'de': 'Dateiname', 'pt': 'Nome do ficheiro', 'it': 'Nome del file', 'ja': 'ファイル名', 'zh': '文件名', 'hi': 'फ़ाइल नाम', 'ar': 'اسم الملف'},
    'from_party': {'en': 'Requesting party', 'es': 'Parte solicitante', 'fr': 'Partie demandeuse', 'de': 'Anfragende Partei', 'pt': 'Parte requerente', 'it': 'Parte richiedente', 'ja': '依頼元', 'zh': '请求方', 'hi': 'अनुरोधकर्ता पक्ष', 'ar': 'الجهة الطالبة'},
    'industry': {'en': 'Industry', 'es': 'Sector', 'fr': 'Secteur', 'de': 'Branche', 'pt': 'Setor', 'it': 'Settore', 'ja': '業界', 'zh': '行业', 'hi': 'उद्योग', 'ar': 'القطاع'},
    'interaction': {'en': 'Interaction', 'es': 'Interacción', 'fr': 'Interaction', 'de': 'Interaktion', 'pt': 'Interação', 'it': 'Interazione', 'ja': 'やり取りの方法', 'zh': '交互方式', 'hi': 'संवाद', 'ar': 'التفاعل'},
    'job_title': {'en': 'Job title', 'es': 'Puesto', 'fr': 'Intitulé du poste', 'de': 'Berufsbezeichnung', 'pt': 'Cargo', 'it': 'Qualifica', 'ja': '職種', 'zh': '职位', 'hi': 'पद', 'ar': 'المسمى الوظيفي'},
    'kind': {'en': 'Kind', 'es': 'Tipo', 'fr': 'Type', 'de': 'Art', 'pt': 'Tipo', 'it': 'Tipo', 'ja': '種類', 'zh': '类型', 'hi': 'प्रकार', 'ar': 'النوع'},
    'label': {'en': 'Label', 'es': 'Etiqueta', 'fr': 'Libellé', 'de': 'Bezeichnung', 'pt': 'Etiqueta', 'it': 'Etichetta', 'ja': 'ラベル', 'zh': '标签', 'hi': 'लेबल', 'ar': 'التسمية'},
    'language': {'en': 'Language', 'es': 'Idioma', 'fr': 'Langue', 'de': 'Sprache', 'pt': 'Idioma', 'it': 'Lingua', 'ja': '言語', 'zh': '语言', 'hi': 'भाषा', 'ar': 'اللغة'},
    'learn_decision_style': {'en': 'Learn my decision-making style (suggest, never take, actions)', 'es': 'Aprender mi estilo de decisión (sugerir acciones, nunca ejecutarlas)', 'fr': 'Apprendre mon style de décision (suggérer des actions, jamais les exécuter)', 'de': 'Meinen Entscheidungsstil lernen (Aktionen vorschlagen, nie ausführen)', 'pt': 'Aprender o meu estilo de decisão (sugerir ações, nunca executá-las)', 'it': 'Imparare il mio stile decisionale (suggerire azioni, mai eseguirle)', 'ja': '私の意思決定スタイルを学習する（提案のみ、実行はしない）', 'zh': '学习我的决策风格（只建议，绝不代行）', 'hi': 'मेरी निर्णय-शैली सीखें (सुझाव दें, कार्रवाई कभी न करें)', 'ar': 'تعلّم أسلوبي في اتخاذ القرار (اقتراح الإجراءات دون تنفيذها)'},
    'manages': {'en': 'What this role manages day-to-day', 'es': 'Lo que esta función gestiona a diario', 'fr': 'Ce que ce poste gère au quotidien', 'de': 'Was diese Rolle täglich verantwortet', 'pt': 'O que esta função gere no dia a dia', 'it': 'Ciò che questo ruolo gestisce ogni giorno', 'ja': 'この役割が日々担うもの', 'zh': '这个岗位每天负责什么', 'hi': 'यह भूमिका रोज़ क्या संभालती है', 'ar': 'ما يديره هذا الدور يوميًا'},
    'manages_staff': {'en': 'Staff managed', 'es': 'Personal a cargo', 'fr': 'Effectif encadré', 'de': 'Betreute Mitarbeitende', 'pt': 'Pessoas sob gestão', 'it': 'Personale gestito', 'ja': '管理する人数', 'zh': '管理人数', 'hi': 'प्रबंधित कर्मचारी', 'ar': 'عدد الموظفين المُدارين'},
    'manual_tasks': {'en': 'Has manual report / data-entry tasks', 'es': 'Tiene tareas manuales de informes / captura de datos', 'fr': 'A des tâches manuelles de rapport / saisie', 'de': 'Hat manuelle Berichts- / Erfassungsaufgaben', 'pt': 'Tem tarefas manuais de relatório / introdução de dados', 'it': 'Ha attività manuali di reportistica / inserimento dati', 'ja': '手作業の報告・データ入力がある', 'zh': '有手工报表／数据录入工作', 'hi': 'मैनुअल रिपोर्ट / डेटा-एंट्री कार्य हैं', 'ar': 'لديه مهام يدوية للتقارير / إدخال البيانات'},
    'model': {'en': 'Model', 'es': 'Modelo', 'fr': 'Modèle', 'de': 'Modell', 'pt': 'Modelo', 'it': 'Modello', 'ja': 'モデル', 'zh': '模型', 'hi': 'मॉडल', 'ar': 'النموذج'},
    'operator_legal_name': {'en': 'Operator legal name', 'es': 'Razón social del operador', 'fr': 'Raison sociale de l’exploitant', 'de': 'Rechtlicher Name des Betreibers', 'pt': 'Denominação legal do operador', 'it': 'Ragione sociale dell’operatore', 'ja': '運営者の法人名', 'zh': '运营方法定名称', 'hi': 'संचालक का कानूनी नाम', 'ar': 'الاسم القانوني للمشغّل'},
    'outdated_tasks': {'en': 'Outdated tasks (comma-separated)', 'es': 'Tareas obsoletas (separadas por comas)', 'fr': 'Tâches obsolètes (séparées par des virgules)', 'de': 'Veraltete Aufgaben (kommagetrennt)', 'pt': 'Tarefas desatualizadas (separadas por vírgulas)', 'it': 'Attività obsolete (separate da virgole)', 'ja': '時代遅れの作業（カンマ区切り）', 'zh': '过时任务（逗号分隔）', 'hi': 'पुराने पड़ चुके कार्य (अल्पविराम से)', 'ar': 'المهام المتقادمة (مفصولة بفواصل)'},
    'platform': {'en': 'Platform', 'es': 'Plataforma', 'fr': 'Plateforme', 'de': 'Plattform', 'pt': 'Plataforma', 'it': 'Piattaforma', 'ja': 'プラットフォーム', 'zh': '平台', 'hi': 'प्लेटफ़ॉर्म', 'ar': 'المنصة'},
    'question': {'en': 'Question', 'es': 'Pregunta', 'fr': 'Question', 'de': 'Frage', 'pt': 'Pergunta', 'it': 'Domanda', 'ja': '質問', 'zh': '问题', 'hi': 'प्रश्न', 'ar': 'السؤال'},
    'recipient': {'en': 'Recipient', 'es': 'Destinatario', 'fr': 'Destinataire', 'de': 'Empfänger', 'pt': 'Destinatário', 'it': 'Destinatario', 'ja': '送り先', 'zh': '收件方', 'hi': 'प्राप्तकर्ता', 'ar': 'المستلم'},
    'redundant_tasks': {'en': 'Redundant tasks (comma-separated)', 'es': 'Tareas redundantes (separadas por comas)', 'fr': 'Tâches redondantes (séparées par des virgules)', 'de': 'Überflüssige Aufgaben (kommagetrennt)', 'pt': 'Tarefas redundantes (separadas por vírgulas)', 'it': 'Attività ridondanti (separate da virgole)', 'ja': '重複する作業（カンマ区切り）', 'zh': '冗余任务（逗号分隔）', 'hi': 'अनावश्यक कार्य (अल्पविराम से)', 'ar': 'المهام المكرّرة (مفصولة بفواصل)'},
    'ref': {'en': 'Reference', 'es': 'Referencia', 'fr': 'Référence', 'de': 'Referenz', 'pt': 'Referência', 'it': 'Riferimento', 'ja': '参照', 'zh': '引用', 'hi': 'संदर्भ', 'ar': 'المرجع'},
    'ref_kind': {'en': 'What the code stands for', 'es': 'Qué representa el código', 'fr': 'Ce que le code représente', 'de': 'Wofür der Code steht', 'pt': 'O que o código representa', 'it': 'Che cosa rappresenta il codice', 'ja': 'コードが指すもの', 'zh': '这个码代表什么', 'hi': 'कोड किसका प्रतिनिधित्व करता है', 'ar': 'ما يمثّله الرمز'},
    'reskilling_interest': {'en': 'Interested in reskilling / repositioning', 'es': 'Interesado en recualificación / reubicación', 'fr': 'Intéressé par une reconversion / un repositionnement', 'de': 'An Umschulung / Neuausrichtung interessiert', 'pt': 'Interessado em requalificação / reposicionamento', 'it': 'Interessato a riqualificazione / ricollocazione', 'ja': '再教育・配置転換に関心がある', 'zh': '有意接受再培训／岗位调整', 'hi': 'पुनःकौशल / पुनर्नियोजन में रुचि', 'ar': 'مهتم بإعادة التأهيل / إعادة التموضع'},
    'retention': {'en': 'Record retention (up to forever)', 'es': 'Conservación de registros (hasta siempre)', 'fr': 'Conservation des enregistrements (jusqu’à toujours)', 'de': 'Aufbewahrung der Einträge (bis für immer)', 'pt': 'Retenção de registos (até para sempre)', 'it': 'Conservazione dei record (fino a per sempre)', 'ja': '記録の保持期間（無期限まで）', 'zh': '记录保留期（可至永久）', 'hi': 'रिकॉर्ड प्रतिधारण (हमेशा तक)', 'ar': 'الاحتفاظ بالسجلات (حتى الأبد)'},
    'role': {'en': 'Role', 'es': 'Rol', 'fr': 'Rôle', 'de': 'Rolle', 'pt': 'Função', 'it': 'Ruolo', 'ja': '役割', 'zh': '角色', 'hi': 'भूमिका', 'ar': 'الدور'},
    'role_type': {'en': 'Oversight level', 'es': 'Nivel de supervisión', 'fr': 'Niveau de supervision', 'de': 'Aufsichtsebene', 'pt': 'Nível de supervisão', 'it': 'Livello di supervisione', 'ja': '監督レベル', 'zh': '监管层级', 'hi': 'पर्यवेक्षण स्तर', 'ar': 'مستوى الإشراف'},
    'scope': {'en': 'Scope', 'es': 'Alcance', 'fr': 'Périmètre', 'de': 'Umfang', 'pt': 'Âmbito', 'it': 'Ambito', 'ja': '範囲', 'zh': '范围', 'hi': 'दायरा', 'ar': 'النطاق'},
    'source': {'en': 'Source', 'es': 'Fuente', 'fr': 'Source', 'de': 'Quelle', 'pt': 'Fonte', 'it': 'Fonte', 'ja': 'ソース', 'zh': '来源', 'hi': 'स्रोत', 'ar': 'المصدر'},
    'summarize_logs': {'en': 'Summarize the daily activity log', 'es': 'Resumir el registro diario de actividad', 'fr': 'Résumer le journal d’activité quotidien', 'de': 'Das tägliche Aktivitätsprotokoll zusammenfassen', 'pt': 'Resumir o registo diário de atividade', 'it': 'Riassumere il registro giornaliero delle attività', 'ja': '日々の活動ログを要約する', 'zh': '总结每日活动日志', 'hi': 'दैनिक गतिविधि लॉग का सारांश', 'ar': 'تلخيص سجل النشاط اليومي'},
    'text': {'en': 'Text', 'es': 'Texto', 'fr': 'Texte', 'de': 'Text', 'pt': 'Texto', 'it': 'Testo', 'ja': 'テキスト', 'zh': '文本', 'hi': 'पाठ', 'ar': 'النص'},
    'tone': {'en': 'Tone', 'es': 'Tono', 'fr': 'Ton', 'de': 'Ton', 'pt': 'Tom', 'it': 'Tono', 'ja': 'トーン', 'zh': '语气', 'hi': 'लहजा', 'ar': 'النبرة'},
    'value': {'en': 'Value (plaintext — sealed by PDI)', 'es': 'Valor (texto sin cifrar — sellado por PDI)', 'fr': 'Valeur (en clair — scellée par PDI)', 'de': 'Wert (Klartext — von PDI versiegelt)', 'pt': 'Valor (texto simples — selado pelo PDI)', 'it': 'Valore (in chiaro — sigillato da PDI)', 'ja': '値（平文 — PDI が封印）', 'zh': '值（明文 — 由 PDI 封存）', 'hi': 'मान (सादा पाठ — PDI द्वारा सील)', 'ar': 'القيمة (نص صريح — يختمه PDI)'},
    'wants': {'en': 'Assistant capabilities', 'es': 'Capacidades del asistente', 'fr': 'Capacités de l’assistant', 'de': 'Fähigkeiten des Assistenten', 'pt': 'Capacidades do assistente', 'it': 'Capacità dell’assistente', 'ja': 'アシスタントの機能', 'zh': '助手能力', 'hi': 'सहायक की क्षमताएँ', 'ar': 'قدرات المساعد'},

}


def field_label(name: str, language: str) -> str:
    """The label a person sees beside this field, or its identifier."""
    row = _FIELD_LABELS.get(name)
    if not row:
        return name
    return row.get(language) or row.get(DEFAULT) or name


def validation_message(rows: list[dict], language: str) -> str:
    """One sentence, from rows a person was never going to read.

    `validation_detail` above puts pydantic's rows into the reader's language.
    Nine clients then rendered them: the three consoles printed the array as
    JSON, the three Android shells did the same by coercion, and the iOS and
    Windows shells asked for a string, got an array, and fell back to the
    status code. So a mistyped form said either `[{"type":"missing",...}]` or
    `HTTP 422`.

        asked     is the refusal translated
        mattered  is the refusal a sentence

    Composed here rather than in each client for the reason the refusal
    handler is one handler: nine renderings of one thing are nine chances to
    render it differently, and six of these are in languages with no test
    runner in this repository.

    ## What stays an identifier

    The field name is not translated and is not meant to read as a word. It is
    the API's name for the field — `display_name` — which is the same string in
    every language, and it is joined to the sentence with an em dash rather
    than declined into it, so nothing here is half in one language and half in
    another — the one thing `tests/refusals_untranslated.txt` will not record
    its way out of.

    Mapping those names to the labels a form actually shows — *"Nome de
    exibição"* rather than `display_name` — is a per-client table this does not
    have, and is recorded as the remaining gap rather than guessed at.

    Carries nothing `detail` does not: the same `loc` and the same already
    redacted `msg`, which is what `test_the_sentence_says_no_more_than_the_rows`
    holds it to.
    """
    parts = []
    for row in rows:
        where = [str(p) for p in row.get("loc", ())]
        if where and where[0] in _WHERE_MARKERS:
            where = where[1:]
        name = ".".join(tr_refusal(p, language) if p == UNRECOGNISED_FIELD
                        else field_label(p, language) for p in where)
        said = str(row.get("msg", ""))
        parts.append(f"{name} — {said}" if name else said)
    return "; ".join(p for p in parts if p)


#: Pydantic's own catalogue, for the messages this product's forms can
#: produce. Safe to pass through untranslated as well as translated: these
#: sentences interpolate limits, never the value that failed. Anything not
#: here falls through as English, which is a visible gap rather than a
#: confident error.
_VALIDATION: dict[str, dict[str, str]] = {
    # Not a message but a field name, and the one field name that is prose:
    # `validation_detail` substitutes it where a caller's own key would
    # otherwise be echoed, so it lands in the sentence `validation_message`
    # composes and has to be readable there.
    UNRECOGNISED_FIELD: {
        'es': '<campo no reconocido>',
        'fr': '<champ non reconnu>',
        'de': '<unbekanntes Feld>',
        'pt': '<campo não reconhecido>',
        'it': '<campo non riconosciuto>',
        'ja': '<認識できない項目>',
        'zh': '<无法识别的字段>',
        'hi': '<अपरिचित फ़ील्ड>',
        'ar': '<حقل غير معروف>',
    },
    UNSPECIFIED_VALUE_ERROR: {
        'es': 'ese valor no es aceptable aquí',
        'fr': "cette valeur n'est pas acceptable ici",
        'de': 'dieser Wert ist hier nicht zulässig',
        'pt': 'esse valor não é aceitável aqui',
        'it': 'questo valore non è accettabile qui',
        'ja': 'この値はここでは使えません',
        'zh': '此处不接受该值',
        'hi': 'यह मान यहाँ स्वीकार्य नहीं है',
        'ar': 'هذه القيمة غير مقبولة هنا',
    },
    'Field required': {
        'es': 'campo obligatorio',
        'fr': 'champ requis',
        'de': 'Pflichtfeld',
        'pt': 'campo obrigatório',
        'it': 'campo obbligatorio',
        'ja': '必須項目です',
        'zh': '此字段为必填项',
        'hi': 'यह फ़ील्ड आवश्यक है',
        'ar': 'حقل مطلوب',
    },
    'Extra inputs are not permitted': {
        'es': 'no se admiten campos adicionales',
        'fr': 'les champs supplémentaires ne sont pas autorisés',
        'de': 'zusätzliche Felder sind nicht zulässig',
        'pt': 'não são permitidos campos adicionais',
        'it': 'non sono ammessi campi aggiuntivi',
        'ja': '追加の項目は指定できません',
        'zh': '不允许提供额外字段',
        'hi': 'अतिरिक्त फ़ील्ड की अनुमति नहीं है',
        'ar': 'لا يُسمح بحقول إضافية',
    },
    'Input should be a valid string': {
        'es': 'debe ser una cadena de texto válida',
        'fr': 'doit être une chaîne de caractères valide',
        'de': 'muss eine gültige Zeichenkette sein',
        'pt': 'tem de ser uma cadeia de texto válida',
        'it': 'deve essere una stringa valida',
        'ja': '有効な文字列を指定してください',
        'zh': '应为有效的字符串',
        'hi': 'यह एक मान्य स्ट्रिंग होनी चाहिए',
        'ar': 'يجب أن تكون سلسلة نصية صالحة',
    },
    'Input should be a valid integer': {
        'es': 'debe ser un número entero válido',
        'fr': 'doit être un entier valide',
        'de': 'muss eine gültige ganze Zahl sein',
        'pt': 'tem de ser um número inteiro válido',
        'it': 'deve essere un numero intero valido',
        'ja': '有効な整数を指定してください',
        'zh': '应为有效的整数',
        'hi': 'यह एक मान्य पूर्णांक होना चाहिए',
        'ar': 'يجب أن يكون عددًا صحيحًا صالحًا',
    },
    'Input should be a valid number': {
        'es': 'debe ser un número válido',
        'fr': 'doit être un nombre valide',
        'de': 'muss eine gültige Zahl sein',
        'pt': 'tem de ser um número válido',
        'it': 'deve essere un numero valido',
        'ja': '有効な数値を指定してください',
        'zh': '应为有效的数字',
        'hi': 'यह एक मान्य संख्या होनी चाहिए',
        'ar': 'يجب أن يكون رقمًا صالحًا',
    },
    'Input should be a valid boolean': {
        'es': 'debe ser un valor booleano válido',
        'fr': 'doit être un booléen valide',
        'de': 'muss ein gültiger Wahrheitswert sein',
        'pt': 'tem de ser um valor booleano válido',
        'it': 'deve essere un valore booleano valido',
        'ja': '有効な真偽値を指定してください',
        'zh': '应为有效的布尔值',
        'hi': 'यह एक मान्य बूलियन मान होना चाहिए',
        'ar': 'يجب أن تكون قيمة منطقية صالحة',
    },
    'Input should be a valid list': {
        'es': 'debe ser una lista válida',
        'fr': 'doit être une liste valide',
        'de': 'muss eine gültige Liste sein',
        'pt': 'tem de ser uma lista válida',
        'it': 'deve essere un elenco valido',
        'ja': '有効なリストを指定してください',
        'zh': '应为有效的列表',
        'hi': 'यह एक मान्य सूची होनी चाहिए',
        'ar': 'يجب أن تكون قائمة صالحة',
    },
    'Input should be a valid dictionary': {
        'es': 'debe ser un objeto válido',
        'fr': 'doit être un objet valide',
        'de': 'muss ein gültiges Objekt sein',
        'pt': 'tem de ser um objeto válido',
        'it': 'deve essere un oggetto valido',
        'ja': '有効なオブジェクトを指定してください',
        'zh': '应为有效的对象',
        'hi': 'यह एक मान्य ऑब्जेक्ट होना चाहिए',
        'ar': 'يجب أن يكون كائنًا صالحًا',
    },
    'Input should be a valid date': {
        'es': 'debe ser una fecha válida',
        'fr': 'doit être une date valide',
        'de': 'muss ein gültiges Datum sein',
        'pt': 'tem de ser uma data válida',
        'it': 'deve essere una data valida',
        'ja': '有効な日付を指定してください',
        'zh': '应为有效的日期',
        'hi': 'यह एक मान्य दिनांक होनी चाहिए',
        'ar': 'يجب أن يكون تاريخًا صالحًا',
    },
}
