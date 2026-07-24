using System;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace PdiVault.Views;

public sealed partial class WelcomePage : Page
{
    public WelcomePage() => InitializeComponent();

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
