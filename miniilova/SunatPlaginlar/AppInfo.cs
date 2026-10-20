using System;
using Microsoft.Win32;

namespace Sunat.Plaginlar
{
    static class AppInfo
    {
        public const string Name = "Sunat.cc Plaginlar";
        public const string Version = "2.0.0";
        // Reyestr: HKCU\Software\SunatCC\Plaginlar\<PREFIKS>. Plaginlar (SunatLicense.bas) kodni shu yerdan o'qiydi.
        public const string RegistryRoot = @"Software\SunatCC\Plaginlar";
        public const string SettingsKey = @"Software\SunatCC\PlaginlarSozlama";
        public const string DefaultSiteUrl = "https://sunat.cc";
        public const string Telegram = "@sunat_aa";
        public const string TelegramUrl = "https://t.me/sunat_aa";
        public const string Instagram = "@sunat_cc";
        public const string InstagramUrl = "https://instagram.com/sunat_cc";
        public const string Phone = "+998 33 400 00 43";

        /// <summary>Sayt manzili. Sinov yoki domen o'zgarsa: SUNAT_SITE muhit o'zgaruvchisi yoki
        /// HKCU\Software\SunatCC\PlaginlarSozlama\SiteUrl.</summary>
        public static string SiteUrl
        {
            get
            {
                string v = Environment.GetEnvironmentVariable("SUNAT_SITE");
                if (string.IsNullOrWhiteSpace(v))
                {
                    try { using (var k = Registry.CurrentUser.OpenSubKey(SettingsKey)) v = k?.GetValue("SiteUrl") as string; }
                    catch { }
                }
                return (string.IsNullOrWhiteSpace(v) ? DefaultSiteUrl : v.Trim()).TrimEnd('/');
            }
        }
    }
}
