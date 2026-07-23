using System;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

namespace PdiVault.Views;

public sealed partial class ConnectorsPage : Page
{
    public sealed class ConnRow
    {
        public string Id { get; init; } = "";
        public string Title { get; init; } = "";
        public string Handle { get; init; } = "";
        public bool Collect { get; init; }
        public Visibility IngestVisibility =>
            Collect ? Visibility.Visible : Visibility.Collapsed;
        public Visibility PublishVisibility =>
            Collect ? Visibility.Collapsed : Visibility.Visible;
    }

    private static readonly string[] Platforms =
    {
        "instagram", "x", "tiktok", "facebook", "linkedin", "youtube",
        "whatsapp", "discord", "twitch", "pinterest", "snapchat", "mastodon",
    };

    private SocialConn[] _conns = Array.Empty<SocialConn>();

    public ConnectorsPage() => InitializeComponent();

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
        PlatformBox.ItemsSource = Platforms.ToList();
        PlatformBox.SelectedIndex = 0;
        await Reload();
    }

    private async System.Threading.Tasks.Task Reload()
    {
        var s = AppState.Current;
        try
        {
            _conns = await ApiClient.Shared.Connectors(s.Token!);
            ConnsList.ItemsSource = _conns.Select(c => new ConnRow
            {
                Id = c.Id,
                Title = $"{Cap(c.Platform)} · {c.Direction}",
                Handle = c.Handle is { } h ? $"@{h}" : "",
                Collect = c.Direction == "collect",
            }).ToList();
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private void OnConnectCollect(object sender, RoutedEventArgs e) => Connect("collect");

    private void OnConnectPublish(object sender, RoutedEventArgs e) => Connect("publish");

    private async void Connect(string direction)
    {
        if (PlatformBox.SelectedItem is not string platform) return;
        var s = AppState.Current;
        ErrorText.Visibility = Visibility.Collapsed;
        try
        {
            await ApiClient.Shared.CreateConnector(
                s.Token!, platform, direction, HandleBox.Text.Trim());
            HandleBox.Text = "";
            await Reload();
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private async void OnIngest(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is not string cid) return;
        var conn = _conns.FirstOrDefault(c => c.Id == cid);
        var s = AppState.Current;
        try
        {
            await ApiClient.Shared.ConnectorIngest(
                s.Token!, cid, $"sample post from {conn?.Platform}");
            ShowStatus($"sealed one item from {conn?.Platform}");
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private async void OnPublish(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is not string cid) return;
        var conn = _conns.FirstOrDefault(c => c.Id == cid);
        var s = AppState.Current;
        try
        {
            await ApiClient.Shared.ConnectorPublish(
                s.Token!, cid, "An update from the vault.");
            ShowStatus($"published to {conn?.Platform}");
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private async void OnRevoke(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is not string cid) return;
        var s = AppState.Current;
        try
        {
            await ApiClient.Shared.RevokeConnector(s.Token!, cid);
            await Reload();
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private void ShowStatus(string message)
    {
        StatusText.Text = message;
        StatusText.Visibility = Visibility.Visible;
    }

    private void ShowError(string message)
    {
        ErrorText.Text = message;
        ErrorText.Visibility = Visibility.Visible;
    }

    private static string Cap(string s) =>
        string.IsNullOrEmpty(s) ? s : char.ToUpper(s[0]) + s[1..];
}
