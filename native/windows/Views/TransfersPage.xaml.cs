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
    }

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
