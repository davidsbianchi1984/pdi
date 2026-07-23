using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

namespace PdiVault.Views;

public sealed partial class OverviewPage : Page
{
    public OverviewPage() => InitializeComponent();

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
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
    }

    private static string Masked(string t) =>
        t.Length > 8 ? t[..6] + "…" + t[^4..] : "••••";
}
