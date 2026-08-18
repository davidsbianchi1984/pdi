using System;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace PdiVault.Views;

/// <summary>The resident intelligence: the agent living in the vault
/// process — planner, closed tool registry, queryable datasets, embeddings,
/// local-only inference. The same engine a colocation or own-facility
/// deployment runs beside its data, reached here over the standard service.
/// The page repeats the honesty rules rather than smoothing them over:
/// leaves_host renders beside every tool and step, and the posture's
/// sentences are the server's own, verbatim.</summary>
public sealed partial class ResidentPage : Page
{
    public ResidentPage()
    {
        InitializeComponent();
        // In code rather than XAML: a XAML literal cannot be re-read when
        // the language changes, and this heading would be the English one.
        TitleText.Text = L10n.T("res.title");
        GoalBox.Header = L10n.T("res.plan");
        GoalBox.PlaceholderText = L10n.T("res.plan.ph");
        PlanButton.Content = L10n.T("res.plan.go");
        TasksHeader.Text = L10n.T("res.tasks");
        DatasetsHeader.Text = L10n.T("res.datasets");
        EmbedHeader.Text = L10n.T("res.embed");
        EmbedKeyBox.Header = L10n.T("res.embed.key");
        EmbedTextBox.Header = L10n.T("res.embed.text");
        EmbedButton.Content = L10n.T("res.embed.go");
        QueryBox.PlaceholderText = L10n.T("res.search.ph");
        SearchButton.Content = L10n.T("res.search.go");
        _ = LoadAsync();
    }

    private async System.Threading.Tasks.Task LoadAsync()
    {
        var s = AppState.Current;
        if (string.IsNullOrEmpty(s.Token)) return;
        try
        {
            var posture = await ApiClient.Shared.ResidentGetPosture(s.Token!);
            MeansText.Text = posture.Means;
            PostureText.Text =
                $"{L10n.T("res.hosting")}: {posture.HostingMode} · " +
                $"{L10n.T("res.model")}: " +
                $"{posture.LocalModel ?? L10n.T("res.nomodel")} · " +
                posture.Embedder;
            ToolsText.Text = string.Join("\n", posture.Tools
                .OrderBy(t => t.Name)
                .Select(t => $"{t.Name} — {t.Means} · " +
                             L10n.T(t.LeavesHost ? "res.leaves"
                                                 : "res.stays")));
            PrivacyText.Text = posture.Privacy;

            var tasks = await ApiClient.Shared.ResidentTasks(s.Token!);
            TasksList.Items.Clear();
            foreach (var task in tasks)
            {
                var panel = new StackPanel { Spacing = 2 };
                panel.Children.Add(new TextBlock
                {
                    Text = $"{task.Goal} — {task.Status}",
                    FontSize = 13,
                });
                foreach (var step in task.Steps)
                {
                    panel.Children.Add(new TextBlock
                    {
                        Text = $"{step.Position}. {step.Tool} — {step.Status}"
                             + (step.LeavesHost
                                ? " · " + L10n.T("res.leaves") : "")
                             + (step.Summary is null ? "" : " · " + step.Summary)
                             + (step.Error is null ? "" : " · " + step.Error),
                        FontSize = 11,
                    });
                }
                if (task.Status is "planned" or "failed")
                {
                    var run = new Button
                    {
                        Content = L10n.T("res.run"),
                        Background = null,
                    };
                    var tid = task.Id;
                    run.Click += async (_, _) =>
                    {
                        try
                        {
                            await ApiClient.Shared.ResidentRun(s.Token!, tid);
                            await LoadAsync();
                        }
                        catch (Exception ex) { ShowError(ex); }
                    };
                    panel.Children.Add(run);
                }
                TasksList.Items.Add(panel);
            }

            var datasets = await ApiClient.Shared.ResidentDatasets(s.Token!);
            DatasetsList.Items.Clear();
            foreach (var d in datasets)
            {
                var open = new Button
                {
                    Content = $"{d.Dataset} · {d.Rows}",
                    Background = null,
                };
                var name = d.Dataset;
                open.Click += async (_, _) =>
                {
                    try
                    {
                        var rows = await ApiClient.Shared.ResidentRows(
                            s.Token!, name);
                        RowsText.Text = string.Join(
                            "\n", rows.Rows.Select(r => r.ToString()));
                    }
                    catch (Exception ex) { ShowError(ex); }
                };
                DatasetsList.Items.Add(open);
            }
        }
        catch (Exception ex) { ShowError(ex); }
    }

    private async void OnPlan(object sender, RoutedEventArgs e)
    {
        var s = AppState.Current;
        if (string.IsNullOrEmpty(s.Token)
            || string.IsNullOrWhiteSpace(GoalBox.Text)) return;
        try
        {
            await ApiClient.Shared.ResidentPlan(s.Token!, GoalBox.Text.Trim());
            GoalBox.Text = "";
            ErrorText.Visibility = Visibility.Collapsed;
            await LoadAsync();
        }
        catch (Exception ex) { ShowError(ex); }
    }

    private async void OnEmbed(object sender, RoutedEventArgs e)
    {
        var s = AppState.Current;
        if (string.IsNullOrEmpty(s.Token)
            || string.IsNullOrWhiteSpace(EmbedKeyBox.Text)
            || string.IsNullOrWhiteSpace(EmbedTextBox.Text)) return;
        try
        {
            var outp = await ApiClient.Shared.ResidentEmbed(
                s.Token!, EmbedKeyBox.Text.Trim(), EmbedTextBox.Text);
            StatusText.Text = $"{outp.Key} · {outp.Embedder}";
            StatusText.Visibility = Visibility.Visible;
            EmbedTextBox.Text = "";
        }
        catch (Exception ex) { ShowError(ex); }
    }

    private async void OnSearch(object sender, RoutedEventArgs e)
    {
        var s = AppState.Current;
        if (string.IsNullOrEmpty(s.Token)
            || string.IsNullOrWhiteSpace(QueryBox.Text)) return;
        try
        {
            var found = await ApiClient.Shared.ResidentSearch(
                s.Token!, QueryBox.Text.Trim());
            MatchesText.Text = string.Join("\n", found.Matches
                .Select(m => $"{m.Key} · {m.Score:F3}"));
        }
        catch (Exception ex) { ShowError(ex); }
    }

    private void ShowError(Exception ex)
    {
        ErrorText.Text = ex.Message;
        ErrorText.Visibility = Visibility.Visible;
    }
}
