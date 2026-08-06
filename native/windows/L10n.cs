using System.Collections.Generic;

namespace PdiVault;

/// <summary>
/// App-chrome localization: nav names and the most common actions, in every
/// language the backend supports. PDI's explanatory notes are localized
/// server-side by the tenant's language setting; this table covers the frame
/// around them. Missing keys fall back to English.
/// </summary>
public static class L10n
{
    /// <summary>
    /// The language of somebody who has no account to take one from.
    ///
    /// <para><c>AppState.Language</c> is the stored setting and is "en" until
    /// an account exists. Every sentence the backend composes on a public
    /// route is chosen from <c>Accept-Language</c>, and this shell was sending
    /// no such header — Windows has been carrying the answer in
    /// CurrentUICulture the whole time.</para>
    ///
    /// <para>Region dropped; anything this app does not carry falls back to
    /// English rather than guessing.</para>
    /// </summary>
    public static readonly string[] Supported =
        { "en", "es", "fr", "de", "pt", "it", "ja", "zh", "hi", "ar" };

    public static string DeviceLanguage()
    {
        var culture = System.Globalization.CultureInfo.CurrentUICulture;
        while (culture != null && !string.IsNullOrEmpty(culture.Name))
        {
            var code = culture.TwoLetterISOLanguageName.ToLowerInvariant();
            if (System.Array.IndexOf(Supported, code) >= 0) return code;
            culture = culture.Parent;
        }
        return "en";
    }

    /// <summary>The shell's chrome, in the signed-in account's language.
    ///
    /// <para>Convenient and, on a public surface, wrong: the language it
    /// reaches for is <c>AppState.Current.Language</c>. A reader with no
    /// account is answered in English no matter what their machine is set to,
    /// and does it without the screen ever naming the setting. iOS and Android
    /// cannot make that mistake — both of their <c>t</c> functions require the
    /// language as an argument.</para></summary>
    public static string T(string key) => T(key, AppState.Current.Language);

    /// <summary>The same table, asked in a language the caller names. Pass
    /// <c>DeviceLanguage()</c> on any surface whose reader has no
    /// account.</summary>
    public static string T(string key, string lang)
    {
        if (Table.TryGetValue(key, out var row))
            return row.TryGetValue(lang, out var s) ? s
                 : row.TryGetValue("en", out var en) ? en : key;
        return key;
    }

