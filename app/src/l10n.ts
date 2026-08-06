// Chrome localization for PDI's desktop console.
//
// The three native shells (native/ios/Sources/L10n.swift and siblings) have
// carried a ten-language table for many releases. This console had none, and
// nothing had ever counted what that cost — 0.48.1 measured it at 250 English
// strings across fourteen screens and wrote `pdi/tests/console_untranslated.txt`.
//
// The sharp part was never that the console was English. It is that
// `Guiding.tsx` renders a **language picker**: a tenant selects Spanish, the
// backend begins answering in Spanish, and the frame around those answers
// stayed English. The screen where you choose your language is the first one
// that has to read in it, which is why it is the first one wired here.
//
// Two deliberate choices, both of them answers to findings in the sibling
// products:
//
//   * **No formal/informal split.** 0.48.1 found QRME's console addressing a
//     German reader as *Sie* in 204 rows while its phones said *du* in 60 —
//     one product making two contradictory claims about the relationship.
//     These rows avoid the T–V distinction wherever a language allows it
//     (infinitives and nominal phrases rather than commands), so the question
//     does not arise and cannot drift.
//   * **Portuguese is pt-PT** — *ficheiro*, *Guardar* — matching the shells
//     and the rest of both siblings.
//
// Missing keys fall back to English so a gap shows words, never a blank.

export type Lang =
  | "en" | "es" | "fr" | "de" | "pt" | "it" | "ja" | "zh" | "hi" | "ar";

export const SUPPORTED: Lang[] = [
  "en", "es", "fr", "de", "pt", "it", "ja", "zh", "hi", "ar",
];

type Table = Record<string, Partial<Record<Lang, string>>>;

/** The language of somebody who has not chosen one yet.
 *
 * The shells read this from the device rather than defaulting to English —
 * `L10n.deviceLanguage` in each — because a stored setting starts empty and
 * the browser has been carrying the answer the whole time. Region is dropped
 * (`es-419` and `es-ES` are both `es`); anything unsupported falls back to
 * English rather than guessing. */
export function deviceLanguage(): Lang {
  const tags = typeof navigator === "undefined" ? [] : navigator.languages ?? [];
  for (const tag of tags) {
    const base = String(tag).split("-")[0].toLowerCase() as Lang;
    if (SUPPORTED.includes(base)) return base;
  }
  return "en";
}

