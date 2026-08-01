using System;
using System.Linq;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;

namespace PdiVault.Views;

public sealed partial class AuditPage : Page
{
    public record EntryRow(int Seq, string Action, string? Ref, string? Category);

    public AuditPage()
    {
        InitializeComponent();
        // The card reads three stored choices, so it has to be told when
        // the page appears rather than only when a button is pressed.
        Loaded += (_, _) => RefreshProblemsCard();
    }

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

    // ---- When something breaks ------------------------------------------
    //
    // The notice that has to be answered before anything leaves this machine.
    // The sending half landed last round and answered AwaitingNotice on every
    // launch because there was no surface to answer it on — safe to be wrong
    // in that direction, and still wrong: a mechanism nobody can reach is a
    // mechanism nobody chose.
    //
    // The preview is built by Problems.Report, the same call the sender posts,
    // so what is on screen is the payload rather than a description of it. A
    // preview that could drift from the message would be worse than none,
    // because it would look like a promise.

    private void RefreshProblemsCard()
    {
        var hasCollector = Problems.CollectorUrl().Length > 0;
        var answered = Problems.NoticeAnswered();

        if (!hasCollector)
        {
            // Not a failure and not a thing to hide: this build has no address
            // compiled in, so there is nothing to consent to.
            ProblemsExplain.Text = "This build reports nowhere. Failures are " +
                "counted on this machine and never leave it.";
            ProblemsAsk.Visibility = Visibility.Collapsed;
            ProblemsSwitch.Visibility = Visibility.Collapsed;
            return;
        }
        if (!answered)
        {
            ProblemsExplain.Text = "This app can send a count of what failed " +
                "— the operation and the HTTP status, the day, and how many " +
                "times. Not what you typed, not who you are, not which " +
                "profile. Nothing that identifies you or anyone else.";
            ProblemsAsk.Visibility = Visibility.Visible;
            ProblemsSwitch.Visibility = Visibility.Collapsed;
            return;
        }
        ProblemsExplain.Text = "Counts of what failed. Never what you typed.";
        ProblemsAsk.Visibility = Visibility.Collapsed;
        ProblemsSwitch.Visibility = Visibility.Visible;
        ProblemsSwitch.IsOn = Problems.SendingEnabled();
    }

    private async void OnProblemsYes(object sender, RoutedEventArgs e)
    {
        Problems.AnswerNotice(true);
        RefreshProblemsCard();
        // The first moment a send is permitted. Doing it now rather than at
        // the next launch means the person who just agreed watches the buffer
        // drain, instead of being told something happened later.
        await Problems.Send();
    }

    private void OnProblemsNo(object sender, RoutedEventArgs e)
    {
        Problems.AnswerNotice(false);
        RefreshProblemsCard();
    }

    private void OnProblemsToggled(object sender, RoutedEventArgs e) =>
        Problems.SetSending(ProblemsSwitch.IsOn);

    private void OnProblemsPreview(object sender, RoutedEventArgs e)
    {
        if (ProblemsPreview.Visibility == Visibility.Visible)
        {
            ProblemsPreview.Visibility = Visibility.Collapsed;
            ProblemsPreviewButton.Content = "Show what would be sent";
            return;
        }
        var owed = Problems.Report()["problems"]
            as List<Dictionary<string, object>> ?? new();
        ProblemsPreview.Text = owed.Count == 0
            ? "Nothing is owed. Either nothing has failed, or everything that "
              + "has was already reported."
            : string.Join("\n", owed.Select(r =>
                $"{r["op"]} → {r["status"]}  ×{r["count"]}  {r["day"]}"));
        ProblemsPreview.Visibility = Visibility.Visible;
        ProblemsPreviewButton.Content = "Hide what would be sent";
    }
}
