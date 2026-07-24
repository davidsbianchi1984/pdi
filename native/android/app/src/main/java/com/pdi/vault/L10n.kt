package com.pdi.vault

/**
 * App-chrome localization: tab names and the most common actions, in every
 * language the backend supports. PDI's explanatory notes are localized
 * server-side by the tenant's language setting; this table covers the frame
 * around them. Missing keys fall back to English.
 */
object L10n {
    fun t(key: String, lang: String): String =
        table[key]?.let { it[lang] ?: it["en"] } ?: key

    private val table: Map<String, Map<String, String>> = mapOf(
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
        "action.save" to mapOf(
            "en" to "Save", "es" to "Guardar", "fr" to "Enregistrer",
            "de" to "Speichern", "pt" to "Salvar", "it" to "Salva",
            "ja" to "保存", "zh" to "保存", "hi" to "सहेजें", "ar" to "حفظ"),
        "action.sign_out" to mapOf(
            "en" to "Sign out", "es" to "Cerrar sesión", "fr" to "Se déconnecter",
            "de" to "Abmelden", "pt" to "Sair", "it" to "Esci",
            "ja" to "サインアウト", "zh" to "退出登录", "hi" to "साइन आउट",
            "ar" to "تسجيل الخروج"),
        "action.refresh" to mapOf(
            "en" to "Refresh", "es" to "Actualizar", "fr" to "Actualiser",
            "de" to "Aktualisieren", "pt" to "Atualizar", "it" to "Aggiorna",
            "ja" to "更新", "zh" to "刷新", "hi" to "रीफ़्रेश", "ar" to "تحديث"),
    )
}
