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
        "offline.title": ["en": "What this deployment can reach", "es": "Qué puede alcanzar esta instalación", "fr": "Ce que ce déploiement peut atteindre", "de": "Was diese Installation erreichen kann", "pt": "O que esta instalação pode alcançar", "it": "Cosa può raggiungere questa installazione", "ja": "この環境が接続できる範囲", "zh": "此部署可以连接到什么", "hi": "यह परिनियोजन किस तक पहुँच सकता है", "ar": "ما يمكن أن يصل إليه هذا النشر"],
        "offline.on": ["en": "Offline — nothing leaves this machine", "es": "Sin conexión — nada sale de esta máquina", "fr": "Hors ligne — rien ne quitte cette machine", "de": "Offline — nichts verlässt diesen Rechner", "pt": "Offline — nada sai desta máquina", "it": "Offline — nulla esce da questa macchina", "ja": "オフライン — このマシンから何も出ません", "zh": "离线 — 任何内容都不会离开这台机器", "hi": "ऑफ़लाइन — इस मशीन से कुछ भी बाहर नहीं जाता", "ar": "دون اتصال — لا شيء يغادر هذا الجهاز"],
        "offline.off": ["en": "Online — this deployment can reach other machines", "es": "En línea — esta instalación puede alcanzar otras máquinas", "fr": "En ligne — ce déploiement peut atteindre d’autres machines", "de": "Online — diese Installation kann andere Rechner erreichen", "pt": "Online — esta instalação pode alcançar outras máquinas", "it": "Online — questa installazione può raggiungere altre macchine", "ja": "オンライン — この環境は他のマシンに接続できます", "zh": "在线 — 此部署可以连接其他机器", "hi": "ऑनलाइन — यह परिनियोजन अन्य मशीनों तक पहुँच सकता है", "ar": "متصل — يمكن لهذا النشر الوصول إلى أجهزة أخرى"],
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
        "action.save": ["en": "Save", "es": "Guardar", "fr": "Enregistrer",
                        "de": "Speichern", "pt": "Salvar", "it": "Salva",
                        "ja": "保存", "zh": "保存", "hi": "सहेजें", "ar": "حفظ"],
        "action.sign_out": ["en": "Sign out", "es": "Cerrar sesión", "fr": "Se déconnecter",
                            "de": "Abmelden", "pt": "Sair", "it": "Esci",
                            "ja": "サインアウト", "zh": "退出登录", "hi": "साइन आउट",
                            "ar": "تسجيل الخروج"],
        "action.refresh": ["en": "Refresh", "es": "Actualizar", "fr": "Actualiser",
                           "de": "Aktualisieren", "pt": "Atualizar", "it": "Aggiorna",
                           "ja": "更新", "zh": "刷新", "hi": "रीफ़्रेश", "ar": "تحديث"],
    ]
}
