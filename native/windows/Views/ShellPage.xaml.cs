using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace PdiVault.Views;

public sealed partial class ShellPage : Page
{
    public ShellPage()
    {
        InitializeComponent();
        LocalizeNav();
        ContentFrame.Navigate(typeof(OverviewPage));
    }

    /// Nav labels follow the tenant's chosen language (chrome localization);
    /// re-applied on every pane selection so a language change in Overview
    /// takes effect immediately.
    private void LocalizeNav()
    {
        foreach (var entry in Nav.MenuItems)
            if (entry is NavigationViewItem nvi && nvi.Tag is string tag)
                nvi.Content = L10n.T($"tab.{tag}");
        // Not a menu item: this one sits in the pane footer, which the
        // loop above does not walk. It said "Sign out" in every language,
        // and the table did not even hold the row. QRME found this in its
        // own copy of this file at 0.46.9 and JIM-mini at 0.47.2; this is
        // the third product with the same nav, and nobody had looked.
        SignOutButton.Content = L10n.T("action.sign_out");
    }

    private void OnSelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        LocalizeNav();
        if (args.SelectedItem is not NavigationViewItem item) return;
        switch (item.Tag as string)
        {
            case "overview": ContentFrame.Navigate(typeof(OverviewPage)); break;
            case "vault": ContentFrame.Navigate(typeof(VaultPage)); break;
            case "audit": ContentFrame.Navigate(typeof(AuditPage)); break;
            case "robots": ContentFrame.Navigate(typeof(RobotsPage)); break;
            case "connectors": ContentFrame.Navigate(typeof(ConnectorsPage)); break;
            case "transfers": ContentFrame.Navigate(typeof(TransfersPage)); break;
            case "resident": ContentFrame.Navigate(typeof(ResidentPage)); break;
        }
    }

    private void OnSignOut(object sender, RoutedEventArgs e)
    {
        AppState.Current.SignOut();
        Frame.Navigate(typeof(WelcomePage));
    }
}
