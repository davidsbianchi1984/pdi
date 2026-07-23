using Microsoft.UI.Xaml;
using PdiVault.Views;

namespace PdiVault;

public sealed partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        Title = "PDI Vault";
        RootFrame.Navigate(AppState.Current.IsSignedIn ? typeof(ShellPage) : typeof(WelcomePage));
    }
}
