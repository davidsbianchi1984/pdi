package com.pdi.vault

import android.content.res.Resources

/**
 * App-chrome localization: tab names and the most common actions, in every
 * language the backend supports. PDI's explanatory notes are localized
 * server-side by the tenant's language setting; this table covers the frame
 * around them. Missing keys fall back to English.
 */
object L10n {
    fun t(key: String, lang: String): String =
        table[key]?.let { it[lang] ?: it["en"] } ?: key

    val supported = listOf("en", "es", "fr", "de", "pt", "it", "ja", "zh",
                           "hi", "ar")

    /**
     * The language of somebody who has no account to take one from.
     *
     * `AppState.language` comes from the stored setting and is "en" until an
     * account exists. Every sentence the backend composes on a public route is
     * chosen from `Accept-Language`, and this shell was sending no such header
     * — the phone has been carrying the answer in the system configuration all
     * along.
     *
     * Region dropped; anything this app does not carry falls back to English
     * rather than guessing.
     */
    fun deviceLanguage(): String {
        val locales = Resources.getSystem().configuration.locales
        for (i in 0 until locales.size()) {
            val base = locales[i].language.lowercase()
            if (supported.contains(base)) return base
        }
        return "en"
    }

    private val table: Map<String, Map<String, String>> = mapOf(
        "nacc.handle" to mapOf("en" to "Handle (optional)", "es" to "Identificador (opcional)", "fr" to "Identifiant (facultatif)", "de" to "Kennung (optional)", "pt" to "Identificador (opcional)", "it" to "Handle (facoltativo)", "ja" to "ハンドル（任意）", "zh" to "用户名（可选）", "hi" to "हैंडल (वैकल्पिक)", "ar" to "المعرّف (اختياري)"),
        "nacc.handle.ph" to mapOf("en" to "@account", "es" to "@cuenta", "fr" to "@compte", "de" to "@konto", "pt" to "@conta", "it" to "@account", "ja" to "@アカウント", "zh" to "@账户", "hi" to "@खाता", "ar" to "@حساب"),
        "nacc.id.ph" to mapOf("en" to "pdi_…", "es" to "pdi_…", "fr" to "pdi_…", "de" to "pdi_…", "pt" to "pdi_…", "it" to "pdi_…", "ja" to "pdi_…", "zh" to "pdi_…", "hi" to "pdi_…", "ar" to "pdi_…"),
        "nadm.retire" to mapOf("en" to "Retire old", "es" to "Retirar la anterior", "fr" to "Retirer l'ancienne", "de" to "Alte zurückziehen", "pt" to "Retirar a anterior", "it" to "Ritira la vecchia", "ja" to "旧鍵を廃止", "zh" to "停用旧密钥", "hi" to "पुरानी हटाएँ", "ar" to "سحب القديم"),
        "nadm.rotate" to mapOf("en" to "Rotate key", "es" to "Rotar la clave", "fr" to "Faire tourner la clé", "de" to "Schlüssel rotieren", "pt" to "Rodar a chave", "it" to "Ruota la chiave", "ja" to "鍵をローテーション", "zh" to "轮换密钥", "hi" to "कुंजी घुमाएँ", "ar" to "تدوير المفتاح"),
        "nadm.token" to mapOf("en" to "Admin token", "es" to "Token de administrador", "fr" to "Jeton d'administration", "de" to "Admin-Token", "pt" to "Token de administrador", "it" to "Token di amministrazione", "ja" to "管理者トークン", "zh" to "管理员令牌", "hi" to "एडमिन टोकन", "ar" to "رمز المشرف"),
        "nadm.versions" to mapOf("en" to "Load versions", "es" to "Cargar versiones", "fr" to "Charger les versions", "de" to "Versionen laden", "pt" to "Carregar versões", "it" to "Carica le versioni", "ja" to "バージョンを読み込む", "zh" to "加载版本", "hi" to "संस्करण लोड करें", "ar" to "تحميل الإصدارات"),
        "nfb.msg.ph" to mapOf("en" to "What's on your mind?", "es" to "¿Qué te preocupa?", "fr" to "Qu'avez-vous en tête ?", "de" to "Was beschäftigt Sie?", "pt" to "O que lhe vai na cabeça?", "it" to "A cosa stai pensando?", "ja" to "気になっていることは？", "zh" to "你在想什么？", "hi" to "आपके मन में क्या है?", "ar" to "بماذا تفكر؟"),
        "nfb.send" to mapOf("en" to "Send feedback", "es" to "Enviar comentarios", "fr" to "Envoyer un retour", "de" to "Rückmeldung senden", "pt" to "Enviar comentários", "it" to "Invia un riscontro", "ja" to "フィードバックを送る", "zh" to "发送反馈", "hi" to "प्रतिक्रिया भेजें", "ar" to "إرسال ملاحظات"),
        "nfil.content" to mapOf("en" to "Content", "es" to "Contenido", "fr" to "Contenu", "de" to "Inhalt", "pt" to "Conteúdo", "it" to "Contenuto", "ja" to "内容", "zh" to "内容", "hi" to "सामग्री", "ar" to "المحتوى"),
        "nfil.content.ph" to mapOf("en" to "the file body to seal", "es" to "el cuerpo del archivo a sellar", "fr" to "le corps du fichier à sceller", "de" to "der zu versiegelnde Dateiinhalt", "pt" to "o corpo do ficheiro a selar", "it" to "il corpo del file da sigillare", "ja" to "封印するファイル本文", "zh" to "要封存的文件正文", "hi" to "सील करने हेतु फ़ाइल सामग्री", "ar" to "محتوى الملف المراد ختمه"),
        "nfil.filename" to mapOf("en" to "Filename", "es" to "Nombre de archivo", "fr" to "Nom du fichier", "de" to "Dateiname", "pt" to "Nome do ficheiro", "it" to "Nome del file", "ja" to "ファイル名", "zh" to "文件名", "hi" to "फ़ाइल नाम", "ar" to "اسم الملف"),
        "nfil.filename.ph" to mapOf("en" to "e.g. results.pdf", "es" to "p. ej. resultados.pdf", "fr" to "ex. resultats.pdf", "de" to "z. B. ergebnisse.pdf", "pt" to "p. ex. resultados.pdf", "it" to "es. risultati.pdf", "ja" to "例：results.pdf", "zh" to "例如：results.pdf", "hi" to "उदा. results.pdf", "ar" to "مثال: results.pdf"),
        "nfil.recipient" to mapOf("en" to "Recipient", "es" to "Destinatario", "fr" to "Destinataire", "de" to "Empfänger", "pt" to "Destinatário", "it" to "Destinatario", "ja" to "受取人", "zh" to "接收人", "hi" to "प्राप्तकर्ता", "ar" to "المستلم"),
        "nfil.recipient.ph" to mapOf("en" to "who it's for", "es" to "para quién es", "fr" to "à qui c'est destiné", "de" to "für wen es ist", "pt" to "para quem é", "it" to "per chi è", "ja" to "誰宛てか", "zh" to "发送给谁", "hi" to "किसके लिए", "ar" to "لمن هو"),
        "nfil.seal" to mapOf("en" to "Seal & create", "es" to "Sellar y crear", "fr" to "Sceller et créer", "de" to "Versiegeln und anlegen", "pt" to "Selar e criar", "it" to "Sigilla e crea", "ja" to "封印して作成", "zh" to "封存并创建", "hi" to "सील करें और बनाएँ", "ar" to "ختم وإنشاء"),
        "nint.content.ph" to mapOf("en" to "the file body", "es" to "el cuerpo del archivo", "fr" to "le corps du fichier", "de" to "der Dateiinhalt", "pt" to "o corpo do ficheiro", "it" to "il corpo del file", "ja" to "ファイル本文", "zh" to "文件正文", "hi" to "फ़ाइल सामग्री", "ar" to "محتوى الملف"),
        "nint.filename.ph" to mapOf("en" to "e.g. w2.pdf", "es" to "p. ej. w2.pdf", "fr" to "ex. w2.pdf", "de" to "z. B. w2.pdf", "pt" to "p. ex. w2.pdf", "it" to "es. w2.pdf", "ja" to "例：w2.pdf", "zh" to "例如：w2.pdf", "hi" to "उदा. w2.pdf", "ar" to "مثال: w2.pdf"),
        "nint.go" to mapOf("en" to "Submit into the newest open intake", "es" to "Entregar en la recepción abierta más reciente", "fr" to "Déposer dans la dernière collecte ouverte", "de" to "In die neueste offene Annahme einreichen", "pt" to "Entregar na receção aberta mais recente", "it" to "Invia all'ultima raccolta aperta", "ja" to "最新の受付に提出", "zh" to "提交至最新的开放受理", "hi" to "नवीनतम खुले इनटेक में जमा करें", "ar" to "الإرسال إلى أحدث استلام مفتوح"),
        "nint.token" to mapOf("en" to "Submit token", "es" to "Token de entrega", "fr" to "Jeton de dépôt", "de" to "Einreichungs-Token", "pt" to "Token de entrega", "it" to "Token di invio", "ja" to "提出トークン", "zh" to "提交令牌", "hi" to "सबमिट टोकन", "ar" to "رمز التسليم"),
        "nint.token.ph" to mapOf("en" to "intk token", "es" to "token intk", "fr" to "jeton intk", "de" to "intk-Token", "pt" to "token intk", "it" to "token intk", "ja" to "intk トークン", "zh" to "intk 令牌", "hi" to "intk टोकन", "ar" to "رمز intk"),
        "nrec.key" to mapOf("en" to "Key", "es" to "Clave", "fr" to "Clé", "de" to "Schlüssel", "pt" to "Chave", "it" to "Chiave", "ja" to "キー", "zh" to "键名", "hi" to "कुंजी", "ar" to "المفتاح"),
        "nrec.key.ph" to mapOf("en" to "e.g. ssn", "es" to "p. ej. ssn", "fr" to "ex. ssn", "de" to "z. B. ssn", "pt" to "p. ex. ssn", "it" to "es. ssn", "ja" to "例：ssn", "zh" to "例如：ssn", "hi" to "उदा. ssn", "ar" to "مثال: ssn"),
        "nrec.seal" to mapOf("en" to "Seal record", "es" to "Sellar el registro", "fr" to "Sceller l'enregistrement", "de" to "Datensatz versiegeln", "pt" to "Selar o registo", "it" to "Sigilla il record", "ja" to "レコードを封印", "zh" to "封存记录", "hi" to "रिकॉर्ड सील करें", "ar" to "ختم السجل"),
        "nrec.t.records" to mapOf("en" to "Records", "es" to "Registros", "fr" to "Enregistrements", "de" to "Datensätze", "pt" to "Registos", "it" to "Record", "ja" to "レコード", "zh" to "记录", "hi" to "रिकॉर्ड", "ar" to "السجلات"),
        "nrec.value" to mapOf("en" to "Value", "es" to "Valor", "fr" to "Valeur", "de" to "Wert", "pt" to "Valor", "it" to "Valore", "ja" to "値", "zh" to "值", "hi" to "मान", "ar" to "القيمة"),
        "nrec.value.ph" to mapOf("en" to "plaintext to seal", "es" to "texto a sellar", "fr" to "texte en clair à sceller", "de" to "zu versiegelnder Klartext", "pt" to "texto a selar", "it" to "testo in chiaro da sigillare", "ja" to "封印する平文", "zh" to "要封存的明文", "hi" to "सील करने हेतु सादा पाठ", "ar" to "نص للختم"),
        "nreq.from" to mapOf("en" to "From", "es" to "De", "fr" to "De", "de" to "Von", "pt" to "De", "it" to "Da", "ja" to "送信元", "zh" to "来自", "hi" to "से", "ar" to "من"),
        "nreq.from.ph" to mapOf("en" to "who should send it", "es" to "quién debe enviarlo", "fr" to "qui doit l'envoyer", "de" to "wer es senden soll", "pt" to "quem deve enviá-lo", "it" to "chi deve inviarlo", "ja" to "誰が送るべきか", "zh" to "应由谁发送", "hi" to "इसे कौन भेजे", "ar" to "من يرسله"),
        "nreq.go" to mapOf("en" to "Request file", "es" to "Solicitar archivo", "fr" to "Demander le fichier", "de" to "Datei anfordern", "pt" to "Solicitar ficheiro", "it" to "Richiedi il file", "ja" to "ファイルを依頼", "zh" to "请求文件", "hi" to "फ़ाइल का अनुरोध करें", "ar" to "طلب ملف"),
        "nreq.purpose" to mapOf("en" to "Purpose (optional)", "es" to "Motivo (opcional)", "fr" to "Objet (facultatif)", "de" to "Zweck (optional)", "pt" to "Finalidade (opcional)", "it" to "Scopo (facoltativo)", "ja" to "目的（任意）", "zh" to "用途（可选）", "hi" to "उद्देश्य (वैकल्पिक)", "ar" to "الغرض (اختياري)"),
        "nreq.purpose.ph" to mapOf("en" to "why you need it", "es" to "por qué lo necesitas", "fr" to "pourquoi vous en avez besoin", "de" to "warum Sie es brauchen", "pt" to "porque precisa dele", "it" to "perché ti serve", "ja" to "なぜ必要か", "zh" to "为什么需要它", "hi" to "आपको इसकी आवश्यकता क्यों है", "ar" to "لماذا تحتاجه"),
        "nrob.bind.go" to mapOf("en" to "Bind", "es" to "Vincular", "fr" to "Associer", "de" to "Verbinden", "pt" to "Vincular", "it" to "Collega", "ja" to "接続", "zh" to "绑定", "hi" to "जोड़ें", "ar" to "ربط"),
        "offline.title" to mapOf("en" to "What this deployment can reach", "es" to "Qué puede alcanzar esta instalación", "fr" to "Ce que ce déploiement peut atteindre", "de" to "Was diese Installation erreichen kann", "pt" to "O que esta instalação pode alcançar", "it" to "Cosa può raggiungere questa installazione", "ja" to "この環境が接続できる範囲", "zh" to "此部署可以连接到什么", "hi" to "यह परिनियोजन किस तक पहुँच सकता है", "ar" to "ما يمكن أن يصل إليه هذا النشر"),
        "offline.on" to mapOf("en" to "Offline — nothing leaves this machine", "es" to "Sin conexión — nada sale de esta máquina", "fr" to "Hors ligne — rien ne quitte cette machine", "de" to "Offline — nichts verlässt diesen Rechner", "pt" to "Offline — nada sai desta máquina", "it" to "Offline — nulla esce da questa macchina", "ja" to "オフライン — このマシンから何も出ません", "zh" to "离线 — 任何内容都不会离开这台机器", "hi" to "ऑफ़लाइन — इस मशीन से कुछ भी बाहर नहीं जाता", "ar" to "دون اتصال — لا شيء يغادر هذا الجهاز"),
        "offline.off" to mapOf("en" to "Online — this deployment can reach other machines", "es" to "En línea — esta instalación puede alcanzar otras máquinas", "fr" to "En ligne — ce déploiement peut atteindre d’autres machines", "de" to "Online — diese Installation kann andere Rechner erreichen", "pt" to "Online — esta instalação pode alcançar outras máquinas", "it" to "Online — questa installazione può raggiungere altre macchine", "ja" to "オンライン — この環境は他のマシンに接続できます", "zh" to "在线 — 此部署可以连接其他机器", "hi" to "ऑनलाइन — यह परिनियोजन अन्य मशीनों तक पहुँच सकता है", "ar" to "متصل — يمكن لهذا النشر الوصول إلى أجهزة أخرى"),
        "wel.title" to mapOf("en" to "Sign in to your vault", "es" to "Entra en tu bóveda", "fr" to "Connectez-vous à votre coffre", "de" to "Melde dich an deinem Tresor an", "pt" to "Entre no seu cofre", "it" to "Accedi alla tua cassaforte", "ja" to "保管庫にサインインする", "zh" to "登录你的保险库", "hi" to "अपने वॉल्ट में साइन इन करें", "ar" to "سجّل الدخول إلى خزنتك"),
        "wel.sub" to mapOf("en" to "Paste the tenant token you were issued. It authorizes every call and never leaves this device unencrypted in transit.", "es" to "Pega el token de inquilino que se te entregó. Autoriza cada llamada y nunca sale de este dispositivo sin cifrar.", "fr" to "Collez le jeton de locataire qui vous a été remis. Il autorise chaque appel et ne quitte jamais cet appareil en clair.", "de" to "Füge das dir ausgestellte Mandanten-Token ein. Es autorisiert jeden Aufruf und verlässt dieses Gerät nie unverschlüsselt.", "pt" to "Cole o token de inquilino que lhe foi entregue. Autoriza cada chamada e nunca sai deste dispositivo sem cifra.", "it" to "Incolla il token del tenant che ti è stato rilasciato. Autorizza ogni chiamata e non lascia mai questo dispositivo in chiaro.", "ja" to "発行されたテナントトークンを貼り付けてください。すべての呼び出しを認可するもので、暗号化されないままこの端末を出ることはありません。", "zh" to "粘贴你收到的租户令牌。它为每一次调用授权，并且绝不会以未加密的形式离开这台设备。", "hi" to "आपको जारी किया गया टेनेंट टोकन यहाँ चिपकाइए। यह हर कॉल को अधिकृत करता है और बिना कूटलेखन के इस डिवाइस से कभी बाहर नहीं जाता।", "ar" to "الصق رمز المستأجر الذي صدر لك. فهو يخوّل كل نداء، ولا يغادر هذا الجهاز غير مُعمّى أبدًا."),
        "wel.token" to mapOf("en" to "Vault token", "es" to "Token de la bóveda", "fr" to "Jeton du coffre", "de" to "Tresor-Token", "pt" to "Token do cofre", "it" to "Token della cassaforte", "ja" to "保管庫のトークン", "zh" to "保险库令牌", "hi" to "वॉल्ट टोकन", "ar" to "رمز الخزنة"),
        "wel.server" to mapOf("en" to "Server", "es" to "Servidor", "fr" to "Serveur", "de" to "Server", "pt" to "Servidor", "it" to "Server", "ja" to "サーバー", "zh" to "服务器", "hi" to "सर्वर", "ar" to "الخادم"),
        "wel.language" to mapOf("en" to "Language", "es" to "Idioma", "fr" to "Langue", "de" to "Sprache", "pt" to "Idioma", "it" to "Lingua", "ja" to "言語", "zh" to "语言", "hi" to "भाषा", "ar" to "اللغة"),
        "wel.unlock" to mapOf("en" to "Unlock", "es" to "Desbloquear", "fr" to "Déverrouiller", "de" to "Entsperren", "pt" to "Desbloquear", "it" to "Sblocca", "ja" to "解錠する", "zh" to "解锁", "hi" to "खोलें", "ar" to "افتح القفل"),
        "wel.backend" to mapOf("en" to "Start the backend:", "es" to "Arranca el servidor:", "fr" to "Démarrez le serveur :", "de" to "Starte das Backend:", "pt" to "Inicie o servidor:", "it" to "Avvia il backend:", "ja" to "バックエンドを起動：", "zh" to "启动后端：", "hi" to "बैकएंड शुरू कीजिए:", "ar" to "شغّل الخادم:"),
        "tab.overview" to mapOf(
            "en" to "Overview", "es" to "Resumen", "fr" to "Aperçu",
            "de" to "Übersicht", "pt" to "Visão geral", "it" to "Panoramica",
            "ja" to "概要", "zh" to "概览", "hi" to "अवलोकन", "ar" to "نظرة عامة"),
        "tab.vault" to mapOf(
            "en" to "Vault", "es" to "Bóveda", "fr" to "Coffre",
            "de" to "Tresor", "pt" to "Cofre", "it" to "Cassaforte",
            "ja" to "保管庫", "zh" to "保险库", "hi" to "वॉल्ट", "ar" to "الخزنة"),
        "tab.audit" to mapOf(
            "en" to "Audit", "es" to "Auditoría", "fr" to "Audit",
            "de" to "Audit", "pt" to "Auditoria", "it" to "Audit",
            "ja" to "監査", "zh" to "审计", "hi" to "ऑडिट", "ar" to "تدقيق"),
        "tab.sources" to mapOf(
            "en" to "Sources", "es" to "Fuentes", "fr" to "Sources",
            "de" to "Quellen", "pt" to "Fontes", "it" to "Fonti",
            "ja" to "ソース", "zh" to "来源", "hi" to "स्रोत", "ar" to "المصادر"),
        "tab.transfers" to mapOf(
            "en" to "Transfers", "es" to "Transferencias", "fr" to "Transferts",
            "de" to "Übertragungen", "pt" to "Transferências", "it" to "Trasferimenti",
            "ja" to "転送", "zh" to "传输", "hi" to "स्थानांतरण", "ar" to "التحويلات"),
        "action.sign_out" to mapOf(
            "en" to "Sign out", "es" to "Cerrar sesión", "fr" to "Se déconnecter",
            "de" to "Abmelden", "pt" to "Sair", "it" to "Esci",
            "ja" to "サインアウト", "zh" to "退出登录", "hi" to "साइन आउट",
            "ar" to "تسجيل الخروج"),
    )
}
