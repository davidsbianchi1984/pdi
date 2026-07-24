import Foundation

/// App-chrome localization: tab names and the most common actions, in every
/// language the backend supports. PDI's explanatory notes are localized
/// server-side by the tenant's language setting; this table covers the frame
/// around them. Missing keys fall back to English.
enum L10n {
    static func t(_ key: String, _ lang: String) -> String {
        table[key]?[lang] ?? table[key]?["en"] ?? key
    }

    private static let table: [String: [String: String]] = [
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
