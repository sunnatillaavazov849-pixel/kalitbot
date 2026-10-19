using System;
using System.Windows;

namespace Sunat.Plaginlar
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            var app = new Application { ShutdownMode = ShutdownMode.OnMainWindowClose };
            app.DispatcherUnhandledException += (s, e) =>
            {
                MessageBox.Show("Kutilmagan xato:\n\n" + e.Exception.Message + "\n\nAdmin bilan bog'laning: " + AppInfo.Telegram,
                                AppInfo.Name, MessageBoxButton.OK, MessageBoxImage.Error);
                e.Handled = true;
            };
            app.Run(new MainWindow());
        }
    }
}
