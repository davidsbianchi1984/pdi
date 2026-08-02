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
        "offline.title" to mapOf("en" to "What this deployment can reach", "es" to "Qué puede alcanzar esta instalación", "fr" to "Ce que ce déploiement peut atteindre", "de" to "Was diese Installation erreichen kann", "pt" to "O que esta instalação pode alcançar", "it" to "Cosa può raggiungere questa installazione", "ja" to "この環境が接続できる範囲", "zh" to "此部署可以连接到什么", "hi" to "यह परिनियोजन किस तक पहुँच सकता है", "ar" to "ما يمكن أن يصل إليه هذا النشر"),
        "offline.on" to mapOf("en" to "Offline — nothing leaves this machine", "es" to "Sin conexión — nada sale de esta máquina", "fr" to "Hors ligne — rien ne quitte cette machine", "de" to "Offline — nichts verlässt diesen Rechner", "pt" to "Offline — nada sai desta máquina", "it" to "Offline — nulla esce da questa macchina", "ja" to "オフライン — このマシンから何も出ません", "zh" to "离线 — 任何内容都不会离开这台机器", "hi" to "ऑफ़लाइन — इस मशीन से कुछ भी बाहर नहीं जाता", "ar" to "دون اتصال — لا شيء يغادر هذا الجهاز"),
        "offline.off" to mapOf("en" to "Online — this deployment can reach other machines", "es" to "En línea — esta instalación puede alcanzar otras máquinas", "fr" to "En ligne — ce déploiement peut atteindre d’autres machines", "de" to "Online — diese Installation kann andere Rechner erreichen", "pt" to "Online — esta instalação pode alcançar outras máquinas", "it" to "Online — questa installazione può raggiungere altre macchine", "ja" to "オンライン — この環境は他のマシンに接続できます", "zh" to "在线 — 此部署可以连接其他机器", "hi" to "ऑनलाइन — यह परिनियोजन अन्य मशीनों तक पहुँच सकता है", "ar" to "متصل — يمكن لهذا النشر الوصول إلى أجهزة أخرى"),
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
