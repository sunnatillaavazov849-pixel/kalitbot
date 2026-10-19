using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Effects;

namespace Sunat.Plaginlar
{
    /// <summary>
    /// Dizayn: oq fon, yumaloq kartochkalar, qora "pill" tugmalar, pastel gradient.
    /// Barcha ranglar va shakllar shu yerda.
    /// </summary>
    static class Ui
    {
        public static readonly Brush Bg = B("#FFFFFF");
        public static readonly Brush Surface = B("#F5F5F6");
        public static readonly Brush Line = B("#E8E8EB");
        public static readonly Brush Ink = B("#0B0B0C");
        public static readonly Brush Muted = B("#6E6E76");
        public static readonly Brush Faint = B("#A1A1AA");
        public static readonly Brush OnInk = B("#FFFFFF");
        public static readonly Brush GreenFg = B("#15803D"), GreenBg = B("#DCFCE7");
        public static readonly Brush AmberFg = B("#A16207"), AmberBg = B("#FEF3C7");
        public static readonly Brush RedFg = B("#B91C1C"), RedBg = B("#FEE2E2");
        public static readonly Brush Dim = B("#660B0B0C");

        public static readonly FontFamily Font = new FontFamily("Segoe UI Variable Text, Segoe UI");
        public static readonly FontFamily Display = new FontFamily("Segoe UI Variable Display, Segoe UI");
        public static readonly FontFamily Mono = new FontFamily("Cascadia Mono, Consolas");

        public static SolidColorBrush B(string hex)
        {
            var b = (SolidColorBrush)new BrushConverter().ConvertFromString(hex);
            b.Freeze();
            return b;
        }

        static Color C(string hex) => (Color)ColorConverter.ConvertFromString(hex);

        /// <summary>Rasmdagi pastel gradient: sariq -> pushti -> binafsha -> moviy.</summary>
        public static Brush Pastel(double opacity = 1)
        {
            var g = new LinearGradientBrush { StartPoint = new Point(0, 0), EndPoint = new Point(1, 1), Opacity = opacity };
            g.GradientStops.Add(new GradientStop(C("#FDE68A"), 0.0));
            g.GradientStops.Add(new GradientStop(C("#FBCFE8"), 0.35));
            g.GradientStops.Add(new GradientStop(C("#DDD6FE"), 0.65));
            g.GradientStops.Add(new GradientStop(C("#BAE6FD"), 1.0));
            g.Freeze();
            return g;
        }

        public static TextBlock T(string text, double size = 14, FontWeight? weight = null, Brush fg = null,
                                  bool wrap = false, FontFamily font = null)
        {
            return new TextBlock
            {
                Text = text,
                FontSize = size,
                FontWeight = weight ?? FontWeights.Normal,
                Foreground = fg ?? Ink,
                FontFamily = font ?? Font,
                TextWrapping = wrap ? TextWrapping.Wrap : TextWrapping.NoWrap,
                TextTrimming = wrap ? TextTrimming.None : TextTrimming.CharacterEllipsis,
            };
        }

        public static TextBlock H1(string text) => T(text, 30, FontWeights.SemiBold, Ink, true, Display);
        public static TextBlock Sub(string text) => T(text, 14, null, Muted, true);

        /// <summary>Elementlar orasida bir xil masofa bilan vertikal ro'yxat.</summary>
        public static StackPanel V(double gap, params UIElement[] items) => Stack(Orientation.Vertical, gap, items);
        public static StackPanel H(double gap, params UIElement[] items) => Stack(Orientation.Horizontal, gap, items);

        static StackPanel Stack(Orientation o, double gap, UIElement[] items)
        {
            var sp = new StackPanel { Orientation = o };
            bool first = true;
            foreach (var it in items)
            {
                if (it == null) continue;
                if (!first && it is FrameworkElement fe)
                {
                    var m = fe.Margin;
                    fe.Margin = o == Orientation.Vertical ? new Thickness(m.Left, m.Top + gap, m.Right, m.Bottom)
                                                          : new Thickness(m.Left + gap, m.Top, m.Right, m.Bottom);
                }
                sp.Children.Add(it);
                first = false;
            }
            return sp;
        }

