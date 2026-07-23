using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

namespace PdiVault.Views;

public sealed partial class VaultPage : Page
{
    // Simple row model; the page rebuilds the list on every change.
    public sealed class RecordRow
    {
        public string Key { get; set; } = "";
        public string Value { get; set; } = "";
        public Visibility ValueVisibility =>
            string.IsNullOrEmpty(Value) ? Visibility.Collapsed : Visibility.Visible;
    }

    private List<RecordRow> _rows = new();

    public VaultPage() => InitializeComponent();

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
        ApiClient.Shared.SetBase(AppState.Current.BaseUrl);
        await Reload();
    }

    private async System.Threading.Tasks.Task Reload()
    {
        try
        {
            var keys = await ApiClient.Shared.Keys(AppState.Current.Token!);
            _rows = keys.Select(k => new RecordRow { Key = k }).ToList();
            Empty.Visibility = _rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
        }
        catch (Exception ex) { ShowError(ex.Message); }
        Render();
    }

    private void Render()
    {
        RecordsList.ItemsSource = null;
        RecordsList.ItemsSource = _rows;
    }

    private async void OnSeal(object sender, RoutedEventArgs e)
    {
        var key = KeyBox.Text.Trim();
        var value = ValueBox.Text;
        if (key.Length == 0 || value.Length == 0) { ShowError("Enter a key and a value."); return; }
        SealButton.IsEnabled = false;
        ErrorText.Visibility = Visibility.Collapsed;
        try
        {
            await ApiClient.Shared.PutRecord(AppState.Current.Token!, key, value);
            KeyBox.Text = ""; ValueBox.Text = "";
            await Reload();
        }
        catch (Exception ex) { ShowError(ex.Message); }
        finally { SealButton.IsEnabled = true; }
    }

    private async void OnReveal(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is not string key) return;
        var row = _rows.FirstOrDefault(r => r.Key == key);
        if (row is null) return;
        if (!string.IsNullOrEmpty(row.Value)) { row.Value = ""; Render(); return; }
        try
        {
            var rec = await ApiClient.Shared.Record(AppState.Current.Token!, key);
            row.Value = rec.Value;
            Render();
        }
        catch (Exception ex) { ShowError(ex.Message); }
    }

    private async void OnDelete(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is not string key) return;
        try
        {
            await ApiClient.Shared.DeleteRecord(AppState.Current.Token!, key);
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
