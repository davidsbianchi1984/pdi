import Foundation

/// App-chrome localization: tab names and the most common actions, in every
/// language the backend supports. PDI's explanatory notes are localized
/// server-side by the tenant's language setting; this table covers the frame
/// around them. Missing keys fall back to English.
enum L10n {
    static func t(_ key: String, _ lang: String) -> String {
        table[key]?[lang] ?? table[key]?["en"] ?? key
    }

    /// The language of somebody who has no account to take one from.
    ///
    /// `AppState.language` is read from the stored setting and defaults to
    /// `"en"` until an account exists. Every sentence the backend composes on
    /// a public route is chosen from `Accept-Language`, and this shell was
    /// sending no such header — the phone had been carrying the answer in
    /// `Locale.preferredLanguages` the whole time and nothing read it.
    ///
    /// Region dropped (`es-419` and `es-ES` are both `es`); anything the app
    /// does not carry falls back to English rather than guessing.
    static var deviceLanguage: String {
        for tag in Locale.preferredLanguages {
            let base = String(tag.split(separator: "-")[0]).lowercased()
            if supported.contains(base) { return base }
        }
        return "en"
    }

    static let supported = ["en", "es", "fr", "de", "pt", "it", "ja", "zh",
                            "hi", "ar"]

    private static let table: [String: [String: String]] = [
        "nfil.content": ["en": "Content", "es": "Contenido", "fr": "Contenu", "de": "Inhalt", "pt": "Conteúdo", "it": "Contenuto", "ja": "内容", "zh": "内容", "hi": "सामग्री", "ar": "المحتوى"],
        "nfil.content.ph": ["en": "the file body to seal", "es": "el cuerpo del archivo a sellar", "fr": "le corps du fichier à sceller", "de": "der zu versiegelnde Dateiinhalt", "pt": "o corpo do ficheiro a selar", "it": "il corpo del file da sigillare", "ja": "封印するファイル本文", "zh": "要封存的文件正文", "hi": "सील करने हेतु फ़ाइल सामग्री", "ar": "محتوى الملف المراد ختمه"],
        "nfil.filename": ["en": "Filename", "es": "Nombre de archivo", "fr": "Nom du fichier", "de": "Dateiname", "pt": "Nome do ficheiro", "it": "Nome del file", "ja": "ファイル名", "zh": "文件名", "hi": "फ़ाइल नाम", "ar": "اسم الملف"],
        "nfil.filename.ph": ["en": "e.g. results.pdf", "es": "p. ej. resultados.pdf", "fr": "ex. resultats.pdf", "de": "z. B. ergebnisse.pdf", "pt": "p. ex. resultados.pdf", "it": "es. risultati.pdf", "ja": "例：results.pdf", "zh": "例如：results.pdf", "hi": "उदा. results.pdf", "ar": "مثال: results.pdf"],
        "nfil.programs": ["en": "Programs", "es": "Programas", "fr": "Programmes", "de": "Programme", "pt": "Programas", "it": "Programmi", "ja": "プログラム", "zh": "合规方案", "hi": "कार्यक्रम", "ar": "البرامج"],
        "nfil.recipient": ["en": "Recipient", "es": "Destinatario", "fr": "Destinataire", "de": "Empfänger", "pt": "Destinatário", "it": "Destinatario", "ja": "受取人", "zh": "接收人", "hi": "प्राप्तकर्ता", "ar": "المستلم"],
        "nfil.recipient.ph": ["en": "who it's for", "es": "para quién es", "fr": "à qui c'est destiné", "de": "für wen es ist", "pt": "para quem é", "it": "per chi è", "ja": "誰宛てか", "zh": "发送给谁", "hi": "किसके लिए", "ar": "لمن هو"],
        "nfil.seal": ["en": "Seal & create", "es": "Sellar y crear", "fr": "Sceller et créer", "de": "Versiegeln und anlegen", "pt": "Selar e criar", "it": "Sigilla e crea", "ja": "封印して作成", "zh": "封存并创建", "hi": "सील करें और बनाएँ", "ar": "ختم وإنشاء"],
        "nfil.sub": ["en": "Seal a file for a recipient under compliance controls. Retention follows the strictest program you pick.", "es": "Sella un archivo para un destinatario bajo controles de cumplimiento. La retención sigue el programa más estricto que elijas.", "fr": "Scellez un fichier pour un destinataire sous contrôles de conformité. La conservation suit le programme le plus strict que vous choisissez.", "de": "Versiegeln Sie eine Datei für einen Empfänger unter Compliance-Kontrollen. Die Aufbewahrung richtet sich nach dem strengsten Programm, das Sie wählen.", "pt": "Sele um ficheiro para um destinatário sob controlos de conformidade. A retenção segue o programa mais estrito que escolher.", "it": "Sigilla un file per un destinatario con controlli di conformità. La conservazione segue il programma più rigoroso che scegli.", "ja": "コンプライアンス管理のもとで受取人向けにファイルを封印します。保持期間は選択した中で最も厳格なプログラムに従います。", "zh": "在合规控制下为接收人封存文件。保留期限遵循你所选最严格的合规方案。", "hi": "अनुपालन नियंत्रणों के तहत प्राप्तकर्ता के लिए फ़ाइल सील करें। प्रतिधारण आपके चुने हुए सबसे कठोर कार्यक्रम का पालन करता है।", "ar": "اختم ملفًا لمستلم وفق ضوابط الامتثال. تتبع مدة الاحتفاظ أشدّ برنامج تختاره."],
        "nfil.token.hand": ["en": "Hand this to the recipient out of band; it is the only way to retrieve the file.", "es": "Entrega esto al destinatario por otro canal; es la única forma de recuperar el archivo.", "fr": "Remettez ceci au destinataire par un autre canal ; c'est le seul moyen de récupérer le fichier.", "de": "Übergeben Sie dies dem Empfänger über einen anderen Kanal; es ist der einzige Weg, die Datei abzurufen.", "pt": "Entregue isto ao destinatário por outro canal; é a única forma de recuperar o ficheiro.", "it": "Consegna questo al destinatario per un altro canale; è l'unico modo per recuperare il file.", "ja": "これは別の経路で受取人に渡してください。ファイルを取り出す唯一の手段です。", "zh": "请通过其他渠道将其交给接收人；这是取回该文件的唯一方式。", "hi": "इसे प्राप्तकर्ता को किसी अन्य माध्यम से सौंपें; फ़ाइल पाने का यही एकमात्र रास्ता है।", "ar": "سلّم هذا إلى المستلم عبر قناة أخرى؛ فهو السبيل الوحيد لاسترجاع الملف."],
        "nfil.token.once": ["en": "Receive token — shown once", "es": "Token de recepción: se muestra una sola vez", "fr": "Jeton de réception — affiché une seule fois", "de": "Empfangs-Token — nur einmal angezeigt", "pt": "Token de receção — mostrado uma só vez", "it": "Token di ricezione — mostrato una sola volta", "ja": "受信トークン — 一度だけ表示されます", "zh": "接收令牌 — 仅显示一次", "hi": "प्राप्ति टोकन — केवल एक बार दिखाया जाता है", "ar": "رمز الاستلام — يُعرض مرة واحدة"],
        "nint.content.ph": ["en": "the file body", "es": "el cuerpo del archivo", "fr": "le corps du fichier", "de": "der Dateiinhalt", "pt": "o corpo do ficheiro", "it": "il corpo del file", "ja": "ファイル本文", "zh": "文件正文", "hi": "फ़ाइल सामग्री", "ar": "محتوى الملف"],
        "nint.filename.ph": ["en": "e.g. w2.pdf", "es": "p. ej. w2.pdf", "fr": "ex. w2.pdf", "de": "z. B. w2.pdf", "pt": "p. ex. w2.pdf", "it": "es. w2.pdf", "ja": "例：w2.pdf", "zh": "例如：w2.pdf", "hi": "उदा. w2.pdf", "ar": "مثال: w2.pdf"],
        "nint.go": ["en": "Submit into the newest open intake", "es": "Entregar en la recepción abierta más reciente", "fr": "Déposer dans la dernière collecte ouverte", "de": "In die neueste offene Annahme einreichen", "pt": "Entregar na receção aberta mais recente", "it": "Invia all'ultima raccolta aperta", "ja": "最新の受付に提出", "zh": "提交至最新的开放受理", "hi": "नवीनतम खुले इनटेक में जमा करें", "ar": "الإرسال إلى أحدث استلام مفتوح"],
        "nint.token": ["en": "Submit token", "es": "Token de entrega", "fr": "Jeton de dépôt", "de": "Einreichungs-Token", "pt": "Token de entrega", "it": "Token di invio", "ja": "提出トークン", "zh": "提交令牌", "hi": "सबमिट टोकन", "ar": "رمز التسليم"],
        "nint.token.once": ["en": "Submit token — shown once", "es": "Token de entrega: se muestra una sola vez", "fr": "Jeton de dépôt — affiché une seule fois", "de": "Einreichungs-Token — nur einmal angezeigt", "pt": "Token de entrega — mostrado uma só vez", "it": "Token di invio — mostrato una sola volta", "ja": "提出トークン — 一度だけ表示されます", "zh": "提交令牌 — 仅显示一次", "hi": "सबमिट टोकन — केवल एक बार दिखाया जाता है", "ar": "رمز التسليم — يُعرض مرة واحدة"],
        "nint.token.ph": ["en": "intk token", "es": "token intk", "fr": "jeton intk", "de": "intk-Token", "pt": "token intk", "it": "token intk", "ja": "intk トークン", "zh": "intk 令牌", "hi": "intk टोकन", "ar": "رمز intk"],
        "nint.token.send": ["en": "Send this to the counterparty out of band; it is their only way in.", "es": "Envía esto a la contraparte por otro canal; es su única vía de entrada.", "fr": "Envoyez ceci à la contrepartie par un autre canal ; c'est sa seule porte d'entrée.", "de": "Senden Sie dies der Gegenpartei über einen anderen Kanal; es ist ihr einziger Zugang.", "pt": "Envie isto à contraparte por outro canal; é a única entrada de que dispõe.", "it": "Invia questo alla controparte per un altro canale; è la sua unica via d'accesso.", "ja": "これは別の経路で相手方に送ってください。相手が入れる唯一の手段です。", "zh": "请通过其他渠道发送给对方；这是对方唯一的进入方式。", "hi": "इसे प्रतिपक्ष को किसी अन्य माध्यम से भेजें; उनके लिए यही एकमात्र प्रवेश है।", "ar": "أرسل هذا إلى الطرف المقابل عبر قناة أخرى؛ فهو مدخله الوحيد."],
        "nrec.t.records": ["en": "Records", "es": "Registros", "fr": "Enregistrements", "de": "Datensätze", "pt": "Registos", "it": "Record", "ja": "レコード", "zh": "记录", "hi": "रिकॉर्ड", "ar": "السجلات"],
        "nreq.close": ["en": "Close request", "es": "Cerrar la solicitud", "fr": "Clore la demande", "de": "Anfrage schließen", "pt": "Fechar o pedido", "it": "Chiudi la richiesta", "ja": "依頼を終了する", "zh": "关闭请求", "hi": "अनुरोध बंद करें", "ar": "إغلاق الطلب"],
        "nreq.from": ["en": "From", "es": "De", "fr": "De", "de": "Von", "pt": "De", "it": "Da", "ja": "送信元", "zh": "来自", "hi": "से", "ar": "من"],
        "nreq.from.ph": ["en": "who should send it", "es": "quién debe enviarlo", "fr": "qui doit l'envoyer", "de": "wer es senden soll", "pt": "quem deve enviá-lo", "it": "chi deve inviarlo", "ja": "誰が送るべきか", "zh": "应由谁发送", "hi": "इसे कौन भेजे", "ar": "من يرسله"],
        "nreq.go": ["en": "Request file", "es": "Solicitar archivo", "fr": "Demander le fichier", "de": "Datei anfordern", "pt": "Solicitar ficheiro", "it": "Richiedi il file", "ja": "ファイルを依頼", "zh": "请求文件", "hi": "फ़ाइल का अनुरोध करें", "ar": "طلب ملف"],
        "nreq.purpose": ["en": "Purpose (optional)", "es": "Motivo (opcional)", "fr": "Objet (facultatif)", "de": "Zweck (optional)", "pt": "Finalidade (opcional)", "it": "Scopo (facoltativo)", "ja": "目的（任意）", "zh": "用途（可选）", "hi": "उद्देश्य (वैकल्पिक)", "ar": "الغرض (اختياري)"],
        "nreq.purpose.ph": ["en": "why you need it", "es": "por qué lo necesitas", "fr": "pourquoi vous en avez besoin", "de": "warum Sie es brauchen", "pt": "porque precisa dele", "it": "perché ti serve", "ja": "なぜ必要か", "zh": "为什么需要它", "hi": "आपको इसकी आवश्यकता क्यों है", "ar": "لماذا تحتاجه"],
        "ntr.answer.sub": ["en": "Paste an intake's submit token to answer it — this is what the counterparty does, no vault account involved.", "es": "Pega el token de entrega de una recepción para responderla: esto es lo que hace la contraparte, sin ninguna cuenta de la bóveda.", "fr": "Collez le jeton de dépôt d'une réception pour y répondre — c'est ce que fait la contrepartie, sans aucun compte du coffre.", "de": "Fügen Sie das Einreichungs-Token einer Annahme ein, um sie zu beantworten — das tut die Gegenpartei, ganz ohne Tresorkonto.", "pt": "Cole o token de entrega de uma receção para lhe responder — é o que a contraparte faz, sem qualquer conta do cofre.", "it": "Incolla il token di invio di una ricezione per rispondere — è ciò che fa la controparte, senza alcun account del caveau.", "ja": "受付の提出トークンを貼り付けて応答します — これは相手方が行う操作で、保管庫のアカウントは不要です。", "zh": "粘贴接收的提交令牌以作答复 — 这是对方的操作，无需保险库账户。", "hi": "उत्तर देने के लिए किसी प्राप्ति का सबमिट टोकन चिपकाएँ — यह प्रतिपक्ष करता है, वॉल्ट खाते की आवश्यकता नहीं।", "ar": "الصق رمز تسليم استلامٍ للردّ عليه — هذا ما يفعله الطرف المقابل، دون أي حساب في الخزنة."],
        "ntr.as.sender": ["en": "Act as the sender", "es": "Actuar como remitente", "fr": "Agir en tant qu'expéditeur", "de": "Als Absender handeln", "pt": "Agir como remetente", "it": "Agisci come mittente", "ja": "送信者として操作する", "zh": "以发送方身份操作", "hi": "भेजने वाले के रूप में कार्य करें", "ar": "التصرّف بصفة المرسِل"],
        "ntr.intake": ["en": "Secure intake", "es": "Recepción segura", "fr": "Réception sécurisée", "de": "Sichere Annahme", "pt": "Receção segura", "it": "Ricezione sicura", "ja": "セキュアな受付", "zh": "安全接收", "hi": "सुरक्षित प्राप्ति", "ar": "استلام آمن"],
        "ntr.intake.sub": ["en": "Ask a counterparty to send a file in. They authenticate with the one-shot submit token — no account needed.", "es": "Pide a una contraparte que envíe un archivo. Se autentica con el token de entrega de un solo uso; no necesita cuenta.", "fr": "Demandez à une contrepartie d'envoyer un fichier. Elle s'authentifie avec le jeton de dépôt à usage unique — aucun compte requis.", "de": "Bitten Sie eine Gegenpartei, eine Datei einzusenden. Sie authentifiziert sich mit dem Einmal-Einreichungs-Token — kein Konto nötig.", "pt": "Peça a uma contraparte que envie um ficheiro. Autentica-se com o token de entrega de utilização única — sem necessidade de conta.", "it": "Chiedi a una controparte di inviare un file. Si autentica con il token di invio monouso — nessun account necessario.", "ja": "相手方にファイルの送付を依頼します。相手は使い捨ての提出トークンで認証します — アカウントは不要です。", "zh": "请对方发送文件。对方使用一次性提交令牌进行验证 — 无需账户。", "hi": "किसी प्रतिपक्ष से फ़ाइल भेजने को कहें। वे एक-बार वाले सबमिट टोकन से प्रमाणित होते हैं — किसी खाते की आवश्यकता नहीं।", "ar": "اطلب من الطرف المقابل إرسال ملف. يجري التحقق منه برمز التسليم أحادي الاستخدام — دون حاجة إلى حساب."],
        "ntr.read": ["en": "Read sealed file", "es": "Leer el archivo sellado", "fr": "Lire le fichier scellé", "de": "Versiegelte Datei lesen", "pt": "Ler o ficheiro selado", "it": "Leggi il file sigillato", "ja": "封印されたファイルを読む", "zh": "读取封存文件", "hi": "सीलबंद फ़ाइल पढ़ें", "ar": "قراءة الملف المختوم"],
        "ntr.revoke": ["en": "Revoke access", "es": "Revocar el acceso", "fr": "Révoquer l'accès", "de": "Zugriff widerrufen", "pt": "Revogar o acesso", "it": "Revoca l'accesso", "ja": "アクセスを取り消す", "zh": "撤销访问权", "hi": "पहुँच निरस्त करें", "ar": "إلغاء الوصول"],
        "ntr.t.intake": ["en": "Intake", "es": "Recepción", "fr": "Réception", "de": "Eingang", "pt": "Receção", "it": "In entrata", "ja": "受付", "zh": "接收", "hi": "प्राप्ति", "ar": "استلام"],
        "ntr.t.outbound": ["en": "Outbound", "es": "Salientes", "fr": "Sortants", "de": "Ausgehend", "pt": "Enviados", "it": "In uscita", "ja": "送信", "zh": "发出", "hi": "भेजे गए", "ar": "صادر"],
        "offline.title": ["en": "What this deployment can reach", "es": "Qué puede alcanzar esta instalación", "fr": "Ce que ce déploiement peut atteindre", "de": "Was diese Installation erreichen kann", "pt": "O que esta instalação pode alcançar", "it": "Cosa può raggiungere questa installazione", "ja": "この環境が接続できる範囲", "zh": "此部署可以连接到什么", "hi": "यह परिनियोजन किस तक पहुँच सकता है", "ar": "ما يمكن أن يصل إليه هذا النشر"],
        "offline.on": ["en": "Offline — nothing leaves this machine", "es": "Sin conexión — nada sale de esta máquina", "fr": "Hors ligne — rien ne quitte cette machine", "de": "Offline — nichts verlässt diesen Rechner", "pt": "Offline — nada sai desta máquina", "it": "Offline — nulla esce da questa macchina", "ja": "オフライン — このマシンから何も出ません", "zh": "离线 — 任何内容都不会离开这台机器", "hi": "ऑफ़लाइन — इस मशीन से कुछ भी बाहर नहीं जाता", "ar": "دون اتصال — لا شيء يغادر هذا الجهاز"],
        "offline.off": ["en": "Online — this deployment can reach other machines", "es": "En línea — esta instalación puede alcanzar otras máquinas", "fr": "En ligne — ce déploiement peut atteindre d’autres machines", "de": "Online — diese Installation kann andere Rechner erreichen", "pt": "Online — esta instalação pode alcançar outras máquinas", "it": "Online — questa installazione può raggiungere altre macchine", "ja": "オンライン — この環境は他のマシンに接続できます", "zh": "在线 — 此部署可以连接其他机器", "hi": "ऑनलाइन — यह परिनियोजन अन्य मशीनों तक पहुँच सकता है", "ar": "متصل — يمكن لهذا النشر الوصول إلى أجهزة أخرى"],
        "wel.title": ["en": "Sign in to your vault", "es": "Entra en tu bóveda", "fr": "Connectez-vous à votre coffre", "de": "Melde dich an deinem Tresor an", "pt": "Entre no seu cofre", "it": "Accedi alla tua cassaforte", "ja": "保管庫にサインインする", "zh": "登录你的保险库", "hi": "अपने वॉल्ट में साइन इन करें", "ar": "سجّل الدخول إلى خزنتك"],
        "wel.sub": ["en": "Paste the tenant token you were issued. It authorizes every call and never leaves this device unencrypted in transit.", "es": "Pega el token de inquilino que se te entregó. Autoriza cada llamada y nunca sale de este dispositivo sin cifrar.", "fr": "Collez le jeton de locataire qui vous a été remis. Il autorise chaque appel et ne quitte jamais cet appareil en clair.", "de": "Füge das dir ausgestellte Mandanten-Token ein. Es autorisiert jeden Aufruf und verlässt dieses Gerät nie unverschlüsselt.", "pt": "Cole o token de inquilino que lhe foi entregue. Autoriza cada chamada e nunca sai deste dispositivo sem cifra.", "it": "Incolla il token del tenant che ti è stato rilasciato. Autorizza ogni chiamata e non lascia mai questo dispositivo in chiaro.", "ja": "発行されたテナントトークンを貼り付けてください。すべての呼び出しを認可するもので、暗号化されないままこの端末を出ることはありません。", "zh": "粘贴你收到的租户令牌。它为每一次调用授权，并且绝不会以未加密的形式离开这台设备。", "hi": "आपको जारी किया गया टेनेंट टोकन यहाँ चिपकाइए। यह हर कॉल को अधिकृत करता है और बिना कूटलेखन के इस डिवाइस से कभी बाहर नहीं जाता।", "ar": "الصق رمز المستأجر الذي صدر لك. فهو يخوّل كل نداء، ولا يغادر هذا الجهاز غير مُعمّى أبدًا."],
        "wel.token": ["en": "Vault token", "es": "Token de la bóveda", "fr": "Jeton du coffre", "de": "Tresor-Token", "pt": "Token do cofre", "it": "Token della cassaforte", "ja": "保管庫のトークン", "zh": "保险库令牌", "hi": "वॉल्ट टोकन", "ar": "رمز الخزنة"],
        "wel.server": ["en": "Server", "es": "Servidor", "fr": "Serveur", "de": "Server", "pt": "Servidor", "it": "Server", "ja": "サーバー", "zh": "服务器", "hi": "सर्वर", "ar": "الخادم"],
        "wel.language": ["en": "Language", "es": "Idioma", "fr": "Langue", "de": "Sprache", "pt": "Idioma", "it": "Lingua", "ja": "言語", "zh": "语言", "hi": "भाषा", "ar": "اللغة"],
        "wel.unlock": ["en": "Unlock", "es": "Desbloquear", "fr": "Déverrouiller", "de": "Entsperren", "pt": "Desbloquear", "it": "Sblocca", "ja": "解錠する", "zh": "解锁", "hi": "खोलें", "ar": "افتح القفل"],
        "wel.backend": ["en": "Start the backend:", "es": "Arranca el servidor:", "fr": "Démarrez le serveur :", "de": "Starte das Backend:", "pt": "Inicie o servidor:", "it": "Avvia il backend:", "ja": "バックエンドを起動：", "zh": "启动后端：", "hi": "बैकएंड शुरू कीजिए:", "ar": "شغّل الخادم:"],
        "tab.overview": ["en": "Overview", "es": "Resumen", "fr": "Aperçu",
                         "de": "Übersicht", "pt": "Visão geral", "it": "Panoramica",
                         "ja": "概要", "zh": "概览", "hi": "अवलोकन", "ar": "نظرة عامة"],
        "tab.vault": ["en": "Vault", "es": "Bóveda", "fr": "Coffre",
                      "de": "Tresor", "pt": "Cofre", "it": "Cassaforte",
                      "ja": "保管庫", "zh": "保险库", "hi": "वॉल्ट", "ar": "الخزنة"],
        "tab.audit": ["en": "Audit", "es": "Auditoría", "fr": "Audit",
                      "de": "Audit", "pt": "Auditoria", "it": "Audit",
                      "ja": "監査", "zh": "审计", "hi": "ऑडिट", "ar": "تدقيق"],
        "tab.sources": ["en": "Sources", "es": "Fuentes", "fr": "Sources",
                        "de": "Quellen", "pt": "Fontes", "it": "Fonti",
                        "ja": "ソース", "zh": "来源", "hi": "स्रोत", "ar": "المصادر"],
        "tab.transfers": ["en": "Transfers", "es": "Transferencias", "fr": "Transferts",
                          "de": "Übertragungen", "pt": "Transferências", "it": "Trasferimenti",
                          "ja": "転送", "zh": "传输", "hi": "स्थानांतरण", "ar": "التحويلات"],
        "tab.robots": ["en": "Robots", "es": "Robots", "fr": "Robots",
                       "de": "Roboter", "pt": "Robôs", "it": "Robot",
                       "ja": "ロボット", "zh": "机器人", "hi": "रोबोट", "ar": "روبوتات"],
        "tab.connectors": ["en": "Connectors", "es": "Conectores", "fr": "Connecteurs",
                           "de": "Konnektoren", "pt": "Conectores", "it": "Connettori",
                           "ja": "コネクタ", "zh": "连接器", "hi": "कनेक्टर", "ar": "الموصلات"],
        "action.sign_out": ["en": "Sign out", "es": "Cerrar sesión", "fr": "Se déconnecter",
                            "de": "Abmelden", "pt": "Sair", "it": "Esci",
                            "ja": "サインアウト", "zh": "退出登录", "hi": "साइन आउट",
                            "ar": "تسجيل الخروج"],
    ]
}