const CHROME: Table = {
  "gd.title": {
    en: "Guiding", es: "Guía", fr: "Guidage", de: "Anleitung",
    pt: "Orientação", it: "Guida", ja: "案内", zh: "指引",
    hi: "मार्गदर्शन", ar: "الإرشاد",
  },
  "gd.sub": {
    en: "the console's guide, its corner, and its words",
    es: "la guía de la consola, su rincón y sus palabras",
    fr: "le guide de la console, son coin et ses mots",
    de: "der Leitfaden der Konsole, ihre Ecke und ihre Worte",
    pt: "o guia da consola, o seu canto e as suas palavras",
    it: "la guida della console, il suo angolo e le sue parole",
    ja: "コンソールの案内、その隅、その言葉",
    zh: "控制台的指引、它的角落和它的用词",
    hi: "कंसोल की गाइड, उसका कोना और उसके शब्द",
    ar: "دليل الوحدة، وركنها، وكلماتها",
  },
  "gd.guide": {
    en: "The guide", es: "La guía", fr: "Le guide", de: "Der Leitfaden",
    pt: "O guia", it: "La guida", ja: "案内", zh: "指引",
    hi: "गाइड", ar: "الدليل",
  },
  "gd.start": {
    en: "Start the walkthrough", es: "Empezar el recorrido",
    fr: "Commencer la visite", de: "Rundgang beginnen",
    pt: "Começar o percurso", it: "Iniziare il percorso",
    ja: "ひと通り始める", zh: "开始导览",
    hi: "परिचय शुरू करें", ar: "بدء الجولة",
  },
  "gd.step": {
    en: "Read a step", es: "Leer un paso", fr: "Lire une étape",
    de: "Einen Schritt lesen", pt: "Ler um passo", it: "Leggere un passo",
    ja: "ステップを読む", zh: "读一个步骤",
    hi: "एक चरण पढ़ें", ar: "قراءة خطوة",
  },
  "gd.thisscreen": {
    en: "What is this screen?", es: "¿Qué es esta pantalla?",
    fr: "Qu'est-ce que cet écran ?", de: "Was ist dieser Bildschirm?",
    pt: "O que é este ecrã?", it: "Che cos'è questa schermata?",
    ja: "この画面は何か", zh: "这是什么界面？",
    hi: "यह स्क्रीन क्या है?", ar: "ما هذه الشاشة؟",
  },
  "gd.done": {
    en: "Mark it done", es: "Marcarlo como hecho", fr: "Marquer comme fait",
    de: "Als erledigt markieren", pt: "Marcar como feito",
    it: "Segnare come fatto", ja: "完了にする", zh: "标记为完成",
    hi: "पूर्ण चिह्नित करें", ar: "وضع علامة الإتمام",
  },
  "gd.progress": {
    en: "{done} of {total} done", es: "{done} de {total} hechos",
    fr: "{done} sur {total} faits", de: "{done} von {total} erledigt",
    pt: "{done} de {total} feitos", it: "{done} di {total} fatti",
    ja: "{total} 件中 {done} 件完了", zh: "已完成 {done} / {total}",
    hi: "{total} में से {done} पूर्ण", ar: "{done} من {total} مكتملة",
  },
  "gd.steps": {
    en: "steps", es: "pasos", fr: "étapes", de: "Schritte", pt: "passos",
    it: "passi", ja: "ステップ", zh: "个步骤", hi: "चरण", ar: "خطوات",
  },
  "gd.ask.head": {
    en: "Ask it", es: "Preguntarle", fr: "Lui demander", de: "Nachfragen",
    pt: "Perguntar-lhe", it: "Chiedere", ja: "たずねる", zh: "问它",
    hi: "इससे पूछें", ar: "اسأله",
  },
  "gd.q": {
    en: "Question", es: "Pregunta", fr: "Question", de: "Frage",
    pt: "Pergunta", it: "Domanda", ja: "質問", zh: "问题",
    hi: "प्रश्न", ar: "السؤال",
  },
  "gd.q.ph": {
    en: "Where is the audit log?", es: "¿Dónde está el registro de auditoría?",
    fr: "Où est le journal d'audit ?", de: "Wo ist das Prüfprotokoll?",
    pt: "Onde está o registo de auditoria?", it: "Dov'è il registro di audit?",
    ja: "監査ログはどこか", zh: "审计日志在哪里？",
    hi: "ऑडिट लॉग कहाँ है?", ar: "أين سجل التدقيق؟",
  },
  "gd.ask.go": {
    en: "Ask", es: "Preguntar", fr: "Demander", de: "Fragen",
    pt: "Perguntar", it: "Chiedere", ja: "質問する", zh: "提问",
    hi: "पूछें", ar: "اسأل",
  },
  "gd.refused": {
    en: "Refused — and that is the answer, not a failure. It was asked something about what is inside the vault, which it cannot read.",
    es: "Rechazado — y esa es la respuesta, no un fallo. Se le preguntó algo sobre lo que hay dentro de la cámara, que no puede leer.",
    fr: "Refusé — et c'est la réponse, pas un échec. On lui a demandé quelque chose sur le contenu du coffre, qu'il ne peut pas lire.",
    de: "Abgelehnt — und das ist die Antwort, kein Fehler. Gefragt wurde nach dem Inhalt des Tresors, den es nicht lesen kann.",
    pt: "Recusado — e essa é a resposta, não uma falha. Foi-lhe perguntado algo sobre o que está dentro do cofre, que não consegue ler.",
    it: "Rifiutato — ed è la risposta, non un errore. Gli è stato chiesto qualcosa sul contenuto della cassaforte, che non può leggere.",
    ja: "拒否されました。これは失敗ではなく答えです。金庫の中身について尋ねられましたが、それは読めません。",
    zh: "已拒绝——这就是答案，不是故障。它被问到保险库里的内容，而那是它读不到的。",
    hi: "अस्वीकृत — और यही उत्तर है, विफलता नहीं। इससे तिजोरी के भीतर की बात पूछी गई, जिसे यह पढ़ नहीं सकता।",
    ar: "مرفوض — وهذا هو الجواب، لا خلل. سُئل عمّا بداخل الخزنة، وهو ما لا يستطيع قراءته.",
  },
  "gd.screens": {
    en: "screens", es: "pantallas", fr: "écrans", de: "Bildschirme",
    pt: "ecrãs", it: "schermate", ja: "画面", zh: "界面",
    hi: "स्क्रीन", ar: "الشاشات",
  },
  "gd.knows": {
    en: "It knows about:", es: "Sabe sobre:", fr: "Il connaît :",
    de: "Es kennt:", pt: "Sabe sobre:", it: "Conosce:",
    ja: "扱える話題：", zh: "它了解：", hi: "यह जानता है:", ar: "يعرف عن:",
  },
  "gd.corner": {
    en: "The corner", es: "El rincón", fr: "Le coin", de: "Die Ecke",
    pt: "O canto", it: "L'angolo", ja: "隅", zh: "角落",
    hi: "कोना", ar: "الركن",
  },
  "gd.showing": {
    en: "showing", es: "mostrando", fr: "affiche", de: "zeigt",
    pt: "a mostrar", it: "mostra", ja: "表示中", zh: "正在显示",
    hi: "दिखा रहा है", ar: "يعرض",
  },
  "gd.othercorner": {
    en: "Other corner", es: "El otro rincón", fr: "L'autre coin",
    de: "Andere Ecke", pt: "O outro canto", it: "L'altro angolo",
    ja: "反対の隅", zh: "另一个角落",
    hi: "दूसरा कोना", ar: "الركن الآخر",
  },
  "gd.tuck": {
    en: "Tuck it away", es: "Guardarlo", fr: "Le replier", de: "Einklappen",
    pt: "Recolher", it: "Richiuderlo", ja: "しまう", zh: "收起来",
    hi: "समेट दें", ar: "طيّه",
  },
  "gd.open": {
    en: "Open it", es: "Abrirlo", fr: "L'ouvrir", de: "Ausklappen",
    pt: "Abrir", it: "Aprirlo", ja: "開く", zh: "打开",
    hi: "खोलें", ar: "فتحه",
  },
  "gd.never": {
    en: "Never in the pane:", es: "Nunca en el panel:",
    fr: "Jamais dans le volet :", de: "Nie im Bereich:",
    pt: "Nunca no painel:", it: "Mai nel riquadro:",
    ja: "この枠に出ないもの：", zh: "从不出现在此面板：",
    hi: "पैनल में कभी नहीं:", ar: "لا يظهر في اللوحة أبدًا:",
  },
  "gd.words": {
    en: "Words", es: "Palabras", fr: "Mots", de: "Worte", pt: "Palavras",
    it: "Parole", ja: "言葉", zh: "用词", hi: "शब्द", ar: "الكلمات",
  },
  "gd.lang": {
    en: "Language", es: "Idioma", fr: "Langue", de: "Sprache",
    pt: "Idioma", it: "Lingua", ja: "言語", zh: "语言",
    hi: "भाषा", ar: "اللغة",
  },
  "gd.notes.en": {
    en: " (notes stay in English)", es: " (las notas siguen en inglés)",
    fr: " (les notes restent en anglais)", de: " (Notizen bleiben auf Englisch)",
    pt: " (as notas ficam em inglês)", it: " (le note restano in inglese)",
    ja: "（注記は英語のまま）", zh: "（注记仍为英文）",
    hi: " (टिप्पणियाँ अंग्रेज़ी में ही रहेंगी)", ar: " (تبقى الملاحظات بالإنجليزية)",
  },
  "gd.use": {
    en: "Use this", es: "Usar este", fr: "Utiliser celle-ci",
    de: "Diese verwenden", pt: "Usar este", it: "Usare questa",
    ja: "これを使う", zh: "使用这个",
    hi: "यही उपयोग करें", ar: "استخدام هذه",
  },
  "gd.now": {
    en: "now:", es: "ahora:", fr: "actuellement :", de: "jetzt:",
    pt: "agora:", it: "ora:", ja: "現在：", zh: "当前：",
    hi: "अभी:", ar: "الآن:",
  },
  "gd.text": {
    en: "Text", es: "Texto", fr: "Texte", de: "Text", pt: "Texto",
    it: "Testo", ja: "テキスト", zh: "文本", hi: "पाठ", ar: "النص",
  },
  "gd.text.ph": {
    en: "A note to translate", es: "Una nota para traducir",
    fr: "Une note à traduire", de: "Eine Notiz zum Übersetzen",
    pt: "Uma nota para traduzir", it: "Una nota da tradurre",
    ja: "翻訳する注記", zh: "要翻译的注记",
    hi: "अनुवाद के लिए एक टिप्पणी", ar: "ملاحظة للترجمة",
  },
  "gd.translate": {
    en: "Translate", es: "Traducir", fr: "Traduire", de: "Übersetzen",
    pt: "Traduzir", it: "Tradurre", ja: "翻訳する", zh: "翻译",
    hi: "अनुवाद करें", ar: "ترجمة",
  },
  "gd.engine": {
    en: "engine:", es: "motor:", fr: "moteur :", de: "Modul:",
    pt: "motor:", it: "motore:", ja: "エンジン：", zh: "引擎：",
    hi: "इंजन:", ar: "المحرّك:",
  },
  "gd.tell": {
    en: "Tell us about the console", es: "Cuéntanos sobre la consola",
    fr: "Parlez-nous de la console", de: "Rückmeldung zur Konsole",
    pt: "Fale-nos da consola", it: "Parlaci della console",
    ja: "コンソールについて教えてください", zh: "说说这个控制台",
    hi: "कंसोल के बारे में बताएँ", ar: "أخبرنا عن الوحدة",
  },
  "gd.idea.ph": {
    en: "What would make this better?", es: "¿Qué lo mejoraría?",
    fr: "Qu'est-ce qui l'améliorerait ?", de: "Was würde das verbessern?",
    pt: "O que o melhoraria?", it: "Cosa lo migliorerebbe?",
    ja: "どうすればもっと良くなるか", zh: "怎样会更好？",
    hi: "इसे बेहतर क्या बनाएगा?", ar: "ما الذي يجعل هذا أفضل؟",
  },
  "gd.send": {
    en: "Send it", es: "Enviarlo", fr: "L'envoyer", de: "Absenden",
    pt: "Enviar", it: "Inviarlo", ja: "送る", zh: "发送",
    hi: "भेजें", ar: "إرساله",
  },
  "gd.total": {
    en: "in all", es: "en total", fr: "au total", de: "insgesamt",
    pt: "no total", it: "in tutto", ja: "件（全体）", zh: "条（全部）",
    hi: "कुल में", ar: "في المجموع",
  },
  "gd.yours": {
    en: "of them yours", es: "de ellas tuyas", fr: "dont les vôtres",
    de: "davon von Ihnen", pt: "delas suas", it: "di queste tue",
    ja: "件（うち自分の分）", zh: "条是你的",
    hi: "इनमें आपकी", ar: "منها لك",
  },

  // --- Custody: the key, the hardware, the paperwork ------------------------
  //
  // Second screen wired, and the one this product exists for. Every sentence
  // here answers *who can read the file* — and three of them are checked by
  // name in `test_the_door_and_the_wire.py`, which now follows them into this
  // table rather than grepping the screen for the English.
  "cu.title": {
    en: "Custody", es: "Custodia", fr: "Garde", de: "Verwahrung",
    pt: "Custódia", it: "Custodia", ja: "保管", zh: "保管",
    hi: "अभिरक्षा", ar: "الحيازة",
  },
  "cu.sub": {
    en: "the key, the hardware, the paperwork",
    es: "la clave, el hardware, los papeles",
    fr: "la clé, le matériel, les papiers",
    de: "der Schlüssel, die Hardware, die Papiere",
    pt: "a chave, o equipamento, os papéis",
    it: "la chiave, l'hardware, le carte",
    ja: "鍵、機器、書類", zh: "密钥、硬件、文书",
    hi: "कुंजी, हार्डवेयर, कागज़ात", ar: "المفتاح والعتاد والأوراق",
  },
  "cu.decrypt": {
    en: "Can the operator decrypt this?",
    es: "¿Puede el operador descifrar esto?",
    fr: "L'opérateur peut-il déchiffrer ceci ?",
    de: "Kann der Betreiber dies entschlüsseln?",
    pt: "O operador consegue decifrar isto?",
    it: "L'operatore può decifrare questo?",
    ja: "運営者はこれを復号できるか", zh: "运营方能解密它吗？",
    hi: "क्या संचालक इसे डिक्रिप्ट कर सकता है?",
    ar: "هل يستطيع المشغّل فكّ تشفير هذا؟",
  },
  "cu.yes": {
    en: "Yes", es: "Sí", fr: "Oui", de: "Ja", pt: "Sim", it: "Sì",
    ja: "はい", zh: "能", hi: "हाँ", ar: "نعم",
  },
  "cu.no": {
    en: "No", es: "No", fr: "Non", de: "Nein", pt: "Não", it: "No",
    ja: "いいえ", zh: "不能", hi: "नहीं", ar: "لا",
  },
  "cu.provider": {
    en: "provider", es: "proveedor", fr: "fournisseur", de: "Anbieter",
    pt: "fornecedor", it: "fornitore", ja: "提供元", zh: "提供方",
    hi: "प्रदाता", ar: "المزوّد",
  },
  "cu.customer_managed": {
    en: "customer-managed", es: "gestionada por el cliente",
    fr: "gérée par le client", de: "kundenverwaltet",
    pt: "gerida pelo cliente", it: "gestita dal cliente",
    ja: "顧客管理", zh: "由客户掌管",
    hi: "ग्राहक-प्रबंधित", ar: "بإدارة العميل",
  },
  "cu.deployment": {
    en: "under deployment custody", es: "bajo custodia del despliegue",
    fr: "sous la garde du déploiement", de: "in Obhut der Installation",
    pt: "sob custódia da instalação", it: "in custodia dell'installazione",
    ja: "配備側の保管下", zh: "由部署方保管",
    hi: "परिनियोजन की अभिरक्षा में", ar: "في عهدة النشر",
  },
  "cu.key.ph": {
    en: "base64 32-byte key", es: "clave de 32 bytes en base64",
    fr: "clé de 32 octets en base64", de: "32-Byte-Schlüssel in Base64",
    pt: "chave de 32 bytes em base64", it: "chiave da 32 byte in base64",
    ja: "base64 の 32 バイト鍵", zh: "base64 编码的 32 字节密钥",
    hi: "base64 में 32-बाइट कुंजी", ar: "مفتاح 32 بايت بترميز base64",
  },
  "cu.hold": {
    en: "Hold our own key", es: "Guardar nuestra propia clave",
    fr: "Détenir notre propre clé", de: "Eigenen Schlüssel halten",
    pt: "Guardar a nossa própria chave", it: "Tenere la nostra chiave",
    ja: "自分たちの鍵を持つ", zh: "自己保管密钥",
    hi: "अपनी कुंजी स्वयं रखें", ar: "الاحتفاظ بمفتاحنا",
  },
  "cu.kms": {
    en: "Use a KMS", es: "Usar un KMS", fr: "Utiliser un KMS",
    de: "Ein KMS verwenden", pt: "Usar um KMS", it: "Usare un KMS",
    ja: "KMS を使う", zh: "使用 KMS", hi: "KMS का उपयोग करें",
    ar: "استخدام KMS",
  },
  "cu.handback": {
    en: "Hand it back", es: "Devolverla", fr: "La rendre",
    de: "Zurückgeben", pt: "Devolvê-la", it: "Restituirla",
    ja: "返す", zh: "交还", hi: "वापस सौंपें", ar: "إعادته",
  },
  "cu.versions": {
    en: "Key versions", es: "Versiones de la clave",
    fr: "Versions de la clé", de: "Schlüsselversionen",
    pt: "Versões da chave", it: "Versioni della chiave",
    ja: "鍵のバージョン", zh: "密钥版本",
    hi: "कुंजी संस्करण", ar: "إصدارات المفتاح",
  },
  "cu.reseal": {
    en: "Reseal under the active key",
    es: "Volver a sellar con la clave activa",
    fr: "Resceller avec la clé active",
    de: "Mit dem aktiven Schlüssel neu versiegeln",
    pt: "Voltar a selar com a chave ativa",
    it: "Risigillare con la chiave attiva",
    ja: "有効な鍵で封印し直す", zh: "用当前密钥重新封存",
    hi: "सक्रिय कुंजी से फिर सील करें",
    ar: "إعادة الختم بالمفتاح النشط",
  },
  "cu.retire": {
    en: "Retire the old ones", es: "Retirar las antiguas",
    fr: "Retirer les anciennes", de: "Die alten ausmustern",
    pt: "Retirar as antigas", it: "Ritirare le vecchie",
    ja: "古い鍵を廃止する", zh: "停用旧密钥",
    hi: "पुरानी हटाएँ", ar: "إحالة القديمة للتقاعد",
  },
  "cu.active": {
    en: "active", es: "activa", fr: "active", de: "aktiv", pt: "ativa",
    it: "attiva", ja: "有効", zh: "当前使用", hi: "सक्रिय", ar: "نشط",
  },
  "cu.reseal.note": {
    en: "A reseal skips every record the customer holds the key for, and reports how many. That number is the honest measure of bring-your-own-key: it is how much of the vault the operator could not touch even when asked to.",
    es: "Un resellado omite cada registro cuya clave tiene el cliente, e informa cuántos son. Esa cifra es la medida honesta de traer tu propia clave: es cuánto de la cámara el operador no pudo tocar ni cuando se lo pidieron.",
    fr: "Un rescellement saute chaque enregistrement dont le client détient la clé, et indique combien. Ce nombre est la mesure honnête d'apporter sa propre clé : c'est la part du coffre que l'opérateur n'a pas pu toucher, même sur demande.",
    de: "Ein Neuversiegeln überspringt jeden Datensatz, dessen Schlüssel der Kunde hält, und meldet wie viele. Diese Zahl ist das ehrliche Maß für den eigenen Schlüssel: sie sagt, wie viel des Tresors der Betreiber nicht anrühren konnte, selbst auf Aufforderung.",
    pt: "Voltar a selar salta todos os registos cuja chave o cliente detém, e diz quantos. Esse número é a medida honesta de trazer a própria chave: é quanto do cofre o operador não conseguiu tocar, mesmo quando lho pediram.",
    it: "Risigillare salta ogni record di cui il cliente detiene la chiave, e riporta quanti. Quel numero è la misura onesta della chiave propria: è quanta parte della cassaforte l'operatore non ha potuto toccare, nemmeno su richiesta.",
    ja: "封印し直す処理は、顧客が鍵を持つレコードをすべて飛ばし、その件数を報告します。この数字こそが「自分の鍵を持ち込む」ことの正直な指標です。求められてもなお運営者が触れられなかった量を示します。",
    zh: "重新封存会跳过每一条由客户掌管密钥的记录，并报告跳过了多少条。这个数字才是「自带密钥」的诚实度量：它说明即便被要求，运营方也有多少内容无法触及。",
    hi: "पुनः सील करना हर उस रिकॉर्ड को छोड़ देता है जिसकी कुंजी ग्राहक के पास है, और बताता है कि कितने छोड़े गए। वही संख्या अपनी कुंजी लाने का ईमानदार माप है: यह बताती है कि माँगे जाने पर भी संचालक तिजोरी का कितना हिस्सा छू नहीं सका।",
    ar: "تتخطّى إعادة الختم كل سجلّ يحتفظ العميل بمفتاحه، وتُبلغ بعددها. هذا الرقم هو القياس الصادق لإحضار مفتاحك: إنه مقدار ما لم يستطع المشغّل لمسه من الخزنة حتى حين طُلب منه ذلك.",
  },
  "cu.away": {
    en: "Take it away, and put it back", es: "Llevárselo y devolverlo",
    fr: "L'emporter, et le remettre", de: "Wegnehmen und zurücklegen",
    pt: "Levá-lo e devolvê-lo", it: "Portarlo via e rimetterlo",
    ja: "持ち出して、戻す", zh: "取走，再放回",
    hi: "ले जाएँ, और वापस रखें", ar: "أخذه ثم إعادته",
  },
  "cu.snapshot": {
    en: "Snapshot", es: "Instantánea", fr: "Instantané",
    de: "Momentaufnahme", pt: "Instantâneo", it: "Istantanea",
    ja: "スナップショット", zh: "快照", hi: "स्नैपशॉट", ar: "لقطة",
  },
  "cu.restore": {
    en: "Restore from the snapshot", es: "Restaurar desde la instantánea",
    fr: "Restaurer depuis l'instantané",
    de: "Aus der Momentaufnahme wiederherstellen",
    pt: "Restaurar a partir do instantâneo",
    it: "Ripristinare dall'istantanea",
    ja: "スナップショットから復元する", zh: "从快照恢复",
    hi: "स्नैपशॉट से पुनर्स्थापित करें", ar: "الاستعادة من اللقطة",
  },
  "cu.restore.all": {
    en: "Restore the whole tenant", es: "Restaurar todo el inquilino",
    fr: "Restaurer tout le locataire", de: "Den ganzen Mandanten wiederherstellen",
    pt: "Restaurar todo o inquilino", it: "Ripristinare l'intero tenant",
    ja: "テナント全体を復元する", zh: "恢复整个租户",
    hi: "पूरा टेनेंट पुनर्स्थापित करें", ar: "استعادة المستأجر بالكامل",
  },
  "cu.delrec": {
    en: "Delete a record", es: "Borrar un registro",
    fr: "Supprimer un enregistrement", de: "Einen Datensatz löschen",
    pt: "Eliminar um registo", it: "Eliminare un record",
    ja: "レコードを削除する", zh: "删除一条记录",
    hi: "एक रिकॉर्ड मिटाएँ", ar: "حذف سجلّ",
  },
  "cu.delrec.ph": {
    en: "a record key", es: "una clave de registro",
    fr: "une clé d'enregistrement", de: "ein Datensatzschlüssel",
    pt: "uma chave de registo", it: "una chiave di record",
    ja: "レコードのキー", zh: "记录键",
    hi: "एक रिकॉर्ड कुंजी", ar: "مفتاح سجلّ",
  },
  "cu.deltenant": {
    en: "Delete the tenant", es: "Borrar el inquilino",
    fr: "Supprimer le locataire", de: "Den Mandanten löschen",
    pt: "Eliminar o inquilino", it: "Eliminare il tenant",
    ja: "テナントを削除する", zh: "删除该租户",
    hi: "टेनेंट मिटाएँ", ar: "حذف المستأجر",
  },
  "cu.audit.note": {
    en: "The audit trail survives every one of these. A deletion is an entry in the chain, not a gap in it — a vault that could erase the record of erasing something would not be evidence of anything.",
    es: "El rastro de auditoría sobrevive a todas estas acciones. Un borrado es una entrada en la cadena, no un hueco en ella: una cámara capaz de borrar el registro de haber borrado algo no sería prueba de nada.",
    fr: "La piste d'audit survit à chacune de ces actions. Une suppression est une entrée dans la chaîne, non un trou : un coffre capable d'effacer la trace d'un effacement ne prouverait rien.",
    de: "Das Prüfprotokoll überlebt jede dieser Aktionen. Eine Löschung ist ein Eintrag in der Kette, keine Lücke darin — ein Tresor, der den Nachweis einer Löschung löschen könnte, wäre kein Beweis für irgendetwas.",
    pt: "O registo de auditoria sobrevive a todas estas ações. Uma eliminação é uma entrada na cadeia, não uma falha nela — um cofre capaz de apagar o registo de ter apagado algo não seria prova de nada.",
    it: "La traccia di audit sopravvive a ognuna di queste azioni. Una cancellazione è una voce nella catena, non un vuoto — una cassaforte capace di cancellare la traccia di una cancellazione non proverebbe nulla.",
    ja: "監査証跡はこれらのどの操作にも残ります。削除は鎖の中の記載であって、鎖の欠落ではありません。何かを消した記録そのものを消せる金庫は、何の証拠にもなりません。",
    zh: "审计链在这些操作之后依然完整。删除是链条上的一条记录，而不是链条上的缺口——一个能抹掉「抹掉过什么」的保险库，无法证明任何事。",
    hi: "इनमें से हर कार्रवाई के बाद भी ऑडिट शृंखला बनी रहती है। मिटाना शृंखला में एक प्रविष्टि है, उसमें छेद नहीं — जो तिजोरी कुछ मिटाने का रिकॉर्ड ही मिटा सके, वह किसी बात का प्रमाण नहीं होगी।",
    ar: "يبقى سجل التدقيق بعد كل واحدة من هذه العمليات. الحذف قيدٌ في السلسلة لا ثغرة فيها — وخزنةٌ تستطيع محو سجلّ المحو لا تصلح دليلًا على شيء.",
  },
  "cu.tokens": {
    en: "Tokens", es: "Tokens", fr: "Jetons", de: "Token", pt: "Tokens",
    it: "Token", ja: "トークン", zh: "令牌", hi: "टोकन", ar: "الرموز",
  },
  "cu.mint.read": {
    en: "Mint a read token", es: "Emitir un token de lectura",
    fr: "Émettre un jeton de lecture", de: "Ein Lese-Token ausstellen",
    pt: "Emitir um token de leitura", it: "Emettere un token di lettura",
    ja: "読み取りトークンを発行", zh: "签发读取令牌",
    hi: "पठन टोकन जारी करें", ar: "إصدار رمز قراءة",
  },
  "cu.mint.write": {
    en: "Mint a write token", es: "Emitir un token de escritura",
    fr: "Émettre un jeton d'écriture", de: "Ein Schreib-Token ausstellen",
    pt: "Emitir um token de escrita", it: "Emettere un token di scrittura",
    ja: "書き込みトークンを発行", zh: "签发写入令牌",
    hi: "लेखन टोकन जारी करें", ar: "إصدار رمز كتابة",
  },
  "cu.revoke": {
    en: "Revoke it", es: "Revocarlo", fr: "Le révoquer", de: "Widerrufen",
    pt: "Revogá-lo", it: "Revocarlo", ja: "取り消す", zh: "撤销",
    hi: "रद्द करें", ar: "إبطاله",
  },
  "cu.revoked": {
    en: "Revoked.", es: "Revocado.", fr: "Révoqué.", de: "Widerrufen.",
    pt: "Revogado.", it: "Revocato.", ja: "取り消しました。", zh: "已撤销。",
    hi: "रद्द कर दिया गया।", ar: "أُبطِل.",
  },
  "cu.minted.note": {
    en: "— shown once. Only its SHA-256 is stored, so nothing here or anywhere else can show it to you again.",
    es: "— se muestra una sola vez. Solo se guarda su SHA-256, así que nada aquí ni en ningún otro sitio puede volver a mostrártelo.",
    fr: "— affiché une seule fois. Seul son SHA-256 est conservé, donc rien ici ni ailleurs ne peut vous le remontrer.",
    de: "— einmalig angezeigt. Gespeichert wird nur sein SHA-256, sodass es weder hier noch anderswo erneut gezeigt werden kann.",
    pt: "— mostrado uma só vez. Apenas o seu SHA-256 é guardado, por isso nada aqui nem em lado nenhum o pode voltar a mostrar.",
    it: "— mostrato una sola volta. Ne è conservato solo lo SHA-256, quindi né qui né altrove può essere mostrato di nuovo.",
    ja: "— 表示は一度きりです。保存されるのは SHA-256 だけなので、ここでも他のどこでも再表示はできません。",
    zh: "— 只显示这一次。系统只保存它的 SHA-256，因此这里和任何别处都无法再向你显示它。",
    hi: "— केवल एक बार दिखाया जाता है। इसका केवल SHA-256 संग्रहीत होता है, इसलिए न यहाँ न कहीं और इसे दोबारा दिखाया जा सकता है।",
    ar: "— يُعرض مرة واحدة. لا يُخزَّن منه سوى SHA-256، فلا شيء هنا ولا في أي مكان آخر يستطيع عرضه عليك ثانية.",
  },
  "cu.paperwork": {
    en: "The paperwork", es: "Los papeles", fr: "Les papiers",
    de: "Die Papiere", pt: "Os papéis", it: "Le carte",
    ja: "書類", zh: "文书", hi: "कागज़ात", ar: "الأوراق",
  },
  "cu.cust.name": {
    en: "Customer legal name", es: "Razón social del cliente",
    fr: "Raison sociale du client", de: "Rechtlicher Name des Kunden",
    pt: "Denominação legal do cliente", it: "Ragione sociale del cliente",
    ja: "顧客の法人名", zh: "客户法定名称",
    hi: "ग्राहक का कानूनी नाम", ar: "الاسم القانوني للعميل",
  },
  "cu.op.name": {
    en: "Operator legal name", es: "Razón social del operador",
    fr: "Raison sociale de l'opérateur", de: "Rechtlicher Name des Betreibers",
    pt: "Denominação legal do operador", it: "Ragione sociale dell'operatore",
    ja: "運営者の法人名", zh: "运营方法定名称",
    hi: "संचालक का कानूनी नाम", ar: "الاسم القانوني للمشغّل",
  },
  "cu.eff": {
    en: "Effective date", es: "Fecha de entrada en vigor",
    fr: "Date d'entrée en vigueur", de: "Datum des Inkrafttretens",
    pt: "Data de entrada em vigor", it: "Data di decorrenza",
    ja: "発効日", zh: "生效日期", hi: "प्रभावी तिथि", ar: "تاريخ السريان",
  },
  "cu.record": {
    en: "Record it", es: "Registrarlo", fr: "L'enregistrer",
    de: "Festhalten", pt: "Registá-lo", it: "Registrarlo",
    ja: "記録する", zh: "记录下来", hi: "दर्ज करें", ar: "تسجيله",
  },
  "cu.rescind": {
    en: "Rescind", es: "Rescindir", fr: "Résilier", de: "Aufheben",
    pt: "Rescindir", it: "Rescindere", ja: "解除する", zh: "解除",
    hi: "निरस्त करें", ar: "فسخ",
  },
  "cu.onfile": {
    en: "On file for this tenant:", es: "En archivo para este inquilino:",
    fr: "Au dossier pour ce locataire :", de: "Für diesen Mandanten hinterlegt:",
    pt: "Em arquivo para este inquilino:", it: "Agli atti per questo tenant:",
    ja: "このテナントの記録：", zh: "该租户存档：",
    hi: "इस टेनेंट के लिए दर्ज:", ar: "المحفوظ لهذا المستأجر:",
  },
  "cu.programs": {
    en: "Programs", es: "Programas", fr: "Programmes", de: "Programme",
    pt: "Programas", it: "Programmi", ja: "プログラム", zh: "合规方案",
    hi: "कार्यक्रम", ar: "البرامج",
  },
  "cu.retention": {
    en: "retention {n} days", es: "retención {n} días",
    fr: "conservation {n} jours", de: "Aufbewahrung {n} Tage",
    pt: "retenção {n} dias", it: "conservazione {n} giorni",
    ja: "保持 {n} 日", zh: "保留 {n} 天",
    hi: "प्रतिधारण {n} दिन", ar: "الاحتفاظ {n} يومًا",
  },
  "cu.where": {
    en: "Where it physically is", es: "Dónde está físicamente",
    fr: "Où il se trouve physiquement", de: "Wo es physisch steht",
    pt: "Onde está fisicamente", it: "Dove si trova fisicamente",
    ja: "物理的にどこにあるか", zh: "它实际在哪里",
    hi: "यह भौतिक रूप से कहाँ है", ar: "أين يوجد فعليًا",
  },
  "cu.deploy": {
    en: "Record a deployment", es: "Registrar un despliegue",
    fr: "Enregistrer un déploiement", de: "Eine Installation festhalten",
    pt: "Registar uma instalação", it: "Registrare un'installazione",
    ja: "配備を記録する", zh: "记录一次部署",
    hi: "एक परिनियोजन दर्ज करें", ar: "تسجيل عملية نشر",
  },

  // --- Continuity: what happens to a sealed file after a death -------------
  //
  // Third screen wired. Two of its sentences are checked by name in
  // `test_the_door_and_the_wire.py` — the one distinguishing revoking a grant
  // from revoking a bequest, and the one distinguishing *nothing paged* from
  // *nothing could have been paged*. Both are distinctions somebody acts on.
  "co.signin": {
    en: "Paste a tenant token to sign in.",
    es: "Pega un token de inquilino para entrar.",
    fr: "Collez un jeton de locataire pour vous connecter.",
    de: "Fügen Sie ein Mandanten-Token ein, um sich anzumelden.",
    pt: "Cole um token de inquilino para entrar.",
    it: "Incolla un token del tenant per accedere.",
    ja: "テナントトークンを貼り付けてサインインします。",
    zh: "粘贴租户令牌以登录。",
    hi: "साइन इन करने हेतु टेनेंट टोकन चिपकाएँ।",
    ar: "الصق رمز المستأجر لتسجيل الدخول.",
  },
  "co.title": {
    en: "Continuity & gateway", es: "Continuidad y pasarela",
    fr: "Continuité et passerelle", de: "Fortbestand und Gateway",
    pt: "Continuidade e gateway", it: "Continuità e gateway",
    ja: "継続とゲートウェイ", zh: "延续与网关",
    hi: "निरंतरता और गेटवे", ar: "الاستمرارية والبوابة",
  },
  "co.bequests": {
    en: "Bequests", es: "Legados", fr: "Legs", de: "Vermächtnisse",
    pt: "Legados", it: "Lasciti", ja: "遺贈", zh: "遗赠",
    hi: "वसीयतें", ar: "الوصايا",
  },
  "co.bequests.note": {
    en: "A standing instruction, dormant when written. Creating one grants nothing — it records what would become readable, by whom, if the condition were ever attested by an operator holding a different credential.",
    es: "Una instrucción permanente, latente en el momento de escribirla. Crearla no concede nada: deja constancia de qué pasaría a ser legible, y por quién, si algún día un operador con otra credencial diera fe de la condición.",
    fr: "Une instruction permanente, dormante à l'écriture. En créer une n'accorde rien : elle consigne ce qui deviendrait lisible, et par qui, si la condition était un jour attestée par un opérateur détenant un autre identifiant.",
    de: "Eine dauerhafte Anweisung, beim Verfassen ruhend. Sie zu erstellen gewährt nichts — sie hält fest, was lesbar würde und für wen, falls die Bedingung je von einem Betreiber mit anderem Berechtigungsnachweis bezeugt würde.",
    pt: "Uma instrução permanente, adormecida quando é escrita. Criá-la não concede nada — regista o que passaria a ser legível, e por quem, se a condição alguma vez fosse atestada por um operador com outra credencial.",
    it: "Un'istruzione permanente, dormiente quando viene scritta. Crearla non concede nulla: registra cosa diventerebbe leggibile, e da chi, se la condizione fosse mai attestata da un operatore con una credenziale diversa.",
    ja: "書いた時点では休眠している常設の指示です。作成しても何も付与されません。別の資格情報を持つ運営者がその条件を証明した場合に、何が誰にとって読めるようになるかを記録するだけです。",
    zh: "一条长期指令，写下时处于休眠状态。创建它并不授予任何权限——它记录的是：若将来由持有另一份凭据的运营方证实了该条件，什么会变得可读、由谁可读。",
    hi: "एक स्थायी निर्देश, लिखे जाने के समय निष्क्रिय। इसे बनाने से कुछ भी प्रदान नहीं होता — यह दर्ज करता है कि यदि कभी किसी भिन्न प्रमाण-पत्र वाले संचालक ने शर्त प्रमाणित की, तो क्या और किसके लिए पठनीय हो जाएगा।",
    ar: "تعليمة دائمة، خاملة وقت كتابتها. إنشاؤها لا يمنح شيئًا — بل يسجّل ما الذي سيصبح مقروءًا، ولمن، لو شهد بتحقّق الشرط يومًا مشغّلٌ يحمل اعتمادًا مختلفًا.",
  },
  "co.nothing": {
    en: "Nothing bequeathed.", es: "Nada legado.", fr: "Rien de légué.",
    de: "Nichts vermacht.", pt: "Nada legado.", it: "Nessun lascito.",
    ja: "遺贈はありません。", zh: "尚无遗赠。",
    hi: "कुछ वसीयत नहीं किया गया।", ar: "لا وصايا.",
  },
  "co.inforce": {
    en: "in force", es: "en vigor", fr: "en vigueur", de: "in Kraft",
    pt: "em vigor", it: "in vigore", ja: "有効", zh: "已生效",
    hi: "प्रभावी", ar: "نافذة",
  },
  "co.dormant": {
    en: "dormant", es: "latente", fr: "dormant", de: "ruhend",
    pt: "adormecido", it: "dormiente", ja: "休眠中", zh: "休眠",
    hi: "निष्क्रिय", ar: "خاملة",
  },
  "co.wouldopen": {
    en: "Would open:", es: "Abriría:", fr: "Ouvrirait :", de: "Würde öffnen:",
    pt: "Abriria:", it: "Aprirebbe:", ja: "開く対象：", zh: "将可打开：",
    hi: "खुलेगा:", ar: "سيفتح:",
  },
  "co.record": {
    en: "Record a bequest", es: "Registrar un legado",
    fr: "Enregistrer un legs", de: "Ein Vermächtnis festhalten",
    pt: "Registar um legado", it: "Registrare un lascito",
    ja: "遺贈を記録する", zh: "记录一份遗赠",
    hi: "एक वसीयत दर्ज करें", ar: "تسجيل وصية",
  },
  "co.grantee.ph": {
    en: "Who inherits the read", es: "Quién hereda la lectura",
    fr: "Qui hérite de la lecture", de: "Wer das Leserecht erbt",
    pt: "Quem herda a leitura", it: "Chi eredita la lettura",
    ja: "読む権利を継ぐ人", zh: "由谁继承读取权",
    hi: "पठन का उत्तराधिकारी कौन", ar: "من يرث حق القراءة",
  },
  "co.prefixes.ph": {
    en: "Key prefixes, comma separated",
    es: "Prefijos de clave, separados por comas",
    fr: "Préfixes de clé, séparés par des virgules",
    de: "Schlüsselpräfixe, durch Komma getrennt",
    pt: "Prefixos de chave, separados por vírgulas",
    it: "Prefissi di chiave, separati da virgole",
    ja: "キーの接頭辞（カンマ区切り）", zh: "键前缀，用逗号分隔",
    hi: "कुंजी उपसर्ग, अल्पविराम से अलग",
    ar: "بادئات المفاتيح، مفصولة بفواصل",
  },
  "co.note.ph": {
    en: "Note (optional)", es: "Nota (opcional)", fr: "Note (facultative)",
    de: "Notiz (optional)", pt: "Nota (opcional)", it: "Nota (facoltativa)",
    ja: "メモ（任意）", zh: "备注（可选）",
    hi: "टिप्पणी (वैकल्पिक)", ar: "ملاحظة (اختيارية)",
  },
  "co.activation": {
    en: "Activation — the operator's act",
    es: "Activación — el acto del operador",
    fr: "Activation — l'acte de l'opérateur",
    de: "Aktivierung — die Handlung des Betreibers",
    pt: "Ativação — o ato do operador",
    it: "Attivazione — l'atto dell'operatore",
    ja: "発動 — 運営者の行為", zh: "启用——运营方的行为",
    hi: "सक्रियण — संचालक का कार्य", ar: "التفعيل — فِعل المشغّل",
  },
  "co.activation.note": {
    en: "Activation needs an admin token, not this tenant's. That separation is the point: the person who wrote the bequest cannot also be the one who declares its condition met. The reference given here goes into the audit chain, and the grant token is shown once.",
    es: "La activación requiere un token de administrador, no el de este inquilino. Esa separación es el objetivo: quien escribió el legado no puede ser también quien declare cumplida su condición. La referencia dada aquí entra en la cadena de auditoría, y el token de concesión se muestra una sola vez.",
    fr: "L'activation exige un jeton d'administration, pas celui de ce locataire. Cette séparation est le but : la personne qui a rédigé le legs ne peut pas être aussi celle qui déclare sa condition remplie. La référence donnée ici entre dans la chaîne d'audit, et le jeton d'octroi n'est affiché qu'une fois.",
    de: "Die Aktivierung verlangt ein Admin-Token, nicht das dieses Mandanten. Genau diese Trennung ist der Zweck: wer das Vermächtnis verfasst hat, kann nicht zugleich dessen Bedingung für erfüllt erklären. Der hier angegebene Beleg geht in die Prüfkette, und das Gewährungs-Token wird einmal angezeigt.",
    pt: "A ativação exige um token de administração, não o deste inquilino. Essa separação é o objetivo: quem escreveu o legado não pode ser também quem declara cumprida a sua condição. A referência aqui dada entra na cadeia de auditoria, e o token de concessão é mostrado uma só vez.",
    it: "L'attivazione richiede un token di amministrazione, non quello di questo tenant. Quella separazione è il punto: chi ha scritto il lascito non può essere anche chi ne dichiara soddisfatta la condizione. Il riferimento indicato qui entra nella catena di audit, e il token di concessione è mostrato una sola volta.",
    ja: "発動にはこのテナントのものではなく管理者トークンが必要です。その分離こそが要点で、遺贈を書いた本人がその条件の成立を宣言する者を兼ねることはできません。ここで示す典拠は監査の連鎖に入り、付与トークンは一度だけ表示されます。",
    zh: "启用需要管理员令牌，而不是该租户的令牌。这一分离正是要点：写下遗赠的人不能同时是宣告其条件已成立的人。此处填写的凭据会进入审计链，而授予令牌只显示一次。",
    hi: "सक्रियण के लिए इस टेनेंट का नहीं, बल्कि व्यवस्थापक टोकन चाहिए। यही पृथक्करण मूल बात है: जिसने वसीयत लिखी, वही उसकी शर्त पूरी होने की घोषणा नहीं कर सकता। यहाँ दिया गया संदर्भ ऑडिट शृंखला में जाता है, और अनुदान टोकन एक ही बार दिखाया जाता है।",
    ar: "يحتاج التفعيل إلى رمز إداري، لا إلى رمز هذا المستأجر. هذا الفصل هو المقصود: من كتب الوصية لا يصح أن يكون هو نفسه من يعلن تحقّق شرطها. والمرجع المُدخل هنا يدخل سلسلة التدقيق، ويُعرض رمز المنح مرة واحدة.",
  },
  "co.admin.ph": {
    en: "Admin token", es: "Token de administrador",
    fr: "Jeton d'administration", de: "Admin-Token",
    pt: "Token de administrador", it: "Token di amministrazione",
    ja: "管理者トークン", zh: "管理员令牌",
    hi: "एडमिन टोकन", ar: "رمز المشرف",
  },
  "co.admin.session.ph": {
    en: "Admin token (from your session)",
    es: "Token de administrador (de tu sesión)",
    fr: "Jeton d'administration (de votre session)",
    de: "Admin-Token (aus Ihrer Sitzung)",
    pt: "Token de administração (da sua sessão)",
    it: "Token di amministrazione (dalla tua sessione)",
    ja: "管理者トークン（現在のセッションから）",
    zh: "管理员令牌（来自你的会话）",
    hi: "व्यवस्थापक टोकन (आपके सत्र से)",
    ar: "رمز إداري (من جلستك)",
  },
  "co.ref.ph": {
    en: "What attests the condition", es: "Qué da fe de la condición",
    fr: "Ce qui atteste la condition", de: "Was die Bedingung bezeugt",
    pt: "O que atesta a condição", it: "Cosa attesta la condizione",
    ja: "条件を証明するもの", zh: "以何证实该条件",
    hi: "शर्त को क्या प्रमाणित करता है", ar: "ما الذي يشهد بالشرط",
  },
  "co.activate": {
    en: "Activate", es: "Activar", fr: "Activer", de: "Aktivieren",
    pt: "Ativar", it: "Attivare", ja: "発動する", zh: "启用",
    hi: "सक्रिय करें", ar: "تفعيل",
  },
  "co.activated": {
    en: "Activated.", es: "Activado.", fr: "Activé.", de: "Aktiviert.",
    pt: "Ativado.", it: "Attivato.", ja: "発動しました。", zh: "已启用。",
    hi: "सक्रिय कर दिया गया।", ar: "فُعِّلت.",
  },
  "co.minted": {
    en: "Grant token — copy it now.", es: "Token de concesión — cópialo ahora.",
    fr: "Jeton d'octroi — copiez-le maintenant.",
    de: "Gewährungs-Token — jetzt kopieren.",
    pt: "Token de concessão — copie-o agora.",
    it: "Token di concessione — copialo ora.",
    ja: "付与トークン — いま控えてください。", zh: "授予令牌——请立即复制。",
    hi: "अनुदान टोकन — अभी कॉपी करें।", ar: "رمز المنح — انسخه الآن.",
  },
  "co.minted.note": {
    en: "It is not stored and will not be shown again.",
    es: "No se guarda y no volverá a mostrarse.",
    fr: "Il n'est pas conservé et ne sera plus affiché.",
    de: "Es wird nicht gespeichert und nicht erneut angezeigt.",
    pt: "Não é guardado e não voltará a ser mostrado.",
    it: "Non viene conservato e non sarà mostrato di nuovo.",
    ja: "保存されず、再表示されることはありません。",
    zh: "它不会被保存，也不会再次显示。",
    hi: "यह संग्रहीत नहीं होता और दोबारा नहीं दिखाया जाएगा।",
    ar: "لا يُخزَّن ولن يُعرض مرة أخرى.",
  },
  "co.copied": {
    en: "I have copied it", es: "Ya lo he copiado", fr: "Je l'ai copié",
    de: "Ich habe es kopiert", pt: "Já o copiei", it: "L'ho copiato",
    ja: "控えました", zh: "我已复制", hi: "मैंने इसे कॉपी कर लिया",
    ar: "نسختُه",
  },
  "co.takeback": {
    en: "Taking a grant back", es: "Retirar una concesión",
    fr: "Reprendre un octroi", de: "Eine Gewährung zurücknehmen",
    pt: "Retirar uma concessão", it: "Ritirare una concessione",
    ja: "付与を取り戻す", zh: "收回一份授予",
    hi: "अनुदान वापस लेना", ar: "استرداد منحة",
  },
  "co.takeback.note": {
    en: "Activation mints a token and hands it to a person. Revoking the bequest is not the same act — this kills the token itself, which is what you want when a grant went to the wrong hands or the condition turned out not to hold.",
    es: "La activación emite un token y se lo entrega a una persona. Revocar el legado no es el mismo acto: esto anula el token en sí, que es lo que quieres cuando una concesión fue a parar a las manos equivocadas o la condición resultó no cumplirse.",
    fr: "L'activation émet un jeton et le remet à une personne. Révoquer le legs n'est pas le même acte : ceci supprime le jeton lui-même, ce que vous voulez lorsqu'un octroi est tombé entre de mauvaises mains ou que la condition s'est révélée non remplie.",
    de: "Die Aktivierung stellt ein Token aus und übergibt es einer Person. Das Vermächtnis zu widerrufen ist nicht dieselbe Handlung — dies vernichtet das Token selbst, und genau das will man, wenn eine Gewährung in die falschen Hände geriet oder die Bedingung doch nicht zutraf.",
    pt: "A ativação emite um token e entrega-o a uma pessoa. Revogar o legado não é o mesmo ato — isto anula o próprio token, que é o que se quer quando uma concessão foi parar às mãos erradas ou a condição afinal não se verificava.",
    it: "L'attivazione emette un token e lo consegna a una persona. Revocare il lascito non è lo stesso atto: questo annulla il token stesso, ed è ciò che serve quando una concessione è finita nelle mani sbagliate o la condizione si è rivelata non soddisfatta.",
    ja: "発動はトークンを発行して人に渡します。遺贈を取り消すのはそれとは別の行為です。こちらはトークン自体を無効にします。付与が誤った相手に渡ったとき、あるいは条件が成立していなかったと判明したときに必要なのはこちらです。",
    zh: "启用会签发一枚令牌并交到某人手上。撤销遗赠并不是同一件事——这里撤销的是令牌本身，当授予落入错误的人手中、或条件其实并不成立时，你要的正是这个。",
    hi: "सक्रियण एक टोकन जारी करके किसी व्यक्ति को सौंपता है। वसीयत रद्द करना वही कार्य नहीं है — यह स्वयं टोकन को समाप्त करता है, और जब अनुदान ग़लत हाथों में चला गया हो या शर्त वस्तुतः पूरी न हुई हो, तब यही चाहिए।",
    ar: "التفعيل يُصدر رمزًا ويسلّمه إلى شخص. وإبطال الوصية ليس الفعل نفسه — هذا يُلغي الرمز ذاته، وهو المطلوب حين تقع منحة في أيدٍ خاطئة أو يتبيّن أن الشرط لم يتحقّق.",
  },
  "co.revoke.grant": {
    en: "Revoke the grant token", es: "Revocar el token de concesión",
    fr: "Révoquer le jeton d'octroi", de: "Das Gewährungs-Token widerrufen",
    pt: "Revogar o token de concessão", it: "Revocare il token di concessione",
    ja: "付与トークンを取り消す", zh: "撤销授予令牌",
    hi: "अनुदान टोकन रद्द करें", ar: "إبطال رمز المنح",
  },
  "co.revoked.grant": {
    en: "The grant token no longer opens anything.",
    es: "El token de concesión ya no abre nada.",
    fr: "Le jeton d'octroi n'ouvre plus rien.",
    de: "Das Gewährungs-Token öffnet nichts mehr.",
    pt: "O token de concessão já não abre nada.",
    it: "Il token di concessione non apre più nulla.",
    ja: "この付与トークンではもう何も開けません。",
    zh: "该授予令牌已无法打开任何内容。",
    hi: "अनुदान टोकन अब कुछ नहीं खोलता।",
    ar: "لم يعد رمز المنح يفتح شيئًا.",
  },
  "co.redeem": {
    en: "Redeeming — the heir's side", es: "Canje — el lado del heredero",
    fr: "Le rachat — du côté de l'héritier",
    de: "Einlösen — die Seite der erbenden Person",
    pt: "Resgate — o lado do herdeiro",
    it: "Riscatto — il lato dell'erede",
    ja: "行使 — 相続する側", zh: "兑现——继承人这一侧",
    hi: "भुनाना — उत्तराधिकारी का पक्ष", ar: "الاستيفاء — جانب الوارث",
  },
  "co.redeem.note": {
    en: "Two separate secrets, and neither works alone: the grant token says the condition was attested, the customer key decrypts. An executor who holds only the token opens nothing.",
    es: "Dos secretos distintos, y ninguno sirve por sí solo: el token de concesión dice que la condición fue atestiguada, la clave del cliente descifra. Un albacea que solo tenga el token no abre nada.",
    fr: "Deux secrets distincts, et aucun ne suffit seul : le jeton d'octroi dit que la condition a été attestée, la clé du client déchiffre. Un exécuteur qui ne détient que le jeton n'ouvre rien.",
    de: "Zwei getrennte Geheimnisse, und keines wirkt allein: das Gewährungs-Token bezeugt die Bedingung, der Kundenschlüssel entschlüsselt. Wer nur das Token hält, öffnet nichts.",
    pt: "Dois segredos distintos, e nenhum funciona sozinho: o token de concessão diz que a condição foi atestada, a chave do cliente decifra. Um testamenteiro que tenha apenas o token não abre nada.",
    it: "Due segreti distinti, e nessuno funziona da solo: il token di concessione dice che la condizione è stata attestata, la chiave del cliente decifra. Un esecutore che possiede solo il token non apre nulla.",
    ja: "別々の秘密が二つあり、どちらも単独では働きません。付与トークンは条件が証明されたことを示し、顧客鍵が復号します。トークンだけを持つ遺言執行者には何も開けません。",
    zh: "两份彼此独立的秘密，缺一不可：授予令牌表明条件已获证实，客户密钥负责解密。只持有令牌的遗嘱执行人什么也打不开。",
    hi: "दो अलग-अलग रहस्य, और कोई भी अकेले काम नहीं करता: अनुदान टोकन कहता है कि शर्त प्रमाणित हुई, ग्राहक कुंजी डिक्रिप्ट करती है। जिस निष्पादक के पास केवल टोकन है, वह कुछ नहीं खोल पाता।",
    ar: "سرّان منفصلان، ولا يكفي أيّهما وحده: رمز المنح يقول إن الشرط قد شُهد به، ومفتاح العميل يفكّ التشفير. ومنفّذ الوصية الذي يملك الرمز وحده لا يفتح شيئًا.",
  },
  "co.grant.ph": {
    en: "Grant token", es: "Token de concesión", fr: "Jeton d'octroi",
    de: "Gewährungs-Token", pt: "Token de concessão",
    it: "Token di concessione", ja: "付与トークン", zh: "授予令牌",
    hi: "अनुदान टोकन", ar: "رمز المنح",
  },
  "co.custkey.ph": {
    en: "Customer key (base64)", es: "Clave del cliente (base64)",
    fr: "Clé du client (base64)", de: "Kundenschlüssel (Base64)",
    pt: "Chave do cliente (base64)", it: "Chiave del cliente (base64)",
    ja: "顧客鍵（base64）", zh: "客户密钥（base64）",
    hi: "ग्राहक कुंजी (base64)", ar: "مفتاح العميل (base64)",
  },
  "co.whatopen": {
    en: "What can I open?", es: "¿Qué puedo abrir?",
    fr: "Qu'est-ce que je peux ouvrir ?", de: "Was kann ich öffnen?",
    pt: "O que posso abrir?", it: "Cosa posso aprire?",
    ja: "何を開けるか", zh: "我能打开什么？",
    hi: "मैं क्या खोल सकता हूँ?", ar: "ماذا أستطيع أن أفتح؟",
  },
  "co.nothing.readable": {
    en: "Nothing is readable under that grant.",
    es: "Nada es legible con esa concesión.",
    fr: "Rien n'est lisible sous cet octroi.",
    de: "Unter dieser Gewährung ist nichts lesbar.",
    pt: "Nada é legível ao abrigo dessa concessão.",
    it: "Nulla è leggibile con quella concessione.",
    ja: "その付与で読めるものはありません。",
    zh: "在该授予下没有任何内容可读。",
    hi: "उस अनुदान के अंतर्गत कुछ भी पठनीय नहीं है।",
    ar: "لا شيء مقروء بموجب تلك المنحة.",
  },
  "co.read": {
    en: "Read", es: "Leer", fr: "Lire", de: "Lesen", pt: "Ler",
    it: "Leggere", ja: "読む", zh: "读取", hi: "पढ़ें", ar: "قراءة",
  },
  "co.ceiling": {
    en: "The gateway's ceiling", es: "El techo de la pasarela",
    fr: "Le plafond de la passerelle", de: "Die Obergrenze des Gateways",
    pt: "O teto do gateway", it: "Il tetto del gateway",
    ja: "ゲートウェイの上限", zh: "网关的上限",
    hi: "गेटवे की सीमा", ar: "سقف البوابة",
  },
  "co.may": {
    en: "It may:", es: "Puede:", fr: "Il peut :", de: "Es darf:",
    pt: "Pode:", it: "Può:", ja: "できること：", zh: "它可以：",
    hi: "यह कर सकता है:", ar: "يجوز له:",
  },
  "co.maynever": {
    en: "It may never:", es: "Nunca puede:", fr: "Il ne peut jamais :",
    de: "Es darf niemals:", pt: "Nunca pode:", it: "Non può mai:",
    ja: "決してできないこと：", zh: "它绝不可以：",
    hi: "यह कभी नहीं कर सकता:", ar: "لا يجوز له أبدًا:",
  },
  "co.shift": {
    en: "Who is on shift", es: "Quién está de turno",
    fr: "Qui est de garde", de: "Wer Dienst hat",
    pt: "Quem está de turno", it: "Chi è di turno",
    ja: "当番は誰か", zh: "谁在值班",
    hi: "पाली पर कौन है", ar: "من في المناوبة",
  },
  "co.nobody": {
    en: "Nobody on shift.", es: "Nadie de turno.", fr: "Personne de garde.",
    de: "Niemand im Dienst.", pt: "Ninguém de turno.",
    it: "Nessuno di turno.", ja: "当番はいません。", zh: "无人值班。",
    hi: "कोई पाली पर नहीं है।", ar: "لا أحد في المناوبة.",
  },
  "co.noroster": {
    en: " No roster configured yet.", es: " Aún no hay turnos configurados.",
    fr: " Aucun planning configuré pour l'instant.",
    de: " Noch kein Dienstplan eingerichtet.",
    pt: " Ainda não há escala configurada.",
    it: " Nessun turno ancora configurato.",
    ja: "　当番表はまだ設定されていません。", zh: " 尚未配置值班表。",
    hi: " अभी कोई ड्यूटी सूची निर्धारित नहीं है।",
    ar: " لم يُضبط جدول مناوبات بعد.",
  },
  "co.overmidnight": {
    en: "over midnight", es: "pasada la medianoche", fr: "après minuit",
    de: "über Mitternacht", pt: "após a meia-noite", it: "oltre la mezzanotte",
    ja: "日付をまたぐ", zh: "跨越午夜", hi: "मध्यरात्रि के पार",
    ar: "بعد منتصف الليل",
  },
  "co.remove": {
    en: "Remove", es: "Quitar", fr: "Retirer", de: "Entfernen",
    pt: "Remover", it: "Rimuovi", ja: "削除", zh: "移除",
    hi: "हटाएँ", ar: "إزالة",
  },
  "co.removed": {
    en: "Removed.", es: "Quitado.", fr: "Retiré.", de: "Entfernt.",
    pt: "Removido.", it: "Rimosso.", ja: "削除しました。", zh: "已移除。",
    hi: "हटा दिया गया।", ar: "أُزيل.",
  },
  "co.name.ph": {
    en: "Name", es: "Nombre", fr: "Nom", de: "Name", pt: "Nome",
    it: "Nome", ja: "名前", zh: "姓名", hi: "नाम", ar: "الاسم",
  },
  "co.role.ph": {
    en: "Role", es: "Función", fr: "Rôle", de: "Rolle", pt: "Função",
    it: "Ruolo", ja: "役割", zh: "职责", hi: "भूमिका", ar: "الدور",
  },
  "co.addroster": {
    en: "Add to roster", es: "Añadir al turno",
    fr: "Ajouter au planning", de: "Zum Dienstplan hinzufügen",
    pt: "Adicionar à escala", it: "Aggiungere al turno",
    ja: "当番表に追加", zh: "加入值班表",
    hi: "ड्यूटी सूची में जोड़ें", ar: "إضافة إلى الجدول",
  },
  "co.tz.ph": {
    en: "Timezone (Europe/London)", es: "Zona horaria (Europe/London)",
    fr: "Fuseau horaire (Europe/London)", de: "Zeitzone (Europe/London)",
    pt: "Fuso horário (Europe/London)", it: "Fuso orario (Europe/London)",
    ja: "タイムゾーン（Europe/London）", zh: "时区（Europe/London）",
    hi: "समय क्षेत्र (Europe/London)", ar: "المنطقة الزمنية (Europe/London)",
  },
  "co.set": {
    en: "Set", es: "Fijar", fr: "Définir", de: "Setzen", pt: "Definir",
    it: "Imposta", ja: "設定", zh: "设定", hi: "निर्धारित करें",
    ar: "ضبط",
  },
  "co.sent": {
    en: "What it sent", es: "Lo que envió", fr: "Ce qu'elle a envoyé",
    de: "Was es gesendet hat", pt: "O que enviou", it: "Cosa ha inviato",
    ja: "送った内容", zh: "它发出了什么",
    hi: "इसने क्या भेजा", ar: "ما الذي أرسله",
  },
  "co.sent.note": {
    en: "Pages the gateway raised when nobody was reachable, and whether they arrived. A page that failed to deliver is the one worth seeing.",
    es: "Avisos que la pasarela lanzó cuando no había nadie localizable, y si llegaron. El aviso que no se entregó es el que merece verse.",
    fr: "Alertes émises par la passerelle quand personne n'était joignable, et si elles sont arrivées. Celle qui n'a pas été remise est celle qu'il faut voir.",
    de: "Rufe, die das Gateway auslöste, als niemand erreichbar war, und ob sie ankamen. Der Ruf, der nicht zugestellt wurde, ist der sehenswerte.",
    pt: "Avisos que o gateway lançou quando ninguém estava contactável, e se chegaram. O aviso que falhou a entrega é o que vale a pena ver.",
    it: "Chiamate che il gateway ha lanciato quando nessuno era raggiungibile, e se sono arrivate. Quella non recapitata è quella che vale la pena vedere.",
    ja: "誰にも連絡がつかなかったときにゲートウェイが上げた呼び出しと、それが届いたかどうか。見る価値があるのは届かなかった呼び出しです。",
    zh: "无人可联系时网关发出的呼叫，以及它们是否送达。真正值得看的，是那条没能送达的。",
    hi: "जब कोई उपलब्ध नहीं था तब गेटवे ने जो पेज भेजे, और वे पहुँचे या नहीं। जो पेज पहुँच नहीं सका, वही देखने योग्य है।",
    ar: "النداءات التي أطلقتها البوابة حين تعذّر الوصول إلى أحد، وهل وصلت. النداء الذي أخفق في التسليم هو الجدير بالنظر.",
  },
  "co.channel": {
    en: "Channel", es: "Canal", fr: "Canal", de: "Kanal", pt: "Canal",
    it: "Canale", ja: "経路", zh: "通道", hi: "चैनल", ar: "القناة",
  },
  "co.configured": {
    en: "configured", es: "configurado", fr: "configuré", de: "eingerichtet",
    pt: "configurado", it: "configurato", ja: "設定済み", zh: "已配置",
    hi: "कॉन्फ़िगर किया गया", ar: "مضبوطة",
  },
  "co.notconfigured": {
    en: "not configured", es: "sin configurar", fr: "non configuré",
    de: "nicht eingerichtet", pt: "não configurado", it: "non configurato",
    ja: "未設定", zh: "未配置", hi: "कॉन्फ़िगर नहीं", ar: "غير مضبوطة",
  },
  "co.signed": {
    en: ", signed", es: ", firmado", fr: ", signé", de: ", signiert",
    pt: ", assinado", it: ", firmato", ja: "、署名あり", zh: "，已签名",
    hi: ", हस्ताक्षरित", ar: "، موقّعة",
  },
  "co.nothingpaged": {
    en: "Nothing paged.", es: "Ningún aviso.", fr: "Aucune alerte.",
    de: "Nichts gerufen.", pt: "Nenhum aviso.", it: "Nessuna chiamata.",
    ja: "呼び出しはありません。", zh: "没有发出呼叫。",
    hi: "कोई पेज नहीं भेजा गया।", ar: "لا نداءات.",
  },
  "co.nothingcould": {
    en: "Nothing paged — and nothing could have been, because no channel is configured. That is a different fact from a quiet week.",
    es: "Ningún aviso — y ninguno habría sido posible, porque no hay canal configurado. Ese es un hecho distinto de una semana tranquila.",
    fr: "Aucune alerte — et aucune n'aurait pu l'être, car aucun canal n'est configuré. C'est un fait différent d'une semaine calme.",
    de: "Nichts gerufen — und nichts hätte gerufen werden können, denn es ist kein Kanal eingerichtet. Das ist eine andere Tatsache als eine ruhige Woche.",
    pt: "Nenhum aviso — e nenhum poderia ter sido enviado, porque não há canal configurado. Esse é um facto diferente de uma semana calma.",
    it: "Nessuna chiamata — e nessuna avrebbe potuto esserci, perché non è configurato alcun canale. È un fatto diverso da una settimana tranquilla.",
    ja: "呼び出しはありません。そして呼び出しようもありませんでした。経路が設定されていないからです。これは「静かな一週間」とは別の事実です。",
    zh: "没有发出呼叫——而且根本无从发出，因为尚未配置任何通道。这与「平静的一周」是完全不同的事实。",
    hi: "कोई पेज नहीं भेजा गया — और भेजा जा भी नहीं सकता था, क्योंकि कोई चैनल कॉन्फ़िगर नहीं है। यह एक शांत सप्ताह से भिन्न तथ्य है।",
    ar: "لا نداءات — ولم يكن بالإمكان إطلاق أي نداء، إذ لا قناة مضبوطة. وهذه حقيقة مختلفة عن أسبوع هادئ.",
  },
};

/** `t("gd.title", lang)` — the key itself if the row is missing, which is
 * loud in a screenshot and silent in a crash. */
export function t(key: string, lang: Lang): string {
  const row = CHROME[key];
  return row?.[lang] ?? row?.en ?? key;
}

/** `fill("gd.progress", lang, { done: 2, total: 9 })`.
 *
 * A slot the translation dropped renders nothing rather than the brace, and
 * `test_the_tabs_are_translated_and_the_screens_are_not.py` checks on the
 * shell side that every slot survives every translation. */
export function fill(key: string, lang: Lang,
                     slots: Record<string, string | number>): string {
  return t(key, lang).replace(/\{(\w+)\}/g,
    (whole, name) => (name in slots ? String(slots[name]) : whole));
}
