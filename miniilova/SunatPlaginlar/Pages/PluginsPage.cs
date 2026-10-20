using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.Win32;
using Sunat.Core;
using Sunat.Plaginlar.Services;

namespace Sunat.Plaginlar.Pages
{
    /// <summary>
    /// Plaginlar: saytdagi ro'yxat + shu kompyuterda o'rnatilganlar. Har bir plagin uchun:
    /// so'rov kodi -> "Saytda sotib olish" -> ZIP'ni o'rnatish -> kodni kiritish; dezaktivatsiya.
    /// </summary>
    class PluginsPage
    {
        readonly MainWindow _w;
        readonly StackPanel _list = new StackPanel();
        public PluginsPage(MainWindow w) { _w = w; }

        class Item
        {
            public string Prefix, Name, Version, Tagline, Price;
            public CatalogPlugin Catalog;
            public InstalledPlugin Installed;
            public string RequestId => Licensing.RequestId(Prefix, Hardware.MachineId);
            public bool IsActive => Installed != null && Installed.IsActive;
        }

        public UIElement Build()
        {
            var page = Ui.V(28,
                Ui.V(8, Ui.H1("Plaginlar"),
                     Ui.Sub("Plaginni tanlang: so'rov kodini saytga kiriting, to'lovdan keyin plaginni o'rnating va kodni shu yerga yozing.")),
                _list);
            if (Catalog.Last != null) Fill(Catalog.Last);
            else
            {
                _list.Children.Add(Ui.T("Plaginlar ro'yxati yuklanmoqda…", 14, null, Ui.Muted));
                Catalog.LoadAsync().ContinueWith(t => _w.Dispatcher.Invoke(() => Fill(t.Result)));
            }
            return page;
        }

        void Fill(CatalogResult cat)
        {
            _list.Children.Clear();
            var installed = PluginStore.All().ToDictionary(p => p.Prefix);
            var items = new List<Item>();
            foreach (var c in cat.Plugins)
            {
                installed.TryGetValue(c.Prefix.ToUpperInvariant(), out var inst);
                items.Add(new Item
                {
                    Prefix = c.Prefix.ToUpperInvariant(), Name = c.Name, Version = c.Version, Tagline = c.Tagline,
                    Price = c.PriceDisplay, Catalog = c, Installed = inst,
                });
            }
            foreach (var inst in installed.Values.Where(i => items.All(x => x.Prefix != i.Prefix)))
                items.Add(new Item
                {
                    Prefix = inst.Prefix, Name = string.IsNullOrEmpty(inst.Name) ? inst.Prefix : inst.Name,
                    Version = inst.Version, Tagline = inst.Description, Installed = inst,
                });

            var bar = new WrapPanel { Margin = new Thickness(0, 0, 0, 6) };
            if (cat.FromCache || cat.Failed)
            {
                bar.Children.Add(Note(cat.Failed
                    ? "Saytga ulanib bo'lmadi. Internetni tekshiring va «Yangilash»ni bosing."
                    : "Internet yo'q — oxirgi saqlangan ro'yxat ko'rsatilmoqda.", Ui.AmberFg, Ui.AmberBg));
            }
            var refresh = Ui.Pill("Yangilash", Ui.PillKind.Secondary, Reload, small: true);
            refresh.Margin = new Thickness(cat.FromCache || cat.Failed ? 10 : 0, 0, 0, 0);
            refresh.VerticalAlignment = VerticalAlignment.Center;
            bar.Children.Add(refresh);
            _list.Children.Add(bar);

            if (items.Count == 0)
            {
                _list.Children.Add(Empty());
                return;
            }
            var wrap = new WrapPanel { Margin = new Thickness(-10, 8, -10, 0) };
            foreach (var it in items.OrderByDescending(i => i.Installed != null).ThenBy(i => i.Name))
                wrap.Children.Add(Card(it));
            _list.Children.Add(wrap);
        }

        void Reload()
        {
            _list.Children.Clear();
            _list.Children.Add(Ui.T("Yangilanmoqda…", 14, null, Ui.Muted));
            Catalog.LoadAsync().ContinueWith(t => _w.Dispatcher.Invoke(() => Fill(t.Result)));
        }