        /// <summary>Yumaloq oq kartochka. Soya alohida qatlamda, matn xira bo'lmasligi uchun.</summary>
        public static Grid Card(UIElement child, double padding = 24, double radius = 26, Brush background = null)
        {
            var g = new Grid();
            g.Children.Add(new Border
            {
                CornerRadius = new CornerRadius(radius),
                Background = Bg,
                Effect = new DropShadowEffect { BlurRadius = 28, ShadowDepth = 2, Direction = 270, Opacity = 0.06, Color = Colors.Black },
            });
            g.Children.Add(new Border
            {
                CornerRadius = new CornerRadius(radius),
                Background = background ?? Bg,
                BorderBrush = Line,
                BorderThickness = new Thickness(1),
                Padding = new Thickness(padding),
                Child = child,
            });
            return g;
        }

        static ControlTemplate PillTemplate(double radius)
        {
            var bd = new FrameworkElementFactory(typeof(Border));
            bd.SetValue(Border.CornerRadiusProperty, new CornerRadius(radius));
            bd.SetBinding(Border.BackgroundProperty, new Binding("Background") { RelativeSource = RelativeSource.TemplatedParent });
            bd.SetBinding(Border.BorderBrushProperty, new Binding("BorderBrush") { RelativeSource = RelativeSource.TemplatedParent });
            bd.SetBinding(Border.BorderThicknessProperty, new Binding("BorderThickness") { RelativeSource = RelativeSource.TemplatedParent });
            bd.SetBinding(Border.PaddingProperty, new Binding("Padding") { RelativeSource = RelativeSource.TemplatedParent });
            var cp = new FrameworkElementFactory(typeof(ContentPresenter));
            cp.SetBinding(ContentPresenter.HorizontalAlignmentProperty,
                new Binding("HorizontalContentAlignment") { RelativeSource = RelativeSource.TemplatedParent });
            cp.SetValue(ContentPresenter.VerticalAlignmentProperty, VerticalAlignment.Center);
            bd.AppendChild(cp);
            var t = new ControlTemplate(typeof(Button)) { VisualTree = bd };
            var hover = new Trigger { Property = UIElement.IsMouseOverProperty, Value = true };
            hover.Setters.Add(new Setter(UIElement.OpacityProperty, 0.86));
            var press = new Trigger { Property = Button.IsPressedProperty, Value = true };
            press.Setters.Add(new Setter(UIElement.OpacityProperty, 0.7));
            var off = new Trigger { Property = UIElement.IsEnabledProperty, Value = false };
            off.Setters.Add(new Setter(UIElement.OpacityProperty, 0.4));
            t.Triggers.Add(hover);
            t.Triggers.Add(press);
            t.Triggers.Add(off);
            return t;
        }

        public enum PillKind { Primary, Secondary, Ghost, Danger }

        public static Button Pill(string text, PillKind kind, Action onClick, bool small = false)
        {
            var b = new Button
            {
                Content = new TextBlock { Text = text, FontFamily = Font, FontSize = small ? 13 : 14, FontWeight = FontWeights.SemiBold },
                Template = PillTemplate(999),
                Padding = small ? new Thickness(14, 7, 14, 7) : new Thickness(22, 11, 22, 11),
                Cursor = Cursors.Hand,
                HorizontalContentAlignment = HorizontalAlignment.Center,
                BorderThickness = new Thickness(1),
            };
            switch (kind)
            {
                case PillKind.Primary: b.Background = Ink; b.BorderBrush = Ink; b.Foreground = OnInk; break;
                case PillKind.Secondary: b.Background = Bg; b.BorderBrush = Line; b.Foreground = Ink; break;
                case PillKind.Ghost: b.Background = Brushes.Transparent; b.BorderBrush = Brushes.Transparent; b.Foreground = Muted; break;
                case PillKind.Danger: b.Background = Bg; b.BorderBrush = RedBg; b.Foreground = RedFg; break;
            }
            ((TextBlock)b.Content).Foreground = b.Foreground;
            if (onClick != null) b.Click += (s, e) => onClick();
            return b;
        }

