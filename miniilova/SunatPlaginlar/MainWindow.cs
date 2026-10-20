using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Security.Principal;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using Sunat.Plaginlar.Pages;
using Sunat.Plaginlar.Services;

namespace Sunat.Plaginlar
{
    /// <summary>Asosiy oyna: chapda panel, o'ngda ish maydoni, ustida dialog va bildirishnoma qatlami.</summary>
    class MainWindow : Window
    {
        readonly ContentControl _content = new ContentControl();
        readonly ScrollViewer _scroll;
        readonly Grid _overlay = new Grid { Visibility = Visibility.Collapsed, Background = Ui.Dim };
        readonly Border _toast;
        readonly TextBlock _toastText;
        readonly DispatcherTimer _toastTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(4) };
        readonly Dictionary<string, Button> _nav = new Dictionary<string, Button>();
        string _current;

        public MainWindow()
        {
            Title = AppInfo.Name;
            Width = 1140;
            Height = 760;
            MinWidth = 900;
            MinHeight = 600;
            Background = Ui.Bg;
            FontFamily = Ui.Font;
            WindowStartupLocation = WindowStartupLocation.CenterScreen;
            UseLayoutRounding = true;
            TextOptions.SetTextFormattingMode(this, TextFormattingMode.Display);
            try
            {
                using (var ico = typeof(MainWindow).Assembly.GetManifestResourceStream("app.ico"))
                    Icon = System.Windows.Media.Imaging.BitmapFrame.Create(ico,
                        System.Windows.Media.Imaging.BitmapCreateOptions.None, System.Windows.Media.Imaging.BitmapCacheOption.OnLoad);
            }
            catch { }

            var root = new Grid();
            root.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(260) });
            root.ColumnDefinitions.Add(new ColumnDefinition());

            var side = BuildSidebar();
            Grid.SetColumn(side, 0);
            root.Children.Add(side);

            _scroll = new ScrollViewer
            {
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled,
                Content = new Border { Padding = new Thickness(44, 40, 44, 48), Child = _content },
            };
            Grid.SetColumn(_scroll, 1);
            root.Children.Add(_scroll);

            _toastText = Ui.T("", 14, FontWeights.Medium, Ui.OnInk, true);
            _toast = new Border
            {
                Background = Ui.Ink,
                CornerRadius = new CornerRadius(999),
                Padding = new Thickness(22, 12, 22, 12),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Bottom,
                Margin = new Thickness(0, 0, 0, 28),
                MaxWidth = 640,
                Visibility = Visibility.Collapsed,
                Child = _toastText,
            };
            Grid.SetColumnSpan(_toast, 2);
            root.Children.Add(_toast);
            _toastTimer.Tick += (s, e) => { _toast.Visibility = Visibility.Collapsed; _toastTimer.Stop(); };

            Grid.SetColumnSpan(_overlay, 2);
            root.Children.Add(_overlay);

            Content = root;
            Navigate("plugins");
            Catalog.LoadAsync().ContinueWith(_ => Dispatcher.Invoke(() => { if (_current == "plugins") Refresh(); }));
        }

        UIElement BuildSidebar()
        {
            var logo = Ui.H(12,
                Ui.Badge("S", 42),
                Ui.V(0, Ui.T("Sunat.cc", 17, FontWeights.Bold, Ui.Ink, false, Ui.Display), Ui.T("Plaginlar", 13, null, Ui.Muted)));

            var nav = new StackPanel { Margin = new Thickness(0, 28, 0, 0) };
            void Add(string key, string icon, string text)
            {
                var b = Ui.Nav(icon, text, () => Navigate(key));
                b.Margin = new Thickness(0, 0, 0, 4);
                _nav[key] = b;
                nav.Children.Add(b);
            }
            Add("plugins", "🧩", "Plaginlar");
            Add("add", "⬇", "Plaginni o'rnatish");
            Add("corel", "🖥", "CorelDRAW versiyalari");
            Add("help", "💬", "Yordam / aloqa");

            var midText = Ui.T(Hardware.MachineId, 18, FontWeights.SemiBold, Ui.Ink, false, Ui.Mono);
            var idCard = new Border
            {
                CornerRadius = new CornerRadius(20),
                Background = Ui.Pastel(0.55),
                Padding = new Thickness(16),
                Child = Ui.V(8,
                    Ui.Label("Kompyuter ID"),
                    midText,
                    Ui.Pill("Nusxalash", Ui.PillKind.Secondary, () => Copy(Hardware.MachineId, "Kompyuter ID nusxalandi"), small: true)),
            };
            ((FrameworkElement)((StackPanel)idCard.Child).Children[2]).HorizontalAlignment = HorizontalAlignment.Left;

            var dock = new DockPanel { LastChildFill = false };
            var top = Ui.V(0, logo, nav);
            DockPanel.SetDock(top, Dock.Top);
            dock.Children.Add(top);
            var bottom = Ui.V(10, idCard, Ui.T("v" + AppInfo.Version, 11, null, Ui.Faint));
            DockPanel.SetDock(bottom, Dock.Bottom);
            dock.Children.Add(bottom);

            return new Border
            {
                Background = Ui.Surface,
                BorderBrush = Ui.Line,
                BorderThickness = new Thickness(0, 0, 1, 0),
                Padding = new Thickness(20, 28, 20, 20),
                Child = dock,
            };
        }

        public void Navigate(string key)
        {
            _current = key;
            foreach (var kv in _nav) Ui.SetNavSelected(kv.Value, kv.Key == key);
            UIElement page;
            switch (key)
            {
                case "add": page = new AddPage(this).Build(); break;
                case "corel": page = new CorelPage(this).Build(); break;
                case "help": page = new HelpPage(this).Build(); break;
                default: page = new PluginsPage(this).Build(); break;
            }
            _content.Content = page;
            _scroll.ScrollToTop();
        }

        public void Refresh() => Navigate(_current);

        /// <summary>Tanlangan paket bilan o'rnatish sahifasini ochadi.</summary>
        public void ShowInstall(PackageInfo pkg)
        {
            _current = "add";
            foreach (var kv in _nav) Ui.SetNavSelected(kv.Value, kv.Key == "add");
            _content.Content = new AddPage(this, pkg).Build();
            _scroll.ScrollToTop();
        }

        public void Toast(string text, bool error = false)
        {
            _toastText.Text = text;
            _toast.Background = error ? Ui.RedFg : Ui.Ink;
            _toast.Visibility = Visibility.Visible;
            _toastTimer.Stop();
            _toastTimer.Start();
        }

        public void Copy(string text, string message)
        {
            for (int i = 0; i < 5; i++)
            {
                try { Clipboard.SetText(text); Toast(message); return; }
                catch { System.Threading.Thread.Sleep(60); }
            }
            Toast("Nusxalab bo'lmadi. Matnni qo'lda belgilab oling.", true);
        }

        public static void OpenUrl(string url)
        {
            try { Process.Start(new ProcessStartInfo(url) { UseShellExecute = true }); } catch { }
        }

        public static void OpenFolder(string path)
        {
            try
            {
                System.IO.Directory.CreateDirectory(path);
                Process.Start("explorer.exe", "\"" + path + "\"");
            }
            catch { }
        }

        public static bool IsAdmin
        {
            get
            {
                try { return new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator); }
                catch { return false; }
            }
        }

        public void RestartAsAdmin()
        {
            try
            {
                Process.Start(new ProcessStartInfo(Process.GetCurrentProcess().MainModule.FileName)
                {
                    UseShellExecute = true,
                    Verb = "runas",
                });
                Application.Current.Shutdown();
            }
            catch
            {
                Toast("Administrator sifatida ochilmadi.", true);
            }
        }

        /// <summary>Oyna ichidagi dialog. Har bir tugma bosilganda dialog yopiladi va amal bajariladi.</summary>
        public void Dialog(string title, UIElement body, params (string text, Ui.PillKind kind, Action action)[] buttons)
        {
            var row = new WrapPanel { HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 8, 0, 0) };
            foreach (var (text, kind, action) in buttons)
            {
                var b = Ui.Pill(text, kind, () => { CloseDialog(); action?.Invoke(); });
                b.Margin = new Thickness(8, 0, 0, 0);
                row.Children.Add(b);
            }
            var card = Ui.Card(Ui.V(14, Ui.T(title, 20, FontWeights.SemiBold, Ui.Ink, true, Ui.Display), body, row), 28, 28);
            card.MaxWidth = 520;
            card.Margin = new Thickness(24);
            card.HorizontalAlignment = HorizontalAlignment.Center;
            card.VerticalAlignment = VerticalAlignment.Center;
            _overlay.Children.Clear();
            _overlay.Children.Add(card);
            _overlay.Visibility = Visibility.Visible;
        }

        public void CloseDialog()
        {
            _overlay.Visibility = Visibility.Collapsed;
            _overlay.Children.Clear();
        }

        protected override void OnPreviewKeyDown(KeyEventArgs e)
        {
            if (e.Key == Key.Escape && _overlay.Visibility == Visibility.Visible)
            {
                CloseDialog();
                e.Handled = true;
            }
            base.OnPreviewKeyDown(e);
        }
    }
}