        UIElement Empty()
        {
            var open = Ui.Pill("Saytni ochish", Ui.PillKind.Primary, () => MainWindow.OpenUrl(AppInfo.SiteUrl));
            open.HorizontalAlignment = HorizontalAlignment.Left;
            return new Border
            {
                CornerRadius = new CornerRadius(28),
                Background = Ui.Pastel(),
                Padding = new Thickness(36),
                Child = Ui.V(14,
                    Ui.T("Plaginlar ro'yxati bo'sh", 22, FontWeights.SemiBold, Ui.Ink, true, Ui.Display),
                    Ui.T("Internetga ulaning va «Yangilash»ni bosing yoki plaginlarni saytda ko'ring.", 14, null, Ui.Ink, true),
                    open),
            };
        }

        UIElement Card(Item it)
        {
            Border status;
            if (it.IsActive) status = Ui.Chip("● Faol", Ui.GreenFg, Ui.GreenBg);
            else if (it.Installed != null && it.Installed.FilesPresent) status = Ui.Chip("● Faollashtirilmagan", Ui.AmberFg, Ui.AmberBg);
            else status = Ui.Chip("O'rnatilmagan", Ui.Muted, Ui.Surface);

            var head = new DockPanel();
            var badge = Ui.Badge(it.Prefix, 46);
            DockPanel.SetDock(badge, Dock.Left);
            head.Children.Add(badge);
            DockPanel.SetDock(status, Dock.Right);
            head.Children.Add(status);
            string sub = string.Join(" · ", new[] { it.Price, string.IsNullOrEmpty(it.Version) ? null : "v" + it.Version }
                                            .Where(x => !string.IsNullOrEmpty(x)));
            var titles = Ui.V(2, Ui.T(it.Name, 18, FontWeights.SemiBold, Ui.Ink, false, Ui.Display),
                                 Ui.T(string.IsNullOrEmpty(sub) ? it.Prefix : sub, 12, null, Ui.Muted));
            titles.Margin = new Thickness(14, 0, 10, 0);
            titles.VerticalAlignment = VerticalAlignment.Center;
            head.Children.Add(titles);

            var body = Ui.V(16, head);
            if (!string.IsNullOrWhiteSpace(it.Tagline))
                body.Children.Add(Spaced(Ui.T(it.Tagline, 13, null, Ui.Muted, true), 14));
            if (it.Installed != null && it.Installed.Files.Length > 0 && !it.Installed.FilesPresent)
                body.Children.Add(Spaced(Note("Plagin fayli topilmadi. Uni qayta o'rnating.", Ui.RedFg, Ui.RedBg), 14));
            body.Children.Add(Spaced(Ui.Divider(), 16));
            body.Children.Add(Spaced(it.IsActive ? ActiveBlock(it) : InactiveBlock(it), 12));

            var footer = new WrapPanel { Margin = new Thickness(-6, 14, 0, 0) };
            footer.Children.Add(Ui.Pill(it.Installed?.FilesPresent == true ? "Qayta o'rnatish" : "Plaginni o'rnatish",
                                        Ui.PillKind.Ghost, () => InstallFromFile(it), small: true));
            if (it.IsActive)
                footer.Children.Add(Ui.Pill("Dezaktiv qilish", Ui.PillKind.Ghost, () => AskDeactivate(it), small: true));
            if (it.Installed != null)
                footer.Children.Add(Ui.Pill("O'chirish", Ui.PillKind.Ghost, () => AskRemove(it), small: true));
            body.Children.Add(footer);

            var card = Ui.Card(body, 24);
            card.Width = 420;
            card.Margin = new Thickness(10);
            card.VerticalAlignment = VerticalAlignment.Top;
            return card;
        }

        static FrameworkElement Spaced(FrameworkElement e, double top)
        {
            e.Margin = new Thickness(e.Margin.Left, top, e.Margin.Right, e.Margin.Bottom);
            return e;
        }

        static Border Note(string text, System.Windows.Media.Brush fg, System.Windows.Media.Brush bg) => new Border
        {
            CornerRadius = new CornerRadius(14),
            Background = bg,
            Padding = new Thickness(12, 10, 12, 10),
            Child = Ui.T(text, 13, FontWeights.Medium, fg, true),
        };

