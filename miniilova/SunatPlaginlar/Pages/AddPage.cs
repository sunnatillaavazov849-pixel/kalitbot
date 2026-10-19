using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Microsoft.Win32;
using Sunat.Plaginlar.Services;

namespace Sunat.Plaginlar.Pages
{
    /// <summary>Plagin qo'shish: ZIP tanlash -> CorelDRAW versiyalarini belgilash -> o'rnatish.</summary>
    class AddPage
    {
        readonly MainWindow _w;
        readonly StackPanel _details = new StackPanel();
        PackageInfo _pkg;

        public AddPage(MainWindow w) { _w = w; }

        public UIElement Build()
        {
            var page = Ui.V(28,
                Ui.V(8, Ui.H1("Plagin qo'shish"),
                     Ui.Sub("Botdan olingan ZIP faylni tanlang yoki shu yerga sudrab tashlang. Dastur plaginni CorelDRAW papkasiga o'zi joylaydi.")),
                DropZone(),
                _details);

            // ZIP ochilgan papkadan ishga tushirilgan bo'lsa - yonidagi plaginni darhol taklif qilamiz
            string exeDir = AppDomain.CurrentDomain.BaseDirectory;
            var nearby = PackageInstaller.FindNearby(exeDir);
            if (nearby.Count > 0) Show(nearby[0]);
            return page;
        }

        UIElement DropZone()
        {
            var choose = Ui.Pill("ZIP faylni tanlash", Ui.PillKind.Primary, Browse);
            choose.HorizontalAlignment = HorizontalAlignment.Center;
            var inner = Ui.V(14,
                Center(Ui.T("⬇", 34, null, Ui.Ink)),
                Center(Ui.T("Plagin ZIP faylini shu yerga tashlang", 18, FontWeights.SemiBold, Ui.Ink, true, Ui.Display)),
                Center(Ui.T("yoki", 13, null, Ui.Muted)),
                choose);

            var zone = new Border
            {
                CornerRadius = new CornerRadius(28),
                Background = Ui.Pastel(0.45),
                BorderBrush = Ui.Line,
                BorderThickness = new Thickness(1),
                Padding = new Thickness(32, 40, 32, 40),
                AllowDrop = true,
                Child = inner,
            };
            zone.DragOver += (s, e) =>
            {
                e.Effects = e.Data.GetDataPresent(DataFormats.FileDrop) ? DragDropEffects.Copy : DragDropEffects.None;
                e.Handled = true;
            };
            zone.DragEnter += (s, e) => zone.BorderBrush = Ui.Ink;
            zone.DragLeave += (s, e) => zone.BorderBrush = Ui.Line;
            zone.Drop += (s, e) =>
            {
                zone.BorderBrush = Ui.Line;
                if (e.Data.GetData(DataFormats.FileDrop) is string[] files && files.Length > 0) Load(files[0]);
            };
            return zone;
        }

        static FrameworkElement Center(FrameworkElement e)
        {
            e.HorizontalAlignment = HorizontalAlignment.Center;
            if (e is TextBlock t) t.TextAlignment = TextAlignment.Center;
            return e;
        }

        void Browse()
        {
            var dlg = new OpenFileDialog
            {
                Title = "Plagin paketini tanlang",
                Filter = "Plagin paketi (*.zip;manifest.json)|*.zip;manifest.json|Barcha fayllar (*.*)|*.*",
                InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile) + "\\Downloads",
            };
            if (dlg.ShowDialog(_w) == true) Load(dlg.FileName);
        }

        void Load(string path)
        {
            try
            {
                Show(PackageInstaller.Read(path));
            }
            catch (Exception ex)
            {
                _w.Toast(PackageInstaller.Explain(ex), true);
            }
        }

