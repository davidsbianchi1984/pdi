using System;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace PdiVault.Views;

public sealed partial class WelcomePage : Page
{
    /// The ten choices, each named in its own language. A language picker
    /// showing *Spanish* to somebody who reads Spanish is a picker they have
    /// to translate before they can use it, so these are endonyms and stay
    /// exactly as written — data rather than copy.
    private static readonly (string Tag, string Endonym)[] Languages =
    {
        ("en", "English"), ("es", "Español"), ("fr", "Français"),
        ("de", "Deutsch"), ("pt", "Português"), ("it", "Italiano"),
        ("ja", "日本語"), ("zh", "中文"), ("hi", "हिन्दी"), ("ar", "العربية"),
    };

    public WelcomePage()
    {
        InitializeComponent();
        foreach (var (tag, endonym) in Languages)
            LanguageBox.Items.Add(new ComboBoxItem { Content = endonym, Tag = tag });
        LanguageBox.SelectedIndex = 0;
        Localize();
    }

    /// Nobody reading this page has a tenant, so `L10n.T(key)` — which takes
    /// the language from `AppState.Current` — would answer every reader on
    /// earth in English. `DeviceLanguage()` is the only honest source here,
    /// and this repo's own L10n docstring has said so since it was written.
    private void Localize()
    {
        var lang = L10n.DeviceLanguage();
        Title.Text = L10n.T("wel.title", lang);
        // \u002F is '/', spelled so the scanner's comment-stripper cannot
        // mistake the URL's // for a comment and eat the rest of the line.
        BaseBox.Text = "http:\u002F\u002F127.0.0.1:8000";
        Sub.Text = L10n.T("wel.sub", lang);
        TokenBox.Header = L10n.T("wel.token", lang);
        TokenBox.PlaceholderText = L10n.T("nacc.id.ph", lang);
        BaseBox.Header = L10n.T("wel.server", lang);
        TenantKeyBox.Header = L10n.T("wel.tenantkey", lang);
        TenantKeyBox.PlaceholderText = L10n.T("wel.tenantkey.ph", lang);
        LanguageBox.Header = L10n.T("wel.language", lang);
        StartButton.Content = L10n.T("wel.unlock", lang);
        BackendHint.Text = L10n.T("wel.backend", lang)
            + "  PDI_CORS_ORIGINS=* uvicorn pdi.api:app";
    }

    private async void OnStart(object sender, RoutedEventArgs e)
    {
        var token = TokenBox.Password.Trim();
        var baseUrl = BaseBox.Text.Trim();
        if (token.Length == 0)
        {
            ShowError("Paste your vault token to continue.");
            return;
        }
        StartButton.IsEnabled = false;
        try
        {
            ApiClient.Shared.SetBase(baseUrl);
            // Before the validating call, not after: on a vault under
            // customer custody the validation itself needs the key.
            ApiClient.Shared.HoldKey(TenantKeyBox.Password.Trim());
            await ApiClient.Shared.Keys(token);   // 200 == valid token
            var language = (LanguageBox.SelectedItem as ComboBoxItem)?.Tag as string;
            if (language is { Length: > 0 } && language != "en")
            {
                try { await ApiClient.Shared.SetLanguage(token, language); }
                catch { /* language is a preference, not a sign-in blocker */ }
            }
            AppState.Current.SignIn(token, baseUrl);
            Frame.Navigate(typeof(ShellPage));
        }
        catch (Exception ex)
        {
            ShowError($"Couldn't unlock — check the token and server. ({ex.Message})");
            StartButton.IsEnabled = true;
        }
    }

    private void ShowError(string message)
    {
        ErrorText.Text = message;
        ErrorText.Visibility = Visibility.Visible;
    }
}