        UIElement CopyRow(string label, string value, string copied)
        {
            var row = new DockPanel();
            var btn = Ui.Pill("Nusxalash", Ui.PillKind.Secondary, () => _w.Copy(value, copied), small: true);
            DockPanel.SetDock(btn, Dock.Right);
            row.Children.Add(btn);
            row.Children.Add(Ui.V(2, Ui.Label(label), Ui.T(value, 17, FontWeights.SemiBold, Ui.Ink, false, Ui.Mono)));
            return row;
        }

        FrameworkElement ActiveBlock(Item it)
        {
            return Ui.V(12,
                CopyRow("Faollashtirish kodi", Licensing.NormalizeCode(it.Installed.Code, it.Prefix), "Kod nusxalandi"),
                Ui.T("Plagin shu kompyuterda faol." +
                     (string.IsNullOrEmpty(it.Installed.ActivatedAt) ? "" : $"\nFaollashtirilgan: {it.Installed.ActivatedAt}"),
                     13, null, Ui.Muted, true));
        }

        FrameworkElement InactiveBlock(Item it)
        {
            var input = Ui.Input(it.Prefix + "-XXXX-XXXX-XXXX", out TextBox box, mono: true);
            var btn = Ui.Pill("Faollashtirish", Ui.PillKind.Primary, () => Activate(it, box.Text));
            box.KeyDown += (s, e) => { if (e.Key == Key.Enter) Activate(it, box.Text); };
            var codeRow = new DockPanel();
            DockPanel.SetDock(btn, Dock.Right);
            btn.Margin = new Thickness(10, 0, 0, 0);
            codeRow.Children.Add(btn);
            codeRow.Children.Add(input);

            var buy = Ui.Pill("Saytda sotib olish", Ui.PillKind.Primary,
                              () => MainWindow.OpenUrl(Catalog.BuyUrl(it.Catalog, it.RequestId)));
            buy.HorizontalAlignment = HorizontalAlignment.Left;

            var block = Ui.V(14,
                CopyRow("So'rov kodi", it.RequestId, "So'rov kodi nusxalandi — endi saytga kiriting"),
                Ui.T("1) «Saytda sotib olish» — kod saytda o'zi to'ldiriladi.\n" +
                     "2) To'lovdan keyin kabinetdan plaginni yuklab oling va «Plaginni o'rnatish»ni bosing.\n" +
                     "3) Saytdagi faollashtirish kodini pastga kiriting.", 13, null, Ui.Muted, true),
                buy,
                codeRow);
            if (!string.IsNullOrEmpty(it.Installed?.DeactConfirm))
                block.Children.Add(Spaced(Note($"Oxirgi dezaktivatsiya tasdiq kodi: {it.Installed.DeactConfirm}\n" +
                                               "Uni saytdagi «Kompyuterni almashtirish» sahifasiga kiriting.",
                                               Ui.AmberFg, Ui.AmberBg), 14));
            return block;
        }

        void InstallFromFile(Item it)
        {
            var dlg = new OpenFileDialog
            {
                Title = $"{it.Name} — saytdan yuklangan ZIP faylni tanlang",
                Filter = "Plagin paketi (*.zip)|*.zip|Barcha fayllar (*.*)|*.*",
                InitialDirectory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads"),
            };
            if (dlg.ShowDialog(_w) != true) return;
            try
            {
                var pkg = PackageInstaller.Read(dlg.FileName);
                if (pkg.Prefix != it.Prefix)
                {
                    _w.Toast($"Bu fayl boshqa plagin ({pkg.Name}) uchun. Shunga qaramay o'rnatish oynasi ochildi.", true);
                }
                _w.ShowInstall(pkg);
            }
            catch (Exception ex)
            {
                _w.Toast(PackageInstaller.Explain(ex), true);
            }
        }

