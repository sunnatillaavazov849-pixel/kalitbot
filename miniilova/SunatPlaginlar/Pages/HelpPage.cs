using System.Windows;
using System.Windows.Controls;
using Sunat.Plaginlar.Services;

namespace Sunat.Plaginlar.Pages
{
    /// <summary>Yordam: qisqa yo'riqnoma va aloqa.</summary>
    class HelpPage
    {
        readonly MainWindow _w;
        public HelpPage(MainWindow w) { _w = w; }

        static UIElement Step(string num, string title, string text)
        {
            var dot = new Border
            {
                Width = 34, Height = 34, CornerRadius = new CornerRadius(17), Background = Ui.Ink,
                Child = new TextBlock { Text = num, Foreground = Ui.OnInk, FontWeight = FontWeights.Bold, FontSize = 14,
                                        HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center },
                VerticalAlignment = VerticalAlignment.Top,
            };
            var txt = Ui.V(2, Ui.T(title, 15, FontWeights.SemiBold, Ui.Ink, true), Ui.T(text, 13, null, Ui.Muted, true));
            txt.Margin = new Thickness(14, 4, 0, 0);
            var row = new DockPanel();
            DockPanel.SetDock(dot, Dock.Left);
            row.Children.Add(dot);
            row.Children.Add(txt);
            return row;
        }

        public UIElement Build()
        {
            var steps = Ui.Card(Ui.V(18,
                Ui.T("Qanday ishlaydi", 20, FontWeights.SemiBold, Ui.Ink, false, Ui.Display),
                Step("1", "Plaginni yuklab oling", "Botdagi «🛒 Plaginlar» bo'limidan ZIP faylni oling."),
                Step("2", "Dasturga qo'shing", "«Plagin qo'shish» → ZIP → CorelDRAW versiyasini belgilang → O'rnatish. CorelDRAW yopiq bo'lsin."),
                Step("3", "So'rov ID'ni yuboring", "«Plaginlarim» dagi so'rov ID'ni nusxalab botga yuboring va to'lov chekini jo'nating."),
                Step("4", "Kodni kiriting", "Admin tasdiqlagach bot kod beradi. Uni plagin kartochkasiga kiriting va «Faollashtirish»ni bosing."),
                Step("5", "Boshqa kompyuterga o'tish", "Kartochkada «Dezaktiv qilish» → tasdiq kodini botdagi «🔄 Boshqa PC'ga ko'chirish»ga yuboring. Kuniga 1, jami 3 marta.")), 28);

            var bot = Ui.Pill("Telegram botni ochish", Ui.PillKind.Primary, () => MainWindow.OpenUrl(PluginStore.BotUrl()));
            bot.HorizontalAlignment = HorizontalAlignment.Center;
            var contacts = new WrapPanel { HorizontalAlignment = HorizontalAlignment.Center };
            contacts.Children.Add(Ui.Pill("Telegram " + AppInfo.Telegram, Ui.PillKind.Secondary, () => MainWindow.OpenUrl(AppInfo.TelegramUrl), small: true));
            var insta = Ui.Pill("Instagram " + AppInfo.Instagram, Ui.PillKind.Secondary, () => MainWindow.OpenUrl(AppInfo.InstagramUrl), small: true);
            insta.Margin = new Thickness(8, 0, 0, 0);
            contacts.Children.Add(insta);
            var phone = Ui.Pill(AppInfo.Phone, Ui.PillKind.Secondary, () => _w.Copy(AppInfo.Phone, "Telefon raqami nusxalandi"), small: true);
            phone.Margin = new Thickness(8, 0, 0, 0);
            contacts.Children.Add(phone);

            var title = Ui.T("Savol bormi?", 22, FontWeights.SemiBold, Ui.Ink, true, Ui.Display);
            title.HorizontalAlignment = HorizontalAlignment.Center;
            var sub = Ui.T("Admin bilan bog'laning — o'rnatishda yordam beramiz.", 14, null, Ui.Ink, true);
            sub.HorizontalAlignment = HorizontalAlignment.Center;
            var banner = new Border
            {
                CornerRadius = new CornerRadius(28),
                Background = Ui.Pastel(),
                Padding = new Thickness(32, 36, 32, 36),
                Child = Ui.V(14, Center(Ui.Badge("S", 52)), title, sub, bot, contacts),
            };

            return Ui.V(28,
                Ui.V(8, Ui.H1("Yordam"), Ui.Sub($"{AppInfo.Name} — CorelDRAW plaginlarini o'rnatish va faollashtirish dasturi.")),
                steps,
                banner,
                Ui.T($"Kompyuter ID: {Hardware.MachineId}   ·   versiya {AppInfo.Version}", 12, null, Ui.Faint));
        }

        static FrameworkElement Center(FrameworkElement e)
        {
            e.HorizontalAlignment = HorizontalAlignment.Center;
            return e;
        }
    }
}
