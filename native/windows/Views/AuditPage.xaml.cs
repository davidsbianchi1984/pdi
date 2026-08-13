using System;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;
using System.Collections.Generic;

namespace PdiVault.Views;

public sealed partial class AuditPage : Page
{
    public record EntryRow(int Seq, string Action, string? Ref, string? Category);

    public AuditPage()
    {
        InitializeComponent();
        TitleText.Text = L10n.T("tab.audit");
        DescText.Text = L10n.T("naud.desc");
        StatusText.Text = L10n.T("naud.verifying");
        CountText.Text = L10n.T("naud.events").Replace("{n}", "0");
        ProblemsTitle.Text = L10n.T("prb.title");
        ProblemsYes.Content = L10n.T("prb.send");
        ProblemsNo.Content = L10n.T("prb.donot");
        ProblemsSwitch.Header = L10n.T("prb.toggle");
        ProblemsPreviewButton.Content = L10n.T("prb.show");
        ProblemsKeyBox.PlaceholderText = L10n.T("prob.key.ph");
        ProblemsFetchButton.Content = L10n.T("prob.fetch");
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
            StatusText.Text = v.Intact ? L10n.T("naud.intact") : L10n.T("naud.broken");
        }
        catch (Exception ex) { StatusText.Text = ex.Message; }

        try
        {
            var entries = await ApiClient.Shared.AuditEntries(s.Token!);
            CountText.Text = L10n.T("naud.events").Replace("{n}", entries.Length.ToString());
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
            ProblemsExplain.Text = L10n.T("prb.nowhere");
            ProblemsAsk.Visibility = Visibility.Collapsed;
            ProblemsSwitch.Visibility = Visibility.Collapsed;
            return;
        }
        if (!answered)
        {
            ProblemsExplain.Text = L10n.T("prb.can");
            ProblemsAsk.Visibility = Visibility.Visible;
            ProblemsSwitch.Visibility = Visibility.Collapsed;
            return;
        }
        ProblemsExplain.Text = L10n.T("prb.never");
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

    // The other end of the wire: what has reached this deployment's own
    // backend, from every client of it. Reading needs PDI_PROBLEMS_KEY (or a
    // caller on the backend's machine); a refusal is rendered verbatim.
    private async void OnProblemsFetch(object sender, RoutedEventArgs e)
    {
        try
        {
            var r = await ApiClient.Shared.ProblemRows(ProblemsKeyBox.Password);
            ProblemsServerRows.Text = r.Rows.Length == 0
                ? L10n.T("prob.none")
                : string.Join("\n", r.Rows.Select(row =>
                    $"{row.Op}  {row.StatusCode}  ×{row.Count}  " +
                    $"{row.Source} {row.AppVersion} · {row.Platform} · {row.Day}"));
        }
        catch (Exception ex) { ProblemsServerRows.Text = ex.Message; }
        ProblemsServerRows.Visibility = Visibility.Visible;
    }

    private void OnProblemsPreview(object sender, RoutedEventArgs e)
    {
        if (ProblemsPreview.Visibility == Visibility.Visible)
        {
            ProblemsPreview.Visibility = Visibility.Collapsed;
            ProblemsPreviewButton.Content = L10n.T("prb.show");
            return;
        }
        var owed = Problems.Report()["problems"]
            as List<Dictionary<string, object>> ?? new();
        ProblemsPreview.Text = owed.Count == 0
            ? L10n.T("prb.owed.none")
            : string.Join("\n", owed.Select(r =>
                $"{r["op"]} → {r["status"]}  ×{r["count"]}  {r["day"]}"));
        ProblemsPreview.Visibility = Visibility.Visible;
        ProblemsPreviewButton.Content = L10n.T("prb.hide");
    }
}
