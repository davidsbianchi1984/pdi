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
    public static string T(string key)
    {
        var lang = AppState.Current.Language;
        if (Table.TryGetValue(key, out var row))
            return row.TryGetValue(lang, out var s) ? s
                 : row.TryGetValue("en", out var en) ? en : key;
        return key;
    }

    private static readonly Dictionary<string, Dictionary<string, string>> Table = new()
    {
        ["tab.overview"] = new() { ["en"] = "Overview", ["es"] = "Resumen", ["fr"] = "Aperçu", ["de"] = "Übersicht", ["pt"] = "Visão geral", ["it"] = "Panoramica", ["ja"] = "概要", ["zh"] = "概览", ["hi"] = "अवलोकन", ["ar"] = "نظرة عامة" },
        ["tab.vault"] = new() { ["en"] = "Vault", ["es"] = "Bóveda", ["fr"] = "Coffre", ["de"] = "Tresor", ["pt"] = "Cofre", ["it"] = "Cassaforte", ["ja"] = "保管庫", ["zh"] = "保险库", ["hi"] = "वॉल्ट", ["ar"] = "الخزنة" },
        ["tab.audit"] = new() { ["en"] = "Audit", ["es"] = "Auditoría", ["fr"] = "Audit", ["de"] = "Audit", ["pt"] = "Auditoria", ["it"] = "Audit", ["ja"] = "監査", ["zh"] = "审计", ["hi"] = "ऑडिट", ["ar"] = "تدقيق" },
        ["tab.robots"] = new() { ["en"] = "Robots", ["es"] = "Robots", ["fr"] = "Robots", ["de"] = "Roboter", ["pt"] = "Robôs", ["it"] = "Robot", ["ja"] = "ロボット", ["zh"] = "机器人", ["hi"] = "रोबोट", ["ar"] = "روبوتات" },
        ["tab.connectors"] = new() { ["en"] = "Connectors", ["es"] = "Conectores", ["fr"] = "Connecteurs", ["de"] = "Konnektoren", ["pt"] = "Conectores", ["it"] = "Connettori", ["ja"] = "コネクタ", ["zh"] = "连接器", ["hi"] = "कनेक्टर", ["ar"] = "الموصلات" },
        ["tab.transfers"] = new() { ["en"] = "Transfers", ["es"] = "Transferencias", ["fr"] = "Transferts", ["de"] = "Übertragungen", ["pt"] = "Transferências", ["it"] = "Trasferimenti", ["ja"] = "転送", ["zh"] = "传输", ["hi"] = "स्थानांतरण", ["ar"] = "التحويلات" },
        ["action.save"] = new() { ["en"] = "Save", ["es"] = "Guardar", ["fr"] = "Enregistrer", ["de"] = "Speichern", ["pt"] = "Salvar", ["it"] = "Salva", ["ja"] = "保存", ["zh"] = "保存", ["hi"] = "सहेजें", ["ar"] = "حفظ" },
        ["action.refresh"] = new() { ["en"] = "Refresh", ["es"] = "Actualizar", ["fr"] = "Actualiser", ["de"] = "Aktualisieren", ["pt"] = "Atualizar", ["it"] = "Aggiorna", ["ja"] = "更新", ["zh"] = "刷新", ["hi"] = "रीफ़्रेश", ["ar"] = "تحديث" },
    };
}
