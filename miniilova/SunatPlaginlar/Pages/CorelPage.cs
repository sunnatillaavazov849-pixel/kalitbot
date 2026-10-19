using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using Sunat.Plaginlar.Services;

namespace Sunat.Plaginlar.Pages
{
    /// <summary>Kompyuterda topilgan CorelDRAW versiyalari va ularning GMS (plagin) papkalari.</summary>
    class CorelPage
    {
        readonly MainWindow _w;
        public CorelPage(MainWindow w) { _w = w; }

        public UIElement Build()
        {
            var installs = CorelLocator.Locate();
            var actions = new WrapPanel();
            actions.Children.Add(Ui.Pill("Qayta qidirish", Ui.PillKind.Secondary, _w.Refresh, small: true));
            actions.Children.Add(Margin(Ui.Pill("Papkani qo'lda qo'shish", Ui.PillKind.Secondary, AddManual, small: true)));
            if (!MainWindow.IsAdmin)
                actions.Children.Add(Margin(Ui.Pill("Administrator sifatida ochish", Ui.PillKind.Ghost, _w.RestartAsAdmin, small: true)));

            var page = Ui.V(28,
                Ui.V(8, Ui.H1("CorelDRAW versiyalari"),
                     Ui.Sub("CorelDRAW 2020–2026 avtomatik qidiriladi. Plaginlar shu versiyalarning GMS papkasiga o'rnatiladi.")),
                actions);

            if (installs.Count == 0)
            {
                page.Children.Add(Ui.Card(Ui.V(10,
                    Ui.T("CorelDRAW topilmadi", 18, FontWeights.SemiBold, Ui.Ink, false, Ui.Display),
                    Ui.T("CorelDRAW o'rnatilganiga ishonchingiz komil bo'lsa, uni bir marta ochib yoping va «Qayta qidirish»ni bosing. " +
                         "Yoki GMS papkasini qo'lda qo'shing, masalan:\nC:\\Program Files\\Corel\\CorelDRAW Graphics Suite 2020\\Draw\\GMS",
                         14, null, Ui.Muted, true))));
                return page;
            }

            foreach (var ci in installs) page.Children.Add(InstallCard(ci));
            return page;
        }

        static FrameworkElement Margin(FrameworkElement e)
        {
            e.Margin = new Thickness(8, 0, 0, 0);
            return e;
        }

        UIElement FolderRow(string label, string path, bool exists, string hint)
        {
            var row = new DockPanel();
            var open = Ui.Pill("Ochish", Ui.PillKind.Secondary, () => MainWindow.OpenFolder(path), small: true);
            DockPanel.SetDock(open, Dock.Right);
            row.Children.Add(open);
            var chip = exists ? Ui.Chip("bor", Ui.GreenFg, Ui.GreenBg) : Ui.Chip("yo'q", Ui.AmberFg, Ui.AmberBg);
            var txt = Ui.V(4, Ui.H(8, Ui.T(label, 13, FontWeights.SemiBold, Ui.Ink), chip),
                           Ui.T(path, 12, null, Ui.Muted, true, Ui.Mono),
                           hint == null ? null : Ui.T(hint, 12, null, Ui.Faint, true));
            txt.Margin = new Thickness(0, 0, 12, 0);
            row.Children.Add(txt);
            return row;
        }

        UIElement InstallCard(CorelInstall ci)
        {
            var plugins = PluginStore.All()
                .Where(p => p.Files.Any(f => File.Exists(f) && (f.StartsWith(ci.UserGms, System.StringComparison.OrdinalIgnoreCase)
                                                             || f.StartsWith(ci.ProgramGms, System.StringComparison.OrdinalIgnoreCase))))
                .Select(p => p.Name).ToList();

            var head = new DockPanel();
            if (ci.Manual)
            {
                var remove = Ui.Pill("Olib tashlash", Ui.PillKind.Ghost, () =>
                {
                    CorelLocator.SetManualDirs(CorelLocator.ManualDirs().Where(d => !d.Equals(ci.Root, System.StringComparison.OrdinalIgnoreCase)));
                    _w.Refresh();
                }, small: true);
                DockPanel.SetDock(remove, Dock.Right);
                head.Children.Add(remove);
            }
            head.Children.Add(Ui.V(2, Ui.T(ci.Title, 20, FontWeights.SemiBold, Ui.Ink, false, Ui.Display),
                                      Ui.T(ci.Root, 12, null, Ui.Muted, true, Ui.Mono)));

            var body = Ui.V(14, head, Ui.Divider());
            if (ci.Manual)
                body.Children.Add(FolderRow("GMS papka", ci.ProgramGms, Directory.Exists(ci.ProgramGms), null));
            else
            {
                body.Children.Add(FolderRow("Foydalanuvchi papkasi", ci.UserGms, Directory.Exists(ci.UserGms),
                    ci.UserProfileExists ? "Tavsiya etiladi: administrator huquqi kerak emas."
                                         : "CorelDRAW bu foydalanuvchida hali ochilmagan."));
                body.Children.Add(FolderRow("Dastur papkasi", ci.ProgramGms, Directory.Exists(ci.ProgramGms),
                    "Bu yerga yozish uchun administrator huquqi kerak."));
            }
            body.Children.Add(Ui.T(plugins.Count == 0 ? "O'rnatilgan plaginlar: yo'q" : "O'rnatilgan plaginlar: " + string.Join(", ", plugins),
                                   13, FontWeights.Medium, Ui.Ink, true));
            return Ui.Card(body, 24);
        }

        void AddManual()
        {
            using (var dlg = new System.Windows.Forms.FolderBrowserDialog
            {
                Description = "CorelDRAW'ning GMS papkasini tanlang (…\\Draw\\GMS)",
                ShowNewFolderButton = true,
            })
            {
                if (dlg.ShowDialog() != System.Windows.Forms.DialogResult.OK) return;
                var dirs = CorelLocator.ManualDirs();
                dirs.Add(dlg.SelectedPath);
                CorelLocator.SetManualDirs(dirs);
                _w.Refresh();
                _w.Toast("Papka qo'shildi");
            }
        }
    }
}
