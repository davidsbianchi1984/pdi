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
        UnlockedText.Text = L10n.T("nov.unlocked");
        VaultTitle.Text = L10n.T("nov.title");
        SealedText.Text = L10n.T("nov.sealed");
        RecordsLabel.Text = L10n.T("nrec.t.records");
        AuditLabel.Text = L10n.T("tab.audit");
        TokenLabel.Text = L10n.T("nov.token");
        NotesText.Text = L10n.T("nov.notes");
        PreTranslateToggle.Header = L10n.T("nov.pretrans");
        PreTranslateToggle.OnContent = L10n.T("nov.mode.on");
        PreTranslateToggle.OffContent = L10n.T("nov.mode.off");
        ImproveTitle.Text = L10n.T("nfb.title");
        ImproveSub.Text = L10n.T("nfb.sub");
        ImproveCategory.Header = L10n.T("nfb.category");
        ImproveMessage.PlaceholderText = L10n.T("nfb.msg.ph");
        ImproveRating.Header = L10n.T("nfb.rating.opt");
        ImproveSend.Content = L10n.T("nfb.send");
        ImproveMineHeader.Text = L10n.T("nfb.yours");
        AdminTitle.Text = L10n.T("nadm.title");
        AdminReq.Text = L10n.T("nadm.req") + " " + L10n.T("nadm.req.more");
        AdminTokenBox.Header = L10n.T("nadm.token");
        AdminDsr.Content = L10n.T("nadm.dsr");
        AdminLoad.Content = L10n.T("nadm.versions");
        RotateButton.Content = L10n.T("nadm.rotate");
        RetireButton.Content = L10n.T("nadm.retire");
        TnTitle.Text = L10n.T("tn.create");
        TnAdminTokenBox.Header = L10n.T("nadm.token");
        TnNameBox.PlaceholderText = L10n.T("co.name.ph");
        TnCreateButton.Content = L10n.T("tn.createbtn");
        TnMadeNote.Text = L10n.T("tn.token.note");
        TnIdBox.PlaceholderText = L10n.T("adm.tenant.ph");
        TnRestoreButton.Content = L10n.T("cu.restore.all");
        TnDelSoftButton.Content = L10n.T("cu.del.soft");
        TnDelHardButton.Content = L10n.T("cu.del.hard");
        TnMintReadButton.Content = L10n.T("cu.mint.read");
        TnMintWriteButton.Content = L10n.T("cu.mint.write");
        TnRetentionBox.PlaceholderText = L10n.T("ky.retention");
        TnRetentionButton.Content = L10n.T("co.set");
        TnBaaHead.Text = L10n.T("cu.paperwork");
        TnCustBox.PlaceholderText = L10n.T("cu.cust.name");
        TnOpBox.PlaceholderText = L10n.T("cu.op.name");
        TnEffBox.PlaceholderText = L10n.T("cu.eff");
        TnBaaRecordButton.Content = L10n.T("cu.record");
        TnBaaReadButton.Content = L10n.T("cu.onfile");
        TnBaaRescindButton.Content = L10n.T("cu.rescind");
        GateTitle.Text = L10n.T("co.ceiling");
        GateShiftHead.Text = L10n.T("co.shift");
        GateNameBox.PlaceholderText = L10n.T("co.name.ph");
        GateRoleBox.PlaceholderText = L10n.T("co.role.ph");
        GateAddButton.Content = L10n.T("co.addroster");
        GateTzBox.PlaceholderText = L10n.T("co.tz.ph");
        GateTzButton.Content = L10n.T("co.set");
        GateSentHead.Text = L10n.T("co.sent");
        GateSentNote.Text = L10n.T("co.sent.note");
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
        AccNeedsTitle.Text = L10n.T("ns.acc.needs.title");
        AccNeedsList.Text = string.Join("\n", new[]
        {
            "blind", "deaf", "mute", "motor", "cognitive", "dyslexia", "motion",
        }.Select(need => "• " + L10n.T($"ns.acc.needs.{need}")));
        AccNeedsMore.Text = L10n.T("ns.acc.needs.more");
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
        await ReloadGate();
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
            AuditValue.Text = v.Intact ? L10n.T("nov.intact") : L10n.T("nov.broken");
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

    private void ShowTnError(string message)
    {
        TnError.Text = message;
        TnError.Visibility = Visibility.Visible;
    }

    private async void OnCreateTenant(object sender, RoutedEventArgs e)
    {
        var name = TnNameBox.Text.Trim();
        if (name.Length == 0) return;
        try
        {
            var made = await ApiClient.Shared.CreateTenant(
                TnAdminTokenBox.Password, name);
            TnMade.Text = $"{made.Id} · {made.Token}";
            TnMade.Visibility = Visibility.Visible;
            TnMadeNote.Visibility = Visibility.Visible;
            TnNameBox.Text = "";
        }
        catch (Exception ex) { ShowTnError(ex.Message); }
    }

    private async void OnTenantRestore(object sender, RoutedEventArgs e)
    {
        try { await ApiClient.Shared.RestoreTenant(TnAdminTokenBox.Password, TnIdBox.Text.Trim()); }
        catch (Exception ex) { ShowTnError(ex.Message); }
    }

    // Soft keeps the door open; hard cannot be taken back. Both leave the
    // audit chain standing.
    private async void OnTenantDelSoft(object sender, RoutedEventArgs e)
    {
        try { await ApiClient.Shared.DeleteTenant(TnAdminTokenBox.Password, TnIdBox.Text.Trim(), "soft"); }
        catch (Exception ex) { ShowTnError(ex.Message); }
    }

    private async void OnTenantDelHard(object sender, RoutedEventArgs e)
    {
        try { await ApiClient.Shared.DeleteTenant(TnAdminTokenBox.Password, TnIdBox.Text.Trim(), "hard"); }
        catch (Exception ex) { ShowTnError(ex.Message); }
    }

    private async void OnMintRead(object sender, RoutedEventArgs e) => await Mint("read");

    private async void OnMintWrite(object sender, RoutedEventArgs e) => await Mint("write");

    private async System.Threading.Tasks.Task Mint(string role)
    {
        try
        {
            var minted = await ApiClient.Shared.MintTenantToken(
                TnAdminTokenBox.Password, TnIdBox.Text.Trim(), role);
            TnMinted.Text = minted.Token;
            TnMinted.Visibility = Visibility.Visible;
            TnMintedNote.Text = L10n.T("cu.minted.note");
            TnMintedNote.Visibility = Visibility.Visible;
        }
        catch (Exception ex) { ShowTnError(ex.Message); }
    }

    private async void OnSetTenantRetention(object sender, RoutedEventArgs e)
    {
        try
        {
            await ApiClient.Shared.SetTenantRetention(
                TnAdminTokenBox.Password, TnIdBox.Text.Trim(),
                TnRetentionBox.Text.Trim());
        }
        catch (Exception ex) { ShowTnError(ex.Message); }
    }

    private async void OnBaaRecord(object sender, RoutedEventArgs e)
    {
        try
        {
            var baa = await ApiClient.Shared.RecordTenantBaa(
                TnAdminTokenBox.Password, TnIdBox.Text.Trim(),
                TnCustBox.Text.Trim(), TnOpBox.Text.Trim(), TnEffBox.Text.Trim());
            ShowBaa(baa);
        }
        catch (Exception ex) { ShowTnError(ex.Message); }
    }

    private async void OnBaaRead(object sender, RoutedEventArgs e)
    {
        try { ShowBaa(await ApiClient.Shared.TenantBaa(TnAdminTokenBox.Password, TnIdBox.Text.Trim())); }
        catch (Exception ex) { ShowTnError(ex.Message); }
    }

    private async void OnBaaRescind(object sender, RoutedEventArgs e)
    {
        try
        {
            await ApiClient.Shared.RescindTenantBaa(TnAdminTokenBox.Password, TnIdBox.Text.Trim());
            TnBaaLine.Visibility = Visibility.Collapsed;
        }
        catch (Exception ex) { ShowTnError(ex.Message); }
    }

    private void ShowBaa(BaaOut baa)
    {
        if (!baa.Executed) return;
        TnBaaLine.Text = $"{baa.CustomerLegalName} ↔ {baa.OperatorLegalName} · {baa.EffectiveDate}";
        TnBaaLine.Visibility = Visibility.Visible;
    }

    private static TextBlock GateLine(string text, string brush) => new()
    {
        Text = text,
        FontSize = 11,
        TextWrapping = TextWrapping.Wrap,
        Foreground = (Microsoft.UI.Xaml.Media.Brush)
            Application.Current.Resources[brush],
    };

    private async System.Threading.Tasks.Task ReloadGate()
    {
        var s = AppState.Current;
        if (s.Token is null) return;
        GateError.Visibility = Visibility.Collapsed;
        try
        {
            var ceiling = await ApiClient.Shared.GateCeiling(s.Token!);
            GateCeilingText.Text = ceiling.Rule + "\n"
                + L10n.T("co.may") + " " + string.Join(", ", ceiling.May.Keys.OrderBy(k => k)) + "\n"
                + L10n.T("co.maynever") + " " + string.Join(", ", ceiling.MayNever.Keys.OrderBy(k => k));
            var channel = await ApiClient.Shared.GateChannel(s.Token!);
            GateChannelText.Text = L10n.T("co.channel") + " "
                + L10n.T(channel.Configured ? "co.configured" : "co.notconfigured")
                + (channel.Signed == true ? " " + L10n.T("co.signed") : "");
            var roster = await ApiClient.Shared.GateRoster(s.Token!);
            GateRosterRows.Children.Clear();
            if (roster.Roster.Length == 0)
                GateRosterRows.Children.Add(GateLine(L10n.T("co.noroster"), "PdiT2Brush"));
            if (!roster.AnybodyOnShift)
                GateRosterRows.Children.Add(GateLine(L10n.T("co.nobody"), "PdiT2Brush"));
            foreach (var entry in roster.Roster)
            {
                var rid = entry.Id;
                var row = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
                row.Children.Add(GateLine($"{entry.Name} · {entry.Role}", "PdiT2Brush"));
                var remove = new Button
                {
                    Content = L10n.T("co.remove"), FontSize = 11,
                    Background = new Microsoft.UI.Xaml.Media.SolidColorBrush(
                        Microsoft.UI.Colors.Transparent),
                };
                remove.Click += async (_, _) =>
                {
                    try
                    {
                        await ApiClient.Shared.RemoveFromRoster(s.Token!, rid);
                        await ReloadGate();
                    }
                    catch (Exception ex) { ShowGateError(ex.Message); }
                };
                row.Children.Add(remove);
                GateRosterRows.Children.Add(row);
            }
            var pages = await ApiClient.Shared.GatePages(s.Token!);
            GatePageRows.Children.Clear();
            if (pages.Length == 0)
                GatePageRows.Children.Add(GateLine(L10n.T("co.nothingpaged"), "PdiT2Brush"));
            foreach (var page in pages)
            {
                var pid = page.Id;
                var row = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
                row.Children.Add(GateLine($"{pid} · {page.State}", "PdiT2Brush"));
                if (page.State != "sent" && pid is not null)
                {
                    var retry = new Button
                    {
                        Content = L10n.T("co.retry"), FontSize = 11,
                        Background = new Microsoft.UI.Xaml.Media.SolidColorBrush(
                            Microsoft.UI.Colors.Transparent),
                    };
                    retry.Click += async (_, _) =>
                    {
                        try
                        {
                            await ApiClient.Shared.RetryGatePage(s.Token!, pid);
                            await ReloadGate();
                        }
                        catch (Exception ex) { ShowGateError(ex.Message); }
                    };
                    row.Children.Add(retry);
                }
                GatePageRows.Children.Add(row);
            }
        }
        catch (Exception ex) { ShowGateError(ex.Message); }
    }

    private void ShowGateError(string message)
    {
        GateError.Text = message;
        GateError.Visibility = Visibility.Visible;
    }

    private async void OnRosterAdd(object sender, RoutedEventArgs e)
    {
        var s = AppState.Current;
        var name = GateNameBox.Text.Trim();
        if (s.Token is null || name.Length == 0) return;
        try
        {
            await ApiClient.Shared.AddToRoster(s.Token!, name, GateRoleBox.Text.Trim());
            GateNameBox.Text = "";
            await ReloadGate();
        }
        catch (Exception ex) { ShowGateError(ex.Message); }
    }

    private async void OnGateTz(object sender, RoutedEventArgs e)
    {
        var s = AppState.Current;
        var tz = GateTzBox.Text.Trim();
        if (s.Token is null || tz.Length == 0) return;
        try
        {
            await ApiClient.Shared.SetGateTimezone(s.Token!, tz);
            GateTzBox.Text = "";
            await ReloadGate();
        }
        catch (Exception ex) { ShowGateError(ex.Message); }
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
