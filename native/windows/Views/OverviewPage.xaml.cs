using System.Linq;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

namespace PdiVault.Views;

public sealed partial class OverviewPage : Page
{
    private LanguageInfo[] _languages = System.Array.Empty<LanguageInfo>();
    private bool _loadingLanguage;

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
        try
        {
            _loadingLanguage = true;
            _languages = (await ApiClient.Shared.Languages(s.Token!)).Languages;
            LanguageBox.ItemsSource = _languages.Select(l =>
                l.Label + (l.NotesTranslated ? "" : "  (notes in English)")).ToList();
            var current = await ApiClient.Shared.Language(s.Token!);
            var idx = System.Array.FindIndex(_languages, l => l.Code == current.Language);
            LanguageBox.SelectedIndex = idx >= 0 ? idx : 0;
        }
        catch { /* backend offline — leave empty */ }
        finally { _loadingLanguage = false; }
    }

    private async void OnLanguagePicked(object sender, SelectionChangedEventArgs e)
    {
        if (_loadingLanguage) return;
        var idx = LanguageBox.SelectedIndex;
        if (idx < 0 || idx >= _languages.Length) return;
        try { await ApiClient.Shared.SetLanguage(AppState.Current.Token!, _languages[idx].Code); }
        catch { /* ignore */ }
    }

    private static string Masked(string t) =>
        t.Length > 8 ? t[..6] + "…" + t[^4..] : "••••";
}
