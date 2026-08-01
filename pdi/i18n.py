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
