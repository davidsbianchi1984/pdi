using System;
using System.Linq;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;
using Microsoft.UI.Xaml;

namespace PdiVault.Views;

public sealed partial class OverviewPage : Page
{
    public record ImproveRow(string Line);

    private static readonly string[] ImproveCategories =
        { "idea", "improvement", "bug", "praise", "other" };

    private LanguageInfo[] _languages = System.Array.Empty<LanguageInfo>();
    private bool _loadingLanguage;

    public OverviewPage()
    {
        InitializeComponent();
        LanguageHead.Text = L10n.T("wel.language");
        // `action.refresh` has been in the table, translated into ten
        // languages, since chrome localization landed — and the only
        // Refresh button in this shell was hardcoded English.
        RefreshButton.Content = L10n.T("action.refresh");
        ImproveCategory.ItemsSource = ImproveCategories
            .Select(c => char.ToUpper(c[0]) + c[1..]).ToList();
        ImproveCategory.SelectedIndex = 0;
        ImproveRating.ItemsSource = new[] { "—", "1", "2", "3", "4", "5" };
        ImproveRating.SelectedIndex = 0;
        AccHead.Text = L10n.T("ns.acc");
        AccLead.Text = L10n.T("ns.acc.lead");
        AccDoing.PlaceholderText = L10n.T("ns.acc.doing.ph");
        AccWall.PlaceholderText = L10n.T("ns.acc.wall.ph");
        AccHelp.PlaceholderText = L10n.T("ns.acc.help.ph");
        AccSend.Content = L10n.T("ns.acc.send");
        AccReviewerBox.PlaceholderText = L10n.T("ns.acc.token.ph");
        AccLoad.Content = L10n.T("ns.acc.load");
        AccEmpty.Text = L10n.T("ns.acc.none");
    }

    // The accessibility door: tokenless on purpose — reporting that the
    // vault shut you out must not require the tenant token it may have
    // shut you out of.
    private async void OnSendAccessReport(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        var doing = AccDoing.Text.Trim();
        var wall = AccWall.Text.Trim();
        if (doing.Length == 0 || wall.Length == 0) return;
        try
        {
            await ApiClient.Shared.SendAccessReport(
                doing, wall, AccHelp.Text.Trim(), AppState.Current.Language);
            AccDoing.Text = ""; AccWall.Text = ""; AccHelp.Text = "";
            AccThanks.Text = L10n.T("ns.acc.sent");
            AccThanks.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
        }
        catch (System.Exception ex)
        {
            AccThanks.Text = ex.Message;
            AccThanks.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
        }
    }

