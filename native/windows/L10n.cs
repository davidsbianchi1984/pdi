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
        ["fb.sofar"] = new() { ["en"] = "So far: {list}", ["es"] = "Hasta ahora: {list}", ["fr"] = "Jusqu'ici : {list}", ["de"] = "Bisher: {list}", ["pt"] = "Até agora: {list}", ["it"] = "Finora: {list}", ["ja"] = "これまで：{list}", ["zh"] = "目前：{list}", ["hi"] = "अब तक: {list}", ["ar"] = "حتى الآن: {list}" },
        ["fb.thanks"] = new() { ["en"] = "Thank you — sent.", ["es"] = "Gracias, enviado.", ["fr"] = "Merci — envoyé.", ["de"] = "Danke — gesendet.", ["pt"] = "Obrigado — enviado.", ["it"] = "Grazie — inviato.", ["ja"] = "ありがとうございます — 送信しました。", ["zh"] = "谢谢 — 已发送。", ["hi"] = "धन्यवाद — भेज दिया गया।", ["ar"] = "شكرًا لك — تم الإرسال." },
        ["nadm.rotated"] = new() { ["en"] = "Rotated — every record re-sealed under the new version.", ["es"] = "Rotada: todos los registros se han vuelto a sellar con la nueva versión.", ["fr"] = "Rotation effectuée — tous les enregistrements ont été rescellés sous la nouvelle version.", ["de"] = "Rotiert — jeder Datensatz wurde unter der neuen Version neu versiegelt.", ["pt"] = "Rodada — todos os registos foram novamente selados sob a nova versão.", ["it"] = "Ruotata — ogni record è stato risigillato con la nuova versione.", ["ja"] = "ローテーションしました — すべてのレコードを新しいバージョンで再封印しました。", ["zh"] = "已轮换 — 所有记录已在新版本下重新封存。", ["hi"] = "घुमाई गई — हर रिकॉर्ड नए संस्करण के तहत पुनः सील किया गया।", ["ar"] = "تم التدوير — أُعيد ختم كل سجل بالإصدار الجديد." },
        ["offline.title"] = new() { ["en"] = "What this deployment can reach", ["es"] = "Qué puede alcanzar esta instalación", ["fr"] = "Ce que ce déploiement peut atteindre", ["de"] = "Was diese Installation erreichen kann", ["pt"] = "O que esta instalação pode alcançar", ["it"] = "Cosa può raggiungere questa installazione", ["ja"] = "この環境が接続できる範囲", ["zh"] = "此部署可以连接到什么", ["hi"] = "यह परिनियोजन किस तक पहुँच सकता है", ["ar"] = "ما يمكن أن يصل إليه هذا النشر" },
        ["offline.on"] = new() { ["en"] = "Offline — nothing leaves this machine", ["es"] = "Sin conexión — nada sale de esta máquina", ["fr"] = "Hors ligne — rien ne quitte cette machine", ["de"] = "Offline — nichts verlässt diesen Rechner", ["pt"] = "Offline — nada sai desta máquina", ["it"] = "Offline — nulla esce da questa macchina", ["ja"] = "オフライン — このマシンから何も出ません", ["zh"] = "离线 — 任何内容都不会离开这台机器", ["hi"] = "ऑफ़लाइन — इस मशीन से कुछ भी बाहर नहीं जाता", ["ar"] = "دون اتصال — لا شيء يغادر هذا الجهاز" },
        ["offline.off"] = new() { ["en"] = "Online — this deployment can reach other machines", ["es"] = "En línea — esta instalación puede alcanzar otras máquinas", ["fr"] = "En ligne — ce déploiement peut atteindre d’autres machines", ["de"] = "Online — diese Installation kann andere Rechner erreichen", ["pt"] = "Online — esta instalação pode alcançar outras máquinas", ["it"] = "Online — questa installazione può raggiungere altre macchine", ["ja"] = "オンライン — この環境は他のマシンに接続できます", ["zh"] = "在线 — 此部署可以连接其他机器", ["hi"] = "ऑनलाइन — यह परिनियोजन अन्य मशीनों तक पहुँच सकता है", ["ar"] = "متصل — يمكن لهذا النشر الوصول إلى أجهزة أخرى" },
        ["prb.can"] = new() { ["en"] = "This app can send a count of what failed — the operation and the HTTP status, the day, and how many times. Not what you typed, not who you are, not which profile. Nothing that identifies you or anyone else.", ["es"] = "Esta aplicación puede enviar un recuento de lo que falló: la operación y el estado HTTP, el día y cuántas veces. No lo que escribiste, ni quién eres, ni qué inquilino. Nada que te identifique a ti ni a nadie.", ["fr"] = "Cette application peut envoyer un décompte des échecs : l'opération et le statut HTTP, le jour et le nombre de fois. Pas ce que vous avez saisi, ni qui vous êtes, ni quel locataire. Rien qui vous identifie, ni personne d'autre.", ["de"] = "Diese App kann eine Anzahl der Fehler senden — den Vorgang und den HTTP-Status, den Tag und wie oft. Nicht, was Sie eingegeben haben, nicht, wer Sie sind, nicht welcher Mandant. Nichts, was Sie oder jemand anderen identifiziert.", ["pt"] = "Esta aplicação pode enviar uma contagem do que falhou — a operação e o estado HTTP, o dia e quantas vezes. Não o que escreveu, nem quem é, nem que inquilino. Nada que o identifique a si ou a outra pessoa.", ["it"] = "Questa app può inviare un conteggio degli errori — l'operazione e lo stato HTTP, il giorno e quante volte. Non ciò che hai digitato, non chi sei, non quale tenant. Nulla che identifichi te o chiunque altro.", ["ja"] = "このアプリは失敗の件数を送信できます — 操作と HTTP ステータス、日付、回数です。入力した内容、あなたが誰か、どのテナントかは送りません。あなたや他の誰かを特定するものは何もありません。", ["zh"] = "此应用可以发送失败计数 — 操作与 HTTP 状态、日期以及次数。不包括你输入的内容、你是谁、或哪个租户。没有任何能识别你或他人的信息。", ["hi"] = "यह ऐप विफलताओं की गिनती भेज सकता है — कार्रवाई और HTTP स्थिति, दिन, और कितनी बार। आपने क्या टाइप किया, आप कौन हैं, कौन-सा टेनेंट — कुछ नहीं। ऐसा कुछ भी नहीं जो आपकी या किसी और की पहचान करे।", ["ar"] = "يمكن لهذا التطبيق إرسال عدد ما فشل — العملية وحالة HTTP واليوم وعدد المرات. لا ما كتبته، ولا من أنت، ولا أي مستأجر. لا شيء يعرّفك أو يعرّف أي شخص آخر." },
        ["prb.hide"] = new() { ["en"] = "Hide what would be sent", ["es"] = "Ocultar qué se enviaría", ["fr"] = "Masquer ce qui serait envoyé", ["de"] = "Ausblenden, was gesendet würde", ["pt"] = "Ocultar o que seria enviado", ["it"] = "Nascondi cosa verrebbe inviato", ["ja"] = "送信される内容を隠す", ["zh"] = "隐藏将要发送的内容", ["hi"] = "छिपाएँ क्या भेजा जाएगा", ["ar"] = "إخفاء ما سيُرسَل" },
        ["prb.never"] = new() { ["en"] = "Counts of what failed. Never what you typed.", ["es"] = "Recuentos de lo que falló. Nunca lo que escribiste.", ["fr"] = "Des décomptes d'échecs. Jamais ce que vous avez saisi.", ["de"] = "Anzahl der Fehler. Nie, was Sie eingegeben haben.", ["pt"] = "Contagens do que falhou. Nunca o que escreveu.", ["it"] = "Conteggi degli errori. Mai ciò che hai digitato.", ["ja"] = "失敗した件数だけ。入力した内容は決して送りません。", ["zh"] = "仅统计失败次数。绝不包含你输入的内容。", ["hi"] = "केवल विफलताओं की गिनती। आपने जो लिखा वह कभी नहीं।", ["ar"] = "أعداد ما فشل فقط. أبدًا ما كتبته." },
        ["prb.nowhere"] = new() { ["en"] = "This build reports nowhere. Failures are counted on this machine and never leave it.", ["es"] = "Esta compilación no informa a ninguna parte. Los fallos se cuentan en este equipo y nunca salen de él.", ["fr"] = "Cette version ne signale rien à personne. Les échecs sont comptés sur cette machine et n'en sortent jamais.", ["de"] = "Dieser Build meldet nirgendwohin. Fehler werden auf diesem Gerät gezählt und verlassen es nie.", ["pt"] = "Esta compilação não reporta a lado nenhum. As falhas são contadas nesta máquina e nunca saem dela.", ["it"] = "Questa build non segnala da nessuna parte. Gli errori sono contati su questa macchina e non la lasciano mai.", ["ja"] = "このビルドはどこにも報告しません。障害はこの端末で数えられ、外に出ることはありません。", ["zh"] = "此版本不向任何地方报告。故障只在本机计数，绝不外传。", ["hi"] = "यह बिल्ड कहीं रिपोर्ट नहीं करता। विफलताएँ इसी मशीन पर गिनी जाती हैं और कभी बाहर नहीं जातीं।", ["ar"] = "لا يُبلّغ هذا الإصدار أي جهة. تُحصى الأعطال على هذا الجهاز ولا تغادره أبدًا." },
        ["prb.show"] = new() { ["en"] = "Show what would be sent", ["es"] = "Ver qué se enviaría", ["fr"] = "Voir ce qui serait envoyé", ["de"] = "Anzeigen, was gesendet würde", ["pt"] = "Ver o que seria enviado", ["it"] = "Mostra cosa verrebbe inviato", ["ja"] = "送信される内容を表示", ["zh"] = "查看将要发送的内容", ["hi"] = "देखें क्या भेजा जाएगा", ["ar"] = "إظهار ما سيُرسَل" },
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
