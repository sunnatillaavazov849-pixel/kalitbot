using System;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Sunat.Core;
using Sunat.Plaginlar.Services;

namespace Sunat.Plaginlar.Pages
{
    /// <summary>Plaginlarim: o'rnatilgan plaginlar, so'rov ID, kod kiritish, dezaktivatsiya.</summary>
    class PluginsPage
    {
        readonly MainWindow _w;
        public PluginsPage(MainWindow w) { _w = w; }

        public UIElement Build()
        {
            var plugins = PluginStore.All();
            var page = Ui.V(28,
                Ui.V(8, Ui.H1("Plaginlarim"),
                     Ui.Sub("Har bir plagin uchun so'rov ID'ni botga yuboring, kelgan kodni shu yerga kiriting.")));

            if (plugins.Count == 0)
            {
                page.Children.Add(Empty());
                return page;
            }

            var wrap = new WrapPanel { Margin = new Thickness(-10, 18, -10, 0) };
            foreach (var p in plugins) wrap.Children.Add(PluginCard(p));
            page.Children.Add(wrap);
            return page;
        }

        UIElement Empty()
        {
            var banner = new Border
            {
                CornerRadius = new CornerRadius(28),
                Background = Ui.Pastel(),
                Padding = new Thickness(36),
                Child = Ui.V(14,
                    Ui.T("Hali plagin o'rnatilmagan", 22, FontWeights.SemiBold, Ui.Ink, true, Ui.Display),
                    Ui.T("Botdan plagin ZIP faylini yuklab oling va shu yerga qo'shing.", 14, null, Ui.Ink, true),
                    Ui.Pill("Plagin qo'shish", Ui.PillKind.Primary, () => _w.Navigate("add"))),
            };
            ((FrameworkElement)((StackPanel)banner.Child).Children[2]).HorizontalAlignment = HorizontalAlignment.Left;
            return banner;
        }

        UIElement PluginCard(InstalledPlugin p)
        {
            bool active = p.IsActive;
            var status = active ? Ui.Chip("● Faol", Ui.GreenFg, Ui.GreenBg)
                                : Ui.Chip("● Faollashtirilmagan", Ui.AmberFg, Ui.AmberBg);

            var head = new DockPanel();
            var badge = Ui.Badge(p.Prefix, 46);
            DockPanel.SetDock(badge, Dock.Left);
            head.Children.Add(badge);
            DockPanel.SetDock(status, Dock.Right);
            head.Children.Add(status);
            var titles = Ui.V(2,
                Ui.T(p.Name, 18, FontWeights.SemiBold, Ui.Ink, false, Ui.Display),
                Ui.T(string.IsNullOrEmpty(p.Version) ? p.Prefix : $"{p.Prefix} · versiya {p.Version}", 12, null, Ui.Muted));
            titles.Margin = new Thickness(14, 0, 10, 0);
            titles.VerticalAlignment = VerticalAlignment.Center;
            head.Children.Add(titles);

            var body = Ui.V(16, head);
            if (!string.IsNullOrWhiteSpace(p.Description))
                body.Children.Add(Spaced(Ui.T(p.Description, 13, null, Ui.Muted, true), 16));
            if (!p.FilesPresent)
                body.Children.Add(Spaced(Note("Plagin fayli topilmadi. Uni qayta o'rnating: Plagin qo'shish.", Ui.RedFg, Ui.RedBg), 16));

            body.Children.Add(Spaced(Ui.Divider(), 16));

            if (active)
                body.Children.Add(Spaced(ActiveBlock(p), 12));
            else
                body.Children.Add(Spaced(InactiveBlock(p), 12));

            var footer = new WrapPanel { Margin = new Thickness(-6, 14, 0, 0) };
            if (active)
                footer.Children.Add(Ui.Pill("Dezaktiv qilish", Ui.PillKind.Ghost, () => AskDeactivate(p), small: true));
            footer.Children.Add(Ui.Pill("Plaginni o'chirish", Ui.PillKind.Ghost, () => AskRemove(p), small: true));
            body.Children.Add(footer);

            var card = Ui.Card(body, 24);
            card.Width = 400;
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
            var txt = Ui.V(2, Ui.Label(label), Ui.T(value, 17, FontWeights.SemiBold, Ui.Ink, false, Ui.Mono));
            row.Children.Add(txt);
            return row;
        }

        FrameworkElement ActiveBlock(InstalledPlugin p)
        {
            return Ui.V(12,
                CopyRow("Faollashtirish kodi", Licensing.NormalizeCode(p.Code, p.Prefix), "Kod nusxalandi"),
                Ui.T("Plagin shu kompyuterda faol. CorelDRAW'ni qayta oching." +
                     (string.IsNullOrEmpty(p.ActivatedAt) ? "" : $"\nFaollashtirilgan: {p.ActivatedAt}"), 13, null, Ui.Muted, true));
        }