    private async void OnLoadAccessReports(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        try
        {
            var st = await ApiClient.Shared.AccessReports(AccReviewerBox.Password.Trim());
            AccEmpty.Visibility = st.Total == 0
                ? Microsoft.UI.Xaml.Visibility.Visible
                : Microsoft.UI.Xaml.Visibility.Collapsed;
            AccReportsList.ItemsSource = st.Reports.Take(6).Select(r => new ImproveRow(
                $"{r.Doing} — {r.Wall}"
                + (r.Help is { Length: > 0 } h ? $" ({h})" : "")
                + $" · {r.Lang} · {r.CreatedAt}")).ToList();
        }
        catch (System.Exception ex)
        {
            AccThanks.Text = ex.Message;
            AccThanks.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
        }
    }

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
        RefreshButton.Content = L10n.T("action.refresh");
        await Load();
    }

    private async void OnRefresh(object sender, Microsoft.UI.Xaml.RoutedEventArgs e) =>
        await Load();

    /// The posture the deployment can show an auditor. Its own try/catch:
    /// a vault that cannot answer must not blank the offline card, which is
    /// about a different question entirely.
    private async System.Threading.Tasks.Task LoadOfflinePosture()
    {
        try
        {
            var p = await ApiClient.Shared.OfflineStatus();
            OfflineTitle.Text = L10n.T("offline.title");
            OfflineState.Text = p.Offline ? L10n.T("offline.on") : L10n.T("offline.off");
            OfflineLocal.Text = p.LocalDestinationsAllowed;
            OfflineGuarantees.Text = string.Join("\n", Array.ConvertAll(
                p.Guarantees ?? Array.Empty<string>(), g => "\u2022 " + g));
            OfflineCard.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
        }
        catch (Exception)
        {
            OfflineCard.Visibility = Microsoft.UI.Xaml.Visibility.Collapsed;
        }
    }

    private async System.Threading.Tasks.Task Load()
    {
        await LoadOfflinePosture();
        var s = AppState.Current;
        ApiClient.Shared.SetBase(s.BaseUrl);
        TokenText.Text = Masked(s.Token ?? "");
        BaseText.Text = s.BaseUrl;
        try
        {
            var keys = await ApiClient.Shared.Keys(s.Token!);
            RecordsValue.Text = keys.Length.ToString();
        }
        catch { RecordsValue.Text = "—"; }
        try
        {
            var v = await ApiClient.Shared.AuditVerify(s.Token!);
            AuditValue.Text = v.Intact ? "Intact" : "Broken";
        }
        catch { AuditValue.Text = "—"; }
        try
        {
            _loadingLanguage = true;
            _languages = (await ApiClient.Shared.Languages(s.Token!)).Languages;
            LanguageBox.ItemsSource = _languages.Select(l =>
                l.Label + (l.NotesTranslated ? "" : "  (notes in English)")).ToList();
            var current = await ApiClient.Shared.Language(s.Token!);
            var idx = System.Array.FindIndex(_languages, l => l.Code == current.Language);
            LanguageBox.SelectedIndex = idx >= 0 ? idx : 0;
            PreTranslateToggle.IsOn = (current.Mode ?? "pre") == "pre";
            s.RememberLanguage(current.Language);   // chrome follows the tenant
        }
        catch { /* backend offline — leave empty */ }
        finally { _loadingLanguage = false; }

        await LoadImprovements();
    }

    private async System.Threading.Tasks.Task LoadImprovements()
    {
        try
        {
            var st = await ApiClient.Shared.Improvements(AppState.Current.Token!);
            if (st.Total > 0)
            {
                var parts = ImproveCategories
                    .Where(c => st.Tally.TryGetValue(c, out var n) && n > 0)
                    .Select(c => $"{st.Tally[c]} {c}");
                ImproveTally.Text = L10n.T("fb.sofar").Replace("{list}", string.Join(" · ", parts));
                ImproveTally.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
            }
            else ImproveTally.Visibility = Microsoft.UI.Xaml.Visibility.Collapsed;

            var mine = st.Mine.Select(f => new ImproveRow(
                $"[{f.Category}] {f.Message}  ·  {f.Status}")).ToList();
            ImproveMine.ItemsSource = mine;
            ImproveMineHeader.Visibility = mine.Count > 0
                ? Microsoft.UI.Xaml.Visibility.Visible
                : Microsoft.UI.Xaml.Visibility.Collapsed;
        }
        catch { /* backend offline — leave empty */ }
    }

    private async void OnSendImprovement(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        var message = ImproveMessage.Text.Trim();
        if (message.Length == 0) return;
        var cat = ImproveCategories[System.Math.Max(0, ImproveCategory.SelectedIndex)];
        int? rating = ImproveRating.SelectedIndex >= 1 ? ImproveRating.SelectedIndex : null;
        try
        {
            await ApiClient.Shared.SubmitImprovement(AppState.Current.Token!, cat, message, rating);
            ImproveMessage.Text = "";
            ImproveRating.SelectedIndex = 0;
            ImproveThanks.Text = L10n.T("fb.thanks");
            ImproveThanks.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
            await LoadImprovements();
        }
        catch (System.Exception ex)
        {
            ImproveThanks.Text = ex.Message;
            ImproveThanks.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
        }
    }

    private string CurrentMode => PreTranslateToggle.IsOn ? "pre" : "on_demand";

    private async void OnLanguagePicked(object sender, SelectionChangedEventArgs e)
    {
        if (_loadingLanguage) return;
        var idx = LanguageBox.SelectedIndex;
        if (idx < 0 || idx >= _languages.Length) return;
        try
        {
            await ApiClient.Shared.SetLanguage(AppState.Current.Token!,
                                               _languages[idx].Code, CurrentMode);
            AppState.Current.RememberLanguage(_languages[idx].Code);
        }
        catch { /* ignore */ }
    }

    private async void OnModeToggled(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        if (_loadingLanguage) return;
        var idx = LanguageBox.SelectedIndex;
        if (idx < 0 || idx >= _languages.Length) return;
        try
        {
            await ApiClient.Shared.SetLanguage(AppState.Current.Token!,
                                               _languages[idx].Code, CurrentMode);
        }
        catch { /* ignore */ }
    }

    private static string Masked(string t) =>
        t.Length > 8 ? t[..6] + "…" + t[^4..] : "••••";

    // -- admin: key management --

    public record KeyRow(string Line);

    private void ShowAdminError(string m)
    {
        AdminError.Text = m;
        AdminError.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
    }

    private void ShowKeys(KeysInfo info)
    {
        KeyList.ItemsSource = info.Versions.Select(v =>
            new KeyRow($"v{v.Version}  {(v.Active ? "active " : "inactive")}  {v.CreatedAt}")).ToList();
        RotateButton.IsEnabled = true;
        RetireButton.IsEnabled = true;
    }

    private async void OnLoadKeys(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        AdminError.Visibility = Microsoft.UI.Xaml.Visibility.Collapsed;
        AdminStatus.Visibility = Microsoft.UI.Xaml.Visibility.Collapsed;
        try { ShowKeys(await ApiClient.Shared.AdminKeys(AdminTokenBox.Password)); }
        catch (System.Exception ex) { ShowAdminError(ex.Message); }
    }

    private async void OnRotateKey(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        AdminError.Visibility = Microsoft.UI.Xaml.Visibility.Collapsed;
        try
        {
            ShowKeys(await ApiClient.Shared.RotateKey(AdminTokenBox.Password));
            AdminStatus.Text = L10n.T("nadm.rotated");
            AdminStatus.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
        }
        catch (System.Exception ex) { ShowAdminError(ex.Message); }
    }

    private async void OnRetireKeys(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        AdminError.Visibility = Microsoft.UI.Xaml.Visibility.Collapsed;
        try
        {
            var r = await ApiClient.Shared.RetireKeys(AdminTokenBox.Password);
            ShowKeys(new KeysInfo("env", r.Versions));
            AdminStatus.Text = $"Retired {r.Retired} old version(s).";
            AdminStatus.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
        }
        catch (System.Exception ex) { ShowAdminError(ex.Message); }
    }

    private async void OnExportEverything(object sender,
                                          Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        var s = AppState.Current;
        if (s.Token is null) return;
        try
        {
            var all = await ApiClient.Shared.ExportEverything(s.Token);
            var rows = 0;
            foreach (var t in all.Tables.Values) rows += t.Count;
            AdminStatus.Text =
                $"{all.Tables.Count} table(s), {rows} row(s) — {all.Note}";
            AdminStatus.Visibility = Microsoft.UI.Xaml.Visibility.Visible;
        }
        catch (Exception ex) { ShowAdminError(ex.Message); }
    }
}
