using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace PdiVault.Views;

public sealed partial class ShellPage : Page
{
    public ShellPage()
    {
        InitializeComponent();
        ContentFrame.Navigate(typeof(OverviewPage));
    }

    private void OnSelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        if (args.SelectedItem is not NavigationViewItem item) return;
        switch (item.Tag as string)
        {
            case "overview": ContentFrame.Navigate(typeof(OverviewPage)); break;
            case "vault": ContentFrame.Navigate(typeof(VaultPage)); break;
            case "audit": ContentFrame.Navigate(typeof(AuditPage)); break;
            case "robots": ContentFrame.Navigate(typeof(RobotsPage)); break;
        }
    }

    private void OnSignOut(object sender, RoutedEventArgs e)
    {
        AppState.Current.SignOut();
        Frame.Navigate(typeof(WelcomePage));
    }
}