        FrameworkElement InactiveBlock(InstalledPlugin p)
        {
            var input = Ui.Input(p.Prefix + "-XXXX-XXXX-XXXX", out TextBox box, mono: true);
            var btn = Ui.Pill("Faollashtirish", Ui.PillKind.Primary, () => Activate(p, box.Text));
            box.KeyDown += (s, e) => { if (e.Key == Key.Enter) Activate(p, box.Text); };

            var codeRow = new DockPanel();
            DockPanel.SetDock(btn, Dock.Right);
            btn.Margin = new Thickness(10, 0, 0, 0);
            codeRow.Children.Add(btn);
            codeRow.Children.Add(input);

            var steps = Ui.T("1) So'rov ID'ni nusxalab, botga yuboring.\n2) To'lovdan keyin bot bergan kodni pastga kiriting.",
                             13, null, Ui.Muted, true);

            var block = Ui.V(14, CopyRow("So'rov ID", p.RequestId, "So'rov ID nusxalandi — endi botga yuboring"), steps, codeRow);
            if (!string.IsNullOrEmpty(p.DeactConfirm))
                block.Children.Add(Spaced(Note($"Oxirgi dezaktivatsiya tasdiq kodi: {p.DeactConfirm}\nUni botdagi «🔄 Boshqa PC'ga ko'chirish» bo'limiga yuboring.",
                                               Ui.AmberFg, Ui.AmberBg), 14));
            return block;
        }

        void Activate(InstalledPlugin p, string text)
        {
            string code = Licensing.NormalizeCode(text, p.Prefix);
            if (code == null)
            {
                string clean = Licensing.Clean(text);
                _w.Toast(clean.Length == 0 ? "Botdan kelgan kodni kiriting."
                        : !clean.StartsWith(p.Prefix) ? $"Bu kod boshqa plagin uchun. {p.Name} kodi {p.Prefix}- bilan boshlanadi."
                        : "Kod noto'g'ri yozilgan. Botdagi kodni aynan nusxalab qo'ying.", true);
                return;
            }
            try
            {
                PluginStore.SetCode(p.Prefix, code);
            }
            catch (Exception ex)
            {
                _w.Toast("Kodni saqlab bo'lmadi: " + ex.Message, true);
                return;
            }
            _w.Refresh();
            _w.Dialog($"{p.Name} faollashtirildi",
                Ui.T("CorelDRAW ochiq bo'lsa, yopib qayta oching — plagin ishlaydi.\n\n" +
                     "Agar plagin «kod bu kompyuter uchun emas» desa, botga shu kompyuterning so'rov ID'sini yuborganingizni tekshiring.",
                     14, null, Ui.Muted, true),
                ("Yaxshi", Ui.PillKind.Primary, null));
        }

        void AskDeactivate(InstalledPlugin p)
        {
            _w.Dialog("Dezaktiv qilasizmi?",
                Ui.T($"{p.Name} shu kompyuterda ishlamay qoladi. Dastur sizga tasdiq kodini beradi — uni botdagi " +
                     "«🔄 Boshqa PC'ga ko'chirish» bo'limiga yuborasiz va litsenziyani yangi kompyuterda yoqasiz.\n\n" +
                     "Eslatma: ko'chirish kuniga 1 marta, jami 3 marta mumkin.", 14, null, Ui.Muted, true),
                ("Bekor qilish", Ui.PillKind.Secondary, null),
                ("Dezaktiv qilish", Ui.PillKind.Primary, () => Deactivate(p)));
        }

        void Deactivate(InstalledPlugin p)
        {
            string confirm = Licensing.DeactConfirm(Licensing.NormalizeCode(p.Code, p.Prefix), Hardware.MachineId);
            try
            {
                PluginStore.Deactivate(p.Prefix, confirm);
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
                    Ui.T("Bu kodni botdagi «🔄 Boshqa PC'ga ko'chirish» bo'limiga yuboring:", 14, null, Ui.Muted, true),
                    new Border { CornerRadius = new CornerRadius(18), Background = Ui.Pastel(0.6), Padding = new Thickness(18), Child = code },
                    Ui.T("Kod plagin kartochkasida ham ko'rinib turadi.", 12, null, Ui.Muted, true)),
                ("Nusxalash", Ui.PillKind.Secondary, () => _w.Copy(confirm, "Tasdiq kodi nusxalandi")),
                ("Yopish", Ui.PillKind.Primary, null));
        }

        void AskRemove(InstalledPlugin p)
        {
            string extra = p.IsActive
                ? "\n\nPlagin faol. Litsenziyani boshqa kompyuterga o'tkazmoqchi bo'lsangiz, avval «Dezaktiv qilish»ni bosing."
                : "";
            _w.Dialog("Plaginni o'chirasizmi?",
                Ui.T($"{p.Name} fayllari CorelDRAW papkasidan o'chiriladi.{extra}", 14, null, Ui.Muted, true),
                ("Bekor qilish", Ui.PillKind.Secondary, null),
                ("O'chirish", Ui.PillKind.Danger, () => Remove(p)));
        }

        void Remove(InstalledPlugin p)
        {
            int failed = 0;
            foreach (var f in p.Files.Where(File.Exists))
                try { File.Delete(f); } catch { failed++; }
            if (failed > 0)
            {
                _w.Toast("Ba'zi fayllarni o'chirib bo'lmadi: CorelDRAW'ni yoping yoki administrator sifatida oching.", true);
                return;
            }
            PluginStore.Remove(p.Prefix);
            _w.Refresh();
            _w.Toast($"{p.Name} o'chirildi");
        }
    }
}
