using System;
using System.Linq;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

namespace PdiVault.Views;

public sealed partial class AuditPage : Page
{
    public record EntryRow(int Seq, string Action, string? Ref, string? Category);

    public AuditPage() => InitializeComponent();

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
        var s = AppState.Current;
        ApiClient.Shared.SetBase(s.BaseUrl);
        try
        {
            var v = await ApiClient.Shared.AuditVerify(s.Token!);
            StatusText.Text = v.Intact ? "Chain intact" : "Chain broken";
        }
        catch (Exception ex) { StatusText.Text = ex.Message; }

        try
        {
            var entries = await ApiClient.Shared.AuditEntries(s.Token!);
            CountText.Text = $"{entries.Length} recorded events";
            EntriesList.ItemsSource = entries
                .OrderByDescending(x => x.Seq).Take(30)
                .Select(x => new EntryRow(x.Seq, x.Action, x.Ref, x.Category)).ToList();
        }
        catch { /* leave list empty */ }
    }
}
