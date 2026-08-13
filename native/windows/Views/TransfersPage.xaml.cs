using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

namespace PdiVault.Views;

public sealed partial class TransfersPage : Page
{
    public sealed class ProgramChip
    {
        public string Key { get; init; } = "";
        public bool Selected { get; set; }
    }

    public record TransferRow(string Id, string Filename, string Status,
                              string Meta, Visibility RevokeVisibility)
    {
        // A DataTemplate is stamped once per row, so `x:Name` addresses only
        // the last one. The label rides on the row instead.
        public string RevokeLabel => L10n.T("ntr.revoke");
        public string CheckLinkLabel => L10n.T("ntr.reciplink");
        public string RefreshLabel => L10n.T("car.refresh");
        public string ChainLabel => L10n.T("car.chain");
        public string ReceiveLabel => L10n.T("exc.asrecipient");
    }

    private string _disclose = "blind";

    private List<ProgramChip> _chips = new();

    public TransfersPage()
    {
        InitializeComponent();
        Localize();
    }

    /// Every word on this page, from the table rather than the markup.
    /// The two token sentences are the reason the screen was worked: each
    /// sits under a token shown once and names the only way the file can be
    /// retrieved, so a reader who cannot read it loses the file.
    private void Localize()
    {
        NtrTOutbound.Header = L10n.T("ntr.t.outbound");
        CarPivot.Header = L10n.T("car.title");
        CarHead.Text = L10n.T("car.title");
        CarPlaceHead.Text = L10n.T("car.place");
        CarLabelBox.PlaceholderText = L10n.T("car.label.ph");
        CarBlind.Content = L10n.T("car.disclose.blind");
        CarBlind.IsChecked = true;
        CarContact.Content = L10n.T("car.disclose.contact");
        CarPlaceButton.Content = L10n.T("car.place.go");
        CarNone.Text = L10n.T("car.none");
        CarRangHead.Text = L10n.T("car.rang");
        CarNoRings.Text = L10n.T("car.norings");
        TabTransfers.Text = L10n.T("tab.transfers");
        NfilSub.Text = L10n.T("nfil.sub");
        ProgramsLabel.Text = L10n.T("nfil.programs");
        RecipientBox.Header = L10n.T("nfil.recipient");
        RecipientBox.PlaceholderText = L10n.T("nfil.recipient.ph");
        FilenameBox.Header = L10n.T("nfil.filename");
        FilenameBox.PlaceholderText = L10n.T("nfil.filename.ph");
        ContentBox.Header = L10n.T("nfil.content");
        ContentBox.PlaceholderText = L10n.T("nfil.content.ph");
        CreateButton.Content = L10n.T("nfil.seal");
        NfilTokenOnce.Text = L10n.T("nfil.token.once");
        NfilTokenHand.Text = L10n.T("nfil.token.hand");
        NtrTIntake.Header = L10n.T("ntr.t.intake");
        NtrIntake.Text = L10n.T("ntr.intake");
        NtrIntakeSub.Text = L10n.T("ntr.intake.sub");
        FromBox.Header = L10n.T("nreq.from");
        FromBox.PlaceholderText = L10n.T("nreq.from.ph");
        PurposeBox.Header = L10n.T("nreq.purpose");
        PurposeBox.PlaceholderText = L10n.T("nreq.purpose.ph");
        RequestButton.Content = L10n.T("nreq.go");
        NintTokenOnce.Text = L10n.T("nint.token.once");
        NintTokenSend.Text = L10n.T("nint.token.send");
        NtrAsSender.Text = L10n.T("ntr.as.sender");
        NtrAnswerSub.Text = L10n.T("ntr.answer.sub");
        SenderTokenBox.Header = L10n.T("nint.token");
        SenderTokenBox.PlaceholderText = L10n.T("nint.token.ph");
        SenderFileBox.Header = L10n.T("nfil.filename");
        SenderFileBox.PlaceholderText = L10n.T("nint.filename.ph");
        SenderContentBox.Header = L10n.T("nfil.content");
        SenderContentBox.PlaceholderText = L10n.T("nint.content.ph");
        NintGo.Content = L10n.T("nint.go");
    }

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
        var s = AppState.Current;
        ApiClient.Shared.SetBase(s.BaseUrl);
        try
        {
            var programs = (await ApiClient.Shared.Programs(s.Token!)).Programs;
            _chips = programs.Select(p => new ProgramChip
            {
                Key = p.Key.ToUpper(),
                Selected = p.Key == "hipaa",
            }).ToList();
            ProgramChips.ItemsSource = _chips;
        }
        catch (Exception ex) { ShowError(ex.Message); }
        await Reload();
        await ReloadIntakes();
        try { await ReloadCarriers(); } catch (Exception ex) { ShowCarError(ex.Message); }
    }

    private async System.Threading.Tasks.Task Reload()
    {
        var s = AppState.Current;
        try
        {
            var transfers = await ApiClient.Shared.Transfers(s.Token!);
            TransfersList.ItemsSource = transfers.Select(t => new TransferRow(
                t.Id, t.Filename, Cap(t.Status),
                $"→ {t.Recipient} · {string.Join(" ", t.Programs.Select(p => p.ToUpper()))}"
                + (t.ExpiresAt is { } exp ? $" · retained until {exp}" : ""),
                t.Status == "revoked" ? Visibility.Collapsed : Visibility.Visible))
                .ToList();
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private async void OnCreate(object sender, RoutedEventArgs e)
    {
        var recipient = RecipientBox.Text.Trim();
        var filename = FilenameBox.Text.Trim();
        var content = ContentBox.Text;
        var programs = _chips.Where(c => c.Selected)
                             .Select(c => c.Key.ToLower()).ToArray();
        if (recipient.Length == 0 || filename.Length == 0
            || content.Length == 0 || programs.Length == 0)
        {
            ShowError("Fill recipient, filename, content, and pick at least one program.");
            return;
        }
        var s = AppState.Current;
        CreateButton.IsEnabled = false;
        ErrorText.Visibility = Visibility.Collapsed;
        try
        {
            var t = await ApiClient.Shared.CreateTransfer(
                s.Token!, recipient, filename, content, programs);
            TokenText.Text = t.ReceiveToken ?? "—";
            TokenCard.Visibility = Visibility.Visible;
            RecipientBox.Text = ""; FilenameBox.Text = ""; ContentBox.Text = "";
            await Reload();
        }
        catch (Exception ex) { ShowError(ex.Message); }
        finally { CreateButton.IsEnabled = true; }
    }

    private async void OnTransferRefresh(object sender, RoutedEventArgs e)
    {
        if (sender is not Button { Tag: string tid }) return;
        var s = AppState.Current;
        if (s.Token is null) return;
        try { await ApiClient.Shared.TransferOne(s.Token!, tid); await Reload(); }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private async void OnTransferChain(object sender, RoutedEventArgs e)
    {
        if (sender is not Button { Tag: string tid }) return;
        var s = AppState.Current;
        if (s.Token is null) return;
        try
        {
            var chain = await ApiClient.Shared.TransferCustody(s.Token!, tid);
            ShowError(L10n.T(chain.AuditChainIntact ? "car.verifies" : "car.notverify")
                + $" · {chain.ChainOfCustody.Length}");
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    // The recipient's act, with the one-shot token this screen just minted.
    private async void OnTransferReceive(object sender, RoutedEventArgs e)
    {
        if (sender is not Button { Tag: string tid }) return;
        var receiveToken = TokenText.Text.Trim();
        if (receiveToken.Length == 0 || receiveToken == "—") return;
        try
        {
            var f = await ApiClient.Shared.ReceiveTransfer(tid, receiveToken);
            ShowError(f.Filename ?? "file");
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    // Resolve the recipient's page before the link goes into an email — a
    // misconfigured public base is otherwise discovered by the recipient,
    // who has nobody to ask.
    private async void OnCheckLink(object sender, RoutedEventArgs e)
    {
        if (sender is not Button { Tag: string tid }) return;
        try
        {
            ShowError(await ApiClient.Shared.CheckRecipientPage(tid)
                ? L10n.T("car.verifies")
                : L10n.T("car.notverify"));
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private void OnDiscloseBlind(object sender, RoutedEventArgs e)
    {
        _disclose = "blind"; CarBlind.IsChecked = true; CarContact.IsChecked = false;
    }

    private void OnDiscloseContact(object sender, RoutedEventArgs e)
    {
        _disclose = "contact"; CarContact.IsChecked = true; CarBlind.IsChecked = false;
    }

    private async void OnPlaceCarrier(object sender, RoutedEventArgs e)
    {
        var label = CarLabelBox.Text.Trim();
        if (label.Length == 0) return;
        var s = AppState.Current;
        try
        {
            await ApiClient.Shared.PlaceCarrierBeacon(s.Token!, label, _disclose);
            CarLabelBox.Text = "";
            await ReloadCarriers();
        }
        catch (Exception ex) { ShowCarError(ex.Message); }
    }

    private void ShowCarError(string message)
    {
        CarError.Text = message;
        CarError.Visibility = Visibility.Visible;
    }

    private static TextBlock CarLine(string text, string brush, int size = 12) => new()
    {
        Text = text,
        FontSize = size,
        TextWrapping = TextWrapping.Wrap,
        IsTextSelectionEnabled = true,
        Foreground = (Microsoft.UI.Xaml.Media.Brush)
            Application.Current.Resources[brush],
    };

    private Button CarAction(string label, Func<System.Threading.Tasks.Task> work)
    {
        var b = new Button
        {
            Content = label, FontSize = 11,
            Background = new Microsoft.UI.Xaml.Media.SolidColorBrush(
                Microsoft.UI.Colors.Transparent),
        };
        b.Click += async (_, _) =>
        {
            try { await work(); }
            catch (Exception ex) { ShowCarError(ex.Message); }
        };
        return b;
    }

    private async System.Threading.Tasks.Task ReloadCarriers()
    {
        var s = AppState.Current;
        if (s.Token is null) return;
        CarError.Visibility = Visibility.Collapsed;
        var rows = await ApiClient.Shared.CarrierBeacons(s.Token!);
        CarNone.Visibility = rows.Length == 0 ? Visibility.Visible : Visibility.Collapsed;
        CarRows.Children.Clear();
        foreach (var row in rows)
        {
            var bid = row.Id;
            var panel = new StackPanel { Spacing = 4 };
            panel.Children.Add(CarLine(
                $"{row.Label} · {row.RefKind} · {row.State} · {row.Disclose}"
                + $" · ×{row.Scans}"
                + (row.Active ? "" : " · " + L10n.T("car.lifted")),
                "PdiTxtBrush"));
            var actions = new StackPanel
            { Orientation = Orientation.Horizontal, Spacing = 6 };
            actions.Children.Add(CarAction(L10n.T("car.chain"), async () =>
            {
                var ch = await ApiClient.Shared.CarrierCustody(s.Token!, bid);
                CarChain.Children.Clear();
                CarChain.Children.Add(CarLine(L10n.T("car.chain"), "PdiTxtBrush"));
                CarChain.Children.Add(CarLine(
                    L10n.T("car.auditchain") + " "
                    + L10n.T(ch.AuditChainIntact ? "car.verifies" : "car.notverify"),
                    "PdiT2Brush"));
                foreach (var entry in ch.ChainOfCustody)
                    CarChain.Children.Add(CarLine(
                        $"{entry.Event} — {entry.Actor} · {entry.At}", "PdiT2Brush", 11));
                CarChainPanel.Visibility = Visibility.Visible;
            }));
            actions.Children.Add(CarAction(L10n.T("car.sees"), async () =>
            {
                var card = await ApiClient.Shared.ScanCard(bid);
                CarCard.Children.Clear();
                CarCard.Children.Add(CarLine(L10n.T("car.strangercard"), "PdiTxtBrush"));
                CarCard.Children.Add(CarLine(card.Badge, "PdiTxtBrush"));
                CarCard.Children.Add(CarLine(card.Note, "PdiT2Brush", 11));
                CarCard.Children.Add(CarLine(
                    $"{card.Reference} · {card.Kind} · {card.State} · "
                    + L10n.T(card.UnderCustody ? "car.custody.yes" : "car.custody.no"),
                    "PdiT2Brush", 11));
                CarCard.Children.Add(CarLine(
                    L10n.T("car.contents") + " " + L10n.T("car.contents.no")
                    + " " + L10n.T("car.contents.never"), "PdiT2Brush", 11));
                CarCardPanel.Visibility = Visibility.Visible;
            }));
            actions.Children.Add(CarAction(L10n.T("car.refresh"), async () =>
            {
                await ApiClient.Shared.CarrierBeacon(s.Token!, bid);
                await ReloadCarriers();
            }));
            actions.Children.Add(CarAction(L10n.T("car.lift"), async () =>
            {
                await ApiClient.Shared.LiftCarrierBeacon(s.Token!, bid);
                await ReloadCarriers();
            }));
            panel.Children.Add(actions);
            // The state select, as a walk along the chain — and the scanner's
            // half, exercised from here: found and ring take no bearer.
            var states = new StackPanel
            { Orientation = Orientation.Horizontal, Spacing = 6 };
            foreach (var st in new[] { "sealed", "in_transit", "delivered", "opened" })
            {
                var target = st;
                states.Children.Add(CarAction(
                    row.State == target ? target + " ✓" : target, async () =>
                {
                    await ApiClient.Shared.SetCarrierState(s.Token!, bid, target);
                    await ReloadCarriers();
                }));
            }
            panel.Children.Add(states);
            var scanner = new StackPanel
            { Orientation = Orientation.Horizontal, Spacing = 6 };
            scanner.Children.Add(CarAction(L10n.T("car.ring"), async () =>
            {
                await ApiClient.Shared.RingHolder(bid);
                await ReloadCarriers();
            }));
            scanner.Children.Add(CarAction(L10n.T("car.found"), async () =>
            {
                await ApiClient.Shared.ReportFound(bid);
                await ReloadCarriers();
            }));
            panel.Children.Add(scanner);
            panel.Children.Add(CarLine(
                L10n.T("qr.addr") + " " + ApiClient.Shared.ScanQrUrl(bid),
                "PdiT2Brush", 10));
            panel.Children.Add(CarLine(ApiClient.Shared.ScanPageUrl(bid),
                "PdiT2Brush", 10));
            var border = new Border
            {
                Background = (Microsoft.UI.Xaml.Media.Brush)
                    Application.Current.Resources["PdiCardBrush"],
                BorderBrush = (Microsoft.UI.Xaml.Media.Brush)
                    Application.Current.Resources["PdiLineBrush"],
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(14),
                Padding = new Thickness(14),
                Child = panel,
            };
            CarRows.Children.Add(border);
        }

        var rings = await ApiClient.Shared.Rings(s.Token!);
        CarNoRings.Visibility = rings.Length == 0 ? Visibility.Visible : Visibility.Collapsed;
        CarRings.Children.Clear();
        foreach (var ring in rings)
        {
            var rid = ring.Id;
            var line = new StackPanel
            { Orientation = Orientation.Horizontal, Spacing = 8 };
            line.Children.Add(CarLine(
                $"{ring.Kind} · {ring.State} · {ring.CreatedAt}", "PdiT2Brush", 11));
            line.Children.Add(CarAction(L10n.T("car.transcript"), async () =>
            {
                var tr = await ApiClient.Shared.RingTranscript(s.Token!, rid);
                CarTranscript.Text = $"{tr.Kind} · {tr.Note} · {tr.Outcome}";
                CarTranscript.Visibility = Visibility.Visible;
            }));
            CarRings.Children.Add(line);
        }

        // The pairing card: the card's own words, straight from the wire.
        try
        {
            var pair = await ApiClient.Shared.PairInfo();
            CarPair.Children.Clear();
            foreach (var how in pair.How)
                CarPair.Children.Add(CarLine(how, "PdiT2Brush", 11));
            CarPair.Children.Add(CarLine(pair.ConsoleUrl, "PdiTxtBrush", 11));
            CarPair.Children.Add(CarLine(pair.Note, "PdiT2Brush", 10));
            CarPair.Children.Add(CarLine(
                L10n.T("qr.addr") + " " + ApiClient.Shared.PairQrUrl(),
                "PdiT2Brush", 10));
        }
        catch { /* pairing is best-effort; the deployment may be headless */ }
    }

    private async void OnRevoke(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is not string tid) return;
        var s = AppState.Current;
        try
        {
            await ApiClient.Shared.RevokeTransfer(s.Token!, tid);
            await Reload();
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private void ShowError(string message)
    {
        ErrorText.Text = message;
        ErrorText.Visibility = Visibility.Visible;
    }

    // -- Intake (request a file in) --

    public sealed class IntakeRow
    {
        public string Id { get; init; } = "";
        public string FromParty { get; init; } = "";
        public string Status { get; init; } = "";
        public string Meta { get; init; } = "";
        public string FileText { get; init; } = "";
        public bool Submitted { get; init; }
        public bool Open { get; init; }
        public string RefreshLabel => L10n.T("car.refresh");
        public string ChainLabel => L10n.T("car.chain");
        public Visibility ReadVisibility =>
            Submitted ? Visibility.Visible : Visibility.Collapsed;
        public Visibility CloseVisibility =>
            Open ? Visibility.Visible : Visibility.Collapsed;
        public Visibility FileVisibility =>
            FileText.Length > 0 ? Visibility.Visible : Visibility.Collapsed;

        // Same reason as TransferRow.RevokeLabel: the template is stamped
        // per row, so the words come with the row.
        public string ReadLabel => L10n.T("ntr.read");
        public string CloseLabel => L10n.T("nreq.close");
    }

    private List<ProgramChip> _intakeChips = new();
    private readonly Dictionary<string, string> _readFiles = new();
    private Intake[] _intakes = Array.Empty<Intake>();

    private async System.Threading.Tasks.Task ReloadIntakes()
    {
        var s = AppState.Current;
        try
        {
            if (_intakeChips.Count == 0)
            {
                var programs = (await ApiClient.Shared.Programs(s.Token!)).Programs;
                _intakeChips = programs.Select(p => new ProgramChip
                {
                    Key = p.Key.ToUpper(),
                    Selected = p.Key == "hipaa",
                }).ToList();
                IntakeProgramChips.ItemsSource = _intakeChips;
            }
            _intakes = await ApiClient.Shared.Intakes(s.Token!);
            IntakesList.ItemsSource = _intakes.Select(i => new IntakeRow
            {
                Id = i.Id,
                FromParty = i.FromParty,
                Status = Cap(i.Status),
                Meta = (i.Purpose is { } p ? $"{p} · " : "")
                       + string.Join(" ", i.Programs.Select(x => x.ToUpper())),
                FileText = _readFiles.TryGetValue(i.Id, out var f) ? f : "",
                Submitted = i.Status == "submitted",
                Open = i.Status == "open",
            }).ToList();
        }
        catch (Exception ex) { ShowIntakeError(ex.Message); }
    }

    private async void OnRequestIntake(object sender, RoutedEventArgs e)
    {
        var from = FromBox.Text.Trim();
        var programs = _intakeChips.Where(c => c.Selected)
                                   .Select(c => c.Key.ToLower()).ToArray();
        if (from.Length == 0 || programs.Length == 0)
        {
            ShowIntakeError("Fill 'From' and pick at least one program.");
            return;
        }
        var s = AppState.Current;
        RequestButton.IsEnabled = false;
        IntakeError.Visibility = Visibility.Collapsed;
        try
        {
            var i = await ApiClient.Shared.CreateIntake(
                s.Token!, from, PurposeBox.Text.Trim(), programs);
            SubmitTokenText.Text = i.SubmitToken ?? "—";
            SubmitTokenCard.Visibility = Visibility.Visible;
            FromBox.Text = ""; PurposeBox.Text = "";
            await ReloadIntakes();
        }
        catch (Exception ex) { ShowIntakeError(ex.Message); }
        finally { RequestButton.IsEnabled = true; }
    }

    private async void OnIntakeRefresh(object sender, RoutedEventArgs e)
    {
        if (sender is not Button { Tag: string iid }) return;
        var s = AppState.Current;
        if (s.Token is null) return;
        try { await ApiClient.Shared.IntakeOne(s.Token!, iid); await ReloadIntakes(); }
        catch (Exception ex) { ShowIntakeError(ex.Message); }
    }

    private async void OnIntakeChain(object sender, RoutedEventArgs e)
    {
        if (sender is not Button { Tag: string iid }) return;
        var s = AppState.Current;
        if (s.Token is null) return;
        try
        {
            var chain = await ApiClient.Shared.IntakeCustody(s.Token!, iid);
            ShowIntakeError(L10n.T(chain.AuditChainIntact ? "car.verifies" : "car.notverify")
                + $" · {chain.ChainOfCustody.Length}");
        }
        catch (Exception ex) { ShowIntakeError(ex.Message); }
    }

    private async void OnReadIntake(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is not string iid) return;
        var s = AppState.Current;
        try
        {
            var f = await ApiClient.Shared.ReadIntakeFile(s.Token!, iid);
            _readFiles[iid] = $"{f.Filename ?? "file"}: {f.Content ?? ""}";
            await ReloadIntakes();
        }
        catch (Exception ex) { ShowIntakeError(ex.Message); }
    }

    private async void OnCloseIntake(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is not string iid) return;
        var s = AppState.Current;
        try
        {
            await ApiClient.Shared.CloseIntake(s.Token!, iid);
            await ReloadIntakes();
        }
        catch (Exception ex) { ShowIntakeError(ex.Message); }
    }

    private async void OnSubmitIntake(object sender, RoutedEventArgs e)
    {
        var target = _intakes.LastOrDefault(i => i.Status == "open");
        if (target is null) { ShowIntakeError("no open intake to submit into"); return; }
        var token = SenderTokenBox.Text.Trim();
        var file = SenderFileBox.Text.Trim();
        var content = SenderContentBox.Text;
        if (token.Length == 0 || file.Length == 0 || content.Length == 0)
        {
            ShowIntakeError("Fill token, filename, and content.");
            return;
        }
        IntakeError.Visibility = Visibility.Collapsed;
        try
        {
            await ApiClient.Shared.SubmitIntake(target.Id, token, file, content);
            SenderTokenBox.Text = ""; SenderFileBox.Text = ""; SenderContentBox.Text = "";
            await ReloadIntakes();
        }
        catch (Exception ex) { ShowIntakeError(ex.Message); }
    }

    private void ShowIntakeError(string message)
    {
        IntakeError.Text = message;
        IntakeError.Visibility = Visibility.Visible;
    }

    private static string Cap(string s) =>
        string.IsNullOrEmpty(s) ? s : char.ToUpper(s[0]) + s[1..];
}
