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
                              string Meta, Visibility RevokeVisibility);

    private List<ProgramChip> _chips = new();

    public TransfersPage() => InitializeComponent();

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

    private static string Cap(string s) =>
        string.IsNullOrEmpty(s) ? s : char.ToUpper(s[0]) + s[1..];
}