        void Show(PackageInfo pkg)
        {
            _pkg = pkg;
            _details.Children.Clear();

            var installs = CorelLocator.Locate();
            var head = Ui.H(14, Ui.Badge(pkg.Prefix, 52),
                Ui.V(2,
                    Ui.T(pkg.Name, 22, FontWeights.SemiBold, Ui.Ink, false, Ui.Display),
                    Ui.T($"{pkg.Prefix}{(string.IsNullOrEmpty(pkg.Version) ? "" : " · versiya " + pkg.Version)} · {Path.GetFileName(pkg.SourcePath)}", 12, null, Ui.Muted)));
            ((FrameworkElement)head.Children[1]).VerticalAlignment = VerticalAlignment.Center;

            var body = Ui.V(18, head);
            if (!string.IsNullOrWhiteSpace(pkg.Description))
                body.Children.Add(Gap(Ui.T(pkg.Description, 14, null, Ui.Muted, true), 18));
            body.Children.Add(Gap(Ui.Divider(), 18));

            var targets = new List<(CheckBox box, RadioButton user, RadioButton prog, CorelInstall ci)>();
            if (installs.Count == 0)
            {
                body.Children.Add(Gap(Ui.T("CorelDRAW topilmadi. «CorelDRAW versiyalari» bo'limida qo'lda papka tanlashingiz mumkin " +
                                           "yoki CorelDRAW'ni bir marta ochib, qayta urinib ko'ring.", 14, null, Ui.RedFg, true), 18));
            }
            else
            {
                body.Children.Add(Gap(Ui.Label("Qaysi CorelDRAW'ga o'rnatamiz"), 18));
                foreach (var ci in installs)
                {
                    var box = new CheckBox
                    {
                        IsChecked = true,
                        Content = Ui.T(ci.Title, 15, FontWeights.SemiBold, Ui.Ink),
                        VerticalContentAlignment = VerticalAlignment.Center,
                    };
                    string group = "g" + targets.Count;
                    var user = new RadioButton
                    {
                        GroupName = group,
                        IsChecked = ci.UserProfileExists,
                        IsEnabled = ci.UserProfileExists,
                        Content = Ui.T("Foydalanuvchi papkasi (tavsiya) — " + ci.UserGms, 12, null, Ui.Muted, true),
                    };
                    var prog = new RadioButton
                    {
                        GroupName = group,
                        IsChecked = !ci.UserProfileExists,
                        Content = Ui.T("Dastur papkasi (administrator kerak) — " + ci.ProgramGms, 12, null, Ui.Muted, true),
                    };
                    var opts = Ui.V(6, user, prog);
                    opts.Margin = new Thickness(26, 6, 0, 0);
                    var block = new Border
                    {
                        CornerRadius = new CornerRadius(18),
                        Background = Ui.Surface,
                        Padding = new Thickness(16),
                        Margin = new Thickness(0, 10, 0, 0),
                        Child = Ui.V(0, box, opts),
                    };
                    box.Checked += (s, e) => opts.IsEnabled = true;
                    box.Unchecked += (s, e) => opts.IsEnabled = false;
                    body.Children.Add(block);
                    targets.Add((box, user, prog, ci));
                }
            }

            var install = Ui.Pill("O'rnatish", Ui.PillKind.Primary, () => Install(targets.Where(t => t.box.IsChecked == true)
                .Select(t => t.user.IsChecked == true ? t.ci.UserGms : t.ci.ProgramGms).ToList()));
            install.IsEnabled = installs.Count > 0;
            var row = Ui.H(10, install, Ui.Pill("Boshqa fayl", Ui.PillKind.Secondary, Browse));
            row.Margin = new Thickness(0, 20, 0, 0);
            body.Children.Add(row);
            body.Children.Add(Gap(Ui.T("O'rnatishdan oldin CorelDRAW'ni yoping.", 12, null, Ui.Muted), 10));

            _details.Children.Add(Ui.Card(body, 28));
        }

        static FrameworkElement Gap(FrameworkElement e, double top)
        {
            e.Margin = new Thickness(0, top, 0, 0);
            return e;
        }

        void Install(List<string> dirs)
        {
            if (_pkg == null) return;
            if (dirs.Count == 0)
            {
                _w.Toast("Kamida bitta CorelDRAW versiyasini belgilang.", true);
                return;
            }
            try
            {
                var files = PackageInstaller.Install(_pkg, dirs);
                PluginStore.SaveInstalled(_pkg, files);
            }
            catch (UnauthorizedAccessException)
            {
                if (MainWindow.IsAdmin)
                {
                    _w.Toast("Papkaga yozib bo'lmadi. Antivirus to'sayotgan bo'lishi mumkin.", true);
                    return;
                }
                _w.Dialog("Administrator huquqi kerak",
                    Ui.T("Dastur papkasiga yozish uchun dasturni administrator sifatida qayta ochish kerak. " +
                         "Yoki «Foydalanuvchi papkasi»ni tanlang.", 14, null, Ui.Muted, true),
                    ("Bekor qilish", Ui.PillKind.Secondary, null),
                    ("Administrator sifatida ochish", Ui.PillKind.Primary, _w.RestartAsAdmin));
                return;
            }
            catch (Exception ex)
            {
                _w.Toast(PackageInstaller.Explain(ex), true);
                return;
            }

            var p = PluginStore.Get(_pkg.Prefix);
            var rid = Ui.T(p.RequestId, 26, FontWeights.Bold, Ui.Ink, false, Ui.Mono);
            rid.HorizontalAlignment = HorizontalAlignment.Center;
            _w.Dialog($"{_pkg.Name} o'rnatildi",
                Ui.V(14,
                    Ui.T("Endi shu so'rov ID'ni botga yuboring. To'lovdan keyin bot faollashtirish kodini beradi.", 14, null, Ui.Muted, true),
                    new Border { CornerRadius = new CornerRadius(18), Background = Ui.Pastel(0.6), Padding = new Thickness(18), Child = rid },
                    Ui.T("CorelDRAW'da plagin ko'rinmasa: Tools → Macros → Macro Manager (yoki Alt+F11) orqali tekshiring. Botdagi «📖 O'rnatish» bo'limida video bor.",
                         12, null, Ui.Muted, true)),
                ("Nusxalash", Ui.PillKind.Secondary, () => _w.Copy(p.RequestId, "So'rov ID nusxalandi — endi botga yuboring")),
                ("Botni ochish", Ui.PillKind.Secondary, () => MainWindow.OpenUrl(PluginStore.BotUrl())),
                ("Plaginlarim", Ui.PillKind.Primary, () => _w.Navigate("plugins")));
        }
    }
}
