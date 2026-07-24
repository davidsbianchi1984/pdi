using System.Linq;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

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
        ImproveCategory.ItemsSource = ImproveCategories
            .Select(c => char.ToUpper(c[0]) + c[1..]).ToList();
        ImproveCategory.SelectedIndex = 0;
        ImproveRating.ItemsSource = new[] { "—", "1", "2", "3", "4", "5" };
        ImproveRating.SelectedIndex = 0;
    }

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
            PreTranslateToggle.IsOn = (current.Mode ?? "pre") == "pre";
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
                ImproveTally.Text = "So far: " + string.Join(" · ", parts);
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
            ImproveThanks.Text = "Thank you — sent.";
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
}