    private static readonly Dictionary<string, Dictionary<string, string>> Table = new()
    {
        ["offline.title"] = new() { ["en"] = "What this deployment can reach", ["es"] = "Qué puede alcanzar esta instalación", ["fr"] = "Ce que ce déploiement peut atteindre", ["de"] = "Was diese Installation erreichen kann", ["pt"] = "O que esta instalação pode alcançar", ["it"] = "Cosa può raggiungere questa installazione", ["ja"] = "この環境が接続できる範囲", ["zh"] = "此部署可以连接到什么", ["hi"] = "यह परिनियोजन किस तक पहुँच सकता है", ["ar"] = "ما يمكن أن يصل إليه هذا النشر" },
        ["offline.on"] = new() { ["en"] = "Offline — nothing leaves this machine", ["es"] = "Sin conexión — nada sale de esta máquina", ["fr"] = "Hors ligne — rien ne quitte cette machine", ["de"] = "Offline — nichts verlässt diesen Rechner", ["pt"] = "Offline — nada sai desta máquina", ["it"] = "Offline — nulla esce da questa macchina", ["ja"] = "オフライン — このマシンから何も出ません", ["zh"] = "离线 — 任何内容都不会离开这台机器", ["hi"] = "ऑफ़लाइन — इस मशीन से कुछ भी बाहर नहीं जाता", ["ar"] = "دون اتصال — لا شيء يغادر هذا الجهاز" },
        ["offline.off"] = new() { ["en"] = "Online — this deployment can reach other machines", ["es"] = "En línea — esta instalación puede alcanzar otras máquinas", ["fr"] = "En ligne — ce déploiement peut atteindre d’autres machines", ["de"] = "Online — diese Installation kann andere Rechner erreichen", ["pt"] = "Online — esta instalação pode alcançar outras máquinas", ["it"] = "Online — questa installazione può raggiungere altre macchine", ["ja"] = "オンライン — この環境は他のマシンに接続できます", ["zh"] = "在线 — 此部署可以连接其他机器", ["hi"] = "ऑनलाइन — यह परिनियोजन अन्य मशीनों तक पहुँच सकता है", ["ar"] = "متصل — يمكن لهذا النشر الوصول إلى أجهزة أخرى" },
        ["wel.title"] = new() { ["en"] = "Sign in to your vault", ["es"] = "Entra en tu bóveda", ["fr"] = "Connectez-vous à votre coffre", ["de"] = "Melde dich an deinem Tresor an", ["pt"] = "Entre no seu cofre", ["it"] = "Accedi alla tua cassaforte", ["ja"] = "保管庫にサインインする", ["zh"] = "登录你的保险库", ["hi"] = "अपने वॉल्ट में साइन इन करें", ["ar"] = "سجّل الدخول إلى خزنتك" },
        ["wel.sub"] = new() { ["en"] = "Paste the tenant token you were issued. It authorizes every call and never leaves this device unencrypted in transit.", ["es"] = "Pega el token de inquilino que se te entregó. Autoriza cada llamada y nunca sale de este dispositivo sin cifrar.", ["fr"] = "Collez le jeton de locataire qui vous a été remis. Il autorise chaque appel et ne quitte jamais cet appareil en clair.", ["de"] = "Füge das dir ausgestellte Mandanten-Token ein. Es autorisiert jeden Aufruf und verlässt dieses Gerät nie unverschlüsselt.", ["pt"] = "Cole o token de inquilino que lhe foi entregue. Autoriza cada chamada e nunca sai deste dispositivo sem cifra.", ["it"] = "Incolla il token del tenant che ti è stato rilasciato. Autorizza ogni chiamata e non lascia mai questo dispositivo in chiaro.", ["ja"] = "発行されたテナントトークンを貼り付けてください。すべての呼び出しを認可するもので、暗号化されないままこの端末を出ることはありません。", ["zh"] = "粘贴你收到的租户令牌。它为每一次调用授权，并且绝不会以未加密的形式离开这台设备。", ["hi"] = "आपको जारी किया गया टेनेंट टोकन यहाँ चिपकाइए। यह हर कॉल को अधिकृत करता है और बिना कूटलेखन के इस डिवाइस से कभी बाहर नहीं जाता।", ["ar"] = "الصق رمز المستأجر الذي صدر لك. فهو يخوّل كل نداء، ولا يغادر هذا الجهاز غير مُعمّى أبدًا." },
        ["wel.token"] = new() { ["en"] = "Vault token", ["es"] = "Token de la bóveda", ["fr"] = "Jeton du coffre", ["de"] = "Tresor-Token", ["pt"] = "Token do cofre", ["it"] = "Token della cassaforte", ["ja"] = "保管庫のトークン", ["zh"] = "保险库令牌", ["hi"] = "वॉल्ट टोकन", ["ar"] = "رمز الخزنة" },
        ["wel.server"] = new() { ["en"] = "Server", ["es"] = "Servidor", ["fr"] = "Serveur", ["de"] = "Server", ["pt"] = "Servidor", ["it"] = "Server", ["ja"] = "サーバー", ["zh"] = "服务器", ["hi"] = "सर्वर", ["ar"] = "الخادم" },
        ["wel.language"] = new() { ["en"] = "Language", ["es"] = "Idioma", ["fr"] = "Langue", ["de"] = "Sprache", ["pt"] = "Idioma", ["it"] = "Lingua", ["ja"] = "言語", ["zh"] = "语言", ["hi"] = "भाषा", ["ar"] = "اللغة" },
        ["wel.unlock"] = new() { ["en"] = "Unlock", ["es"] = "Desbloquear", ["fr"] = "Déverrouiller", ["de"] = "Entsperren", ["pt"] = "Desbloquear", ["it"] = "Sblocca", ["ja"] = "解錠する", ["zh"] = "解锁", ["hi"] = "खोलें", ["ar"] = "افتح القفل" },
        ["wel.backend"] = new() { ["en"] = "Start the backend:", ["es"] = "Arranca el servidor:", ["fr"] = "Démarrez le serveur :", ["de"] = "Starte das Backend:", ["pt"] = "Inicie o servidor:", ["it"] = "Avvia il backend:", ["ja"] = "バックエンドを起動：", ["zh"] = "启动后端：", ["hi"] = "बैकएंड शुरू कीजिए:", ["ar"] = "شغّل الخادم:" },
        ["action.sign_out"] = new() { ["en"] = "Sign out", ["es"] = "Cerrar sesión", ["fr"] = "Se déconnecter", ["de"] = "Abmelden", ["pt"] = "Sair", ["it"] = "Esci", ["ja"] = "サインアウト", ["zh"] = "退出登录", ["hi"] = "साइन आउट", ["ar"] = "تسجيل الخروج" },
        ["tab.overview"] = new() { ["en"] = "Overview", ["es"] = "Resumen", ["fr"] = "Aperçu", ["de"] = "Übersicht", ["pt"] = "Visão geral", ["it"] = "Panoramica", ["ja"] = "概要", ["zh"] = "概览", ["hi"] = "अवलोकन", ["ar"] = "نظرة عامة" },
        ["tab.vault"] = new() { ["en"] = "Vault", ["es"] = "Bóveda", ["fr"] = "Coffre", ["de"] = "Tresor", ["pt"] = "Cofre", ["it"] = "Cassaforte", ["ja"] = "保管庫", ["zh"] = "保险库", ["hi"] = "वॉल्ट", ["ar"] = "الخزنة" },
        ["tab.audit"] = new() { ["en"] = "Audit", ["es"] = "Auditoría", ["fr"] = "Audit", ["de"] = "Audit", ["pt"] = "Auditoria", ["it"] = "Audit", ["ja"] = "監査", ["zh"] = "审计", ["hi"] = "ऑडिट", ["ar"] = "تدقيق" },
        ["tab.robots"] = new() { ["en"] = "Robots", ["es"] = "Robots", ["fr"] = "Robots", ["de"] = "Roboter", ["pt"] = "Robôs", ["it"] = "Robot", ["ja"] = "ロボット", ["zh"] = "机器人", ["hi"] = "रोबोट", ["ar"] = "روبوتات" },
        ["tab.connectors"] = new() { ["en"] = "Connectors", ["es"] = "Conectores", ["fr"] = "Connecteurs", ["de"] = "Konnektoren", ["pt"] = "Conectores", ["it"] = "Connettori", ["ja"] = "コネクタ", ["zh"] = "连接器", ["hi"] = "कनेक्टर", ["ar"] = "الموصلات" },
        ["tab.transfers"] = new() { ["en"] = "Transfers", ["es"] = "Transferencias", ["fr"] = "Transferts", ["de"] = "Übertragungen", ["pt"] = "Transferências", ["it"] = "Trasferimenti", ["ja"] = "転送", ["zh"] = "传输", ["hi"] = "स्थानांतरण", ["ar"] = "التحويلات" },
        ["action.refresh"] = new() { ["en"] = "Refresh", ["es"] = "Actualizar", ["fr"] = "Actualiser", ["de"] = "Aktualisieren", ["pt"] = "Atualizar", ["it"] = "Aggiorna", ["ja"] = "更新", ["zh"] = "刷新", ["hi"] = "रीफ़्रेश", ["ar"] = "تحديث" },
    };
}
