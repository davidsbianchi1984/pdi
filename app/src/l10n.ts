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