        /// <summary>Chap paneldagi bo'lim tugmasi.</summary>
        public static Button Nav(string icon, string text, Action onClick)
        {
            var row = H(12,
                new TextBlock { Text = icon, FontFamily = new FontFamily("Segoe UI Emoji, Segoe UI Symbol"), FontSize = 15, VerticalAlignment = VerticalAlignment.Center },
                new TextBlock { Text = text, FontFamily = Font, FontSize = 14, FontWeight = FontWeights.Medium, VerticalAlignment = VerticalAlignment.Center });
            var b = new Button
            {
                Content = row,
                Template = PillTemplate(14),
                Padding = new Thickness(14, 11, 14, 11),
                Cursor = Cursors.Hand,
                HorizontalContentAlignment = HorizontalAlignment.Left,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                Background = Brushes.Transparent,
                BorderBrush = Brushes.Transparent,
                BorderThickness = new Thickness(0),
            };
            b.Click += (s, e) => onClick();
            return b;
        }

        public static void SetNavSelected(Button b, bool selected)
        {
            b.Background = selected ? Ink : Brushes.Transparent;
            foreach (var child in ((StackPanel)b.Content).Children)
                if (child is TextBlock tb) tb.Foreground = selected ? OnInk : Ink;
        }

        public static Border Chip(string text, Brush fg, Brush bg)
        {
            return new Border
            {
                CornerRadius = new CornerRadius(999),
                Background = bg,
                Padding = new Thickness(10, 4, 10, 4),
                HorizontalAlignment = HorizontalAlignment.Left,
                VerticalAlignment = VerticalAlignment.Center,
                Child = T(text, 12, FontWeights.SemiBold, fg),
            };
        }

        /// <summary>Yumaloq kiritish maydoni (placeholder bilan).</summary>
        public static Border Input(string placeholder, out TextBox box, bool mono = false)
        {
            var tb = new TextBox
            {
                BorderThickness = new Thickness(0),
                Background = Brushes.Transparent,
                FontFamily = mono ? Mono : Font,
                FontSize = 15,
                Foreground = Ink,
                VerticalContentAlignment = VerticalAlignment.Center,
                CharacterCasing = mono ? CharacterCasing.Upper : CharacterCasing.Normal,
                Padding = new Thickness(0),
            };
            var hint = T(placeholder, 15, null, Faint, false, mono ? Mono : Font);
            hint.IsHitTestVisible = false;
            hint.VerticalAlignment = VerticalAlignment.Center;
            tb.TextChanged += (s, e) => hint.Visibility = tb.Text.Length == 0 ? Visibility.Visible : Visibility.Collapsed;
            var g = new Grid();
            g.Children.Add(hint);
            g.Children.Add(tb);
            var border = new Border
            {
                CornerRadius = new CornerRadius(14),
                BorderBrush = Line,
                BorderThickness = new Thickness(1),
                Background = Surface,
                Padding = new Thickness(14, 10, 14, 10),
                Child = g,
            };
            tb.GotKeyboardFocus += (s, e) => { border.BorderBrush = Ink; border.Background = Bg; };
            tb.LostKeyboardFocus += (s, e) => { border.BorderBrush = Line; border.Background = Surface; };
            box = tb;
            return border;
        }

        /// <summary>Kichik yumaloq belgi (plagin ikonkasi o'rnida): gradient fon + bosh harflar.</summary>
        public static Border Badge(string letters, double size = 44)
        {
            return new Border
            {
                Width = size,
                Height = size,
                CornerRadius = new CornerRadius(size * 0.32),
                Background = Pastel(),
                Child = new TextBlock
                {
                    Text = letters,
                    FontFamily = Display,
                    FontWeight = FontWeights.Bold,
                    FontSize = size * 0.34,
                    Foreground = Ink,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center,
                },
            };
        }

        public static Border Divider() => new Border { Height = 1, Background = Line, Margin = new Thickness(0, 4, 0, 4) };

        /// <summary>Kichik sarlavha: "KOMPYUTER ID" kabi.</summary>
        public static TextBlock Label(string text)
        {
            var t = T(text.ToUpperInvariant(), 11, FontWeights.SemiBold, Muted);
            t.Margin = new Thickness(0, 0, 0, 2);
            return t;
        }
    }
}