        void Activate(Item it, string text)
        {
            string code = Licensing.NormalizeCode(text, it.Prefix);
            if (code == null)
            {
                string clean = Licensing.Clean(text);
                _w.Toast(clean.Length == 0 ? "Saytdagi faollashtirish kodini kiriting."
                        : clean == Licensing.Clean(it.RequestId) ? "Bu so'rov kodi. Uni saytga kiriting — faollashtirish kodini sayt beradi."
                        : !clean.StartsWith(it.Prefix) ? $"Bu kod boshqa plagin uchun. {it.Name} kodi {it.Prefix}- bilan boshlanadi."
                        : "Kod noto'g'ri yozilgan. Saytdagi kodni aynan nusxalab qo'ying.", true);
                return;
            }
            try
            {
                PluginStore.SetCode(it.Prefix, code, it.Name);
            }
            catch (Exception ex)
            {
                _w.Toast("Kodni saqlab bo'lmadi: " + ex.Message, true);
                return;
            }
            _w.Refresh();
            bool installed = it.Installed?.FilesPresent == true;
            _w.Dialog($"{it.Name} faollashtirildi",
                Ui.T((installed ? "CorelDRAW ochiq bo'lsa, yopib qayta oching — plagin ishlaydi.\n\n"
                                : "Endi plaginni o'rnating: saytdagi kabinetdan ZIP'ni yuklab oling va «Plaginni o'rnatish»ni bosing.\n\n") +
                     "Agar plagin «kod bu kompyuter uchun emas» desa, saytga aynan shu kompyuterning so'rov kodi kiritilganini tekshiring.",
                     14, null, Ui.Muted, true),
                ("Yaxshi", Ui.PillKind.Primary, null));
        }

        void AskDeactivate(Item it)
        {
            _w.Dialog("Dezaktiv qilasizmi?",
                Ui.T($"{it.Name} shu kompyuterda ishlamay qoladi. Dastur tasdiq kodini beradi — uni saytdagi " +
                     "«Kompyuterni almashtirish» sahifasiga kiritasiz va litsenziyani yangi kompyuterda yoqasiz.\n\n" +
                     "Eslatma: almashtirish kuniga 1 marta, jami 3 marta mumkin.", 14, null, Ui.Muted, true),
                ("Bekor qilish", Ui.PillKind.Secondary, null),
                ("Dezaktiv qilish", Ui.PillKind.Primary, () => Deactivate(it)));
        }

        void Deactivate(Item it)
        {
            string confirm = Licensing.DeactConfirm(Licensing.NormalizeCode(it.Installed.Code, it.Prefix), Hardware.MachineId);
            try
            {
                PluginStore.Deactivate(it.Prefix, confirm);
            }
            catch (Exception ex)
            {
                _w.Toast("Dezaktiv qilib bo'lmadi: " + ex.Message, true);
                return;
            }
            _w.Refresh();
            var code = Ui.T(confirm, 30, FontWeights.Bold, Ui.Ink, false, Ui.Mono);
            code.HorizontalAlignment = HorizontalAlignment.Center;
            _w.Dialog("Tasdiq kodi",
                Ui.V(14,
                    Ui.T("Bu kodni saytdagi kabinetda «Kompyuterni almashtirish» sahifasiga kiriting:", 14, null, Ui.Muted, true),
                    new Border { CornerRadius = new CornerRadius(18), Background = Ui.Pastel(0.6), Padding = new Thickness(18), Child = code },
                    Ui.T("Kod plagin kartochkasida ham ko'rinib turadi.", 12, null, Ui.Muted, true)),
                ("Nusxalash", Ui.PillKind.Secondary, () => _w.Copy(confirm, "Tasdiq kodi nusxalandi")),
                ("Saytni ochish", Ui.PillKind.Secondary, () => MainWindow.OpenUrl(AppInfo.SiteUrl + "/kabinet/")),
                ("Yopish", Ui.PillKind.Primary, null));
        }

        void AskRemove(Item it)
        {
            string extra = it.IsActive
                ? "\n\nPlagin faol. Litsenziyani boshqa kompyuterga o'tkazmoqchi bo'lsangiz, avval «Dezaktiv qilish»ni bosing."
                : "";
            _w.Dialog("Plaginni o'chirasizmi?",
                Ui.T($"{it.Name} fayllari CorelDRAW papkasidan o'chiriladi.{extra}", 14, null, Ui.Muted, true),
                ("Bekor qilish", Ui.PillKind.Secondary, null),
                ("O'chirish", Ui.PillKind.Danger, () => Remove(it)));
        }

        void Remove(Item it)
        {
            int failed = 0;
            foreach (var f in it.Installed.Files.Where(File.Exists))
                try { File.Delete(f); } catch { failed++; }
            if (failed > 0)
            {
                _w.Toast("Ba'zi fayllarni o'chirib bo'lmadi: CorelDRAW'ni yoping yoki administrator sifatida oching.", true);
                return;
            }
            PluginStore.Remove(it.Prefix);
            _w.Refresh();
            _w.Toast($"{it.Name} o'chirildi");
        }
    }
}
