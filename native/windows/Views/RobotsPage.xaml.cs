using System;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

namespace PdiVault.Views;

public sealed partial class RobotsPage : Page
{
    public record RobotRow(string Id, string Name, string Sealed);

    private RobotSpec[] _catalog = Array.Empty<RobotSpec>();

    public RobotsPage() => InitializeComponent();

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
        var s = AppState.Current;
        ApiClient.Shared.SetBase(s.BaseUrl);
        try
        {
            _catalog = (await ApiClient.Shared.Robotics(s.Token!)).Robots;
            ModelBox.ItemsSource = _catalog
                .Select(r => $"{r.Label} · {r.Maker}").ToList();
            if (_catalog.Length > 0) ModelBox.SelectedIndex = 0;
        }
        catch (Exception ex) { ShowError(ex.Message); }
        await Reload();
    }

    private async System.Threading.Tasks.Task Reload()
    {
        var s = AppState.Current;
        try
        {
            var robots = await ApiClient.Shared.Robots(s.Token!);
            RobotsList.ItemsSource = robots.Select(r =>
                new RobotRow(r.Id, r.Name, $"{r.Collected} sealed")).ToList();
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private async void OnBind(object sender, RoutedEventArgs e)
    {
        if (ModelBox.SelectedIndex < 0 || ModelBox.SelectedIndex >= _catalog.Length) return;
        var s = AppState.Current;
        BindButton.IsEnabled = false;
        ErrorText.Visibility = Visibility.Collapsed;
        try
        {
            await ApiClient.Shared.BindRobot(s.Token!,
                _catalog[ModelBox.SelectedIndex].Model);
            await Reload();
        }
        catch (Exception ex) { ShowError(ex.Message); }
        finally { BindButton.IsEnabled = true; }
    }

    private void OnSealMap(object sender, RoutedEventArgs e) =>
        Seal(sender, "map", "{\"rooms\": 5}");

    private void OnSealSnapshot(object sender, RoutedEventArgs e) =>
        Seal(sender, "snapshot", "camera still");

    private void OnSealSensor(object sender, RoutedEventArgs e) =>
        Seal(sender, "sensor_log", "steps & doors");

    private async void Seal(object sender, string kind, string content)
    {
        if ((sender as Button)?.Tag is not string rid) return;
        var s = AppState.Current;
        ErrorText.Visibility = Visibility.Collapsed;
        try
        {
            var r = await ApiClient.Shared.Ingest(s.Token!, rid, kind, content);
            KeyText.Text = r.Key;
            ResultCard.Visibility = Visibility.Visible;
            await Reload();
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private void ShowError(string message)
    {
        ErrorText.Text = message;
        ErrorText.Visibility = Visibility.Visible;
    }
}
