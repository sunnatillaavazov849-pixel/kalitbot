using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Win32;
using Sunat.Core;

namespace Sunat.Plaginlar.Services
{
    class InstalledPlugin
    {
        public string Prefix, Name, Version, Description, Bot, Code, DeactConfirm, InstalledAt, ActivatedAt;
        public string[] Files = new string[0];

        public bool IsActive => !string.IsNullOrEmpty(Code) && Licensing.NormalizeCode(Code, Prefix) != null;
        public bool FilesPresent => Files.Length > 0 && Files.Any(File.Exists);
        public string RequestId => Licensing.RequestId(Prefix, Hardware.MachineId);
    }

    /// <summary>O'rnatilgan plaginlar ro'yxati va kodlar: HKCU\Software\SunatCC\Plaginlar\PREFIKS</summary>
    static class PluginStore
    {
        static RegistryKey Root(bool write) =>
            write ? Registry.CurrentUser.CreateSubKey(AppInfo.RegistryRoot) : Registry.CurrentUser.OpenSubKey(AppInfo.RegistryRoot);

        static string S(RegistryKey k, string name) => k.GetValue(name) as string ?? "";

        public static List<InstalledPlugin> All()
        {
            var list = new List<InstalledPlugin>();
            using (var root = Root(false))
            {
                if (root == null) return list;
                foreach (string prefix in root.GetSubKeyNames().OrderBy(x => x))
                    using (var k = root.OpenSubKey(prefix))
                    {
                        if (k == null) continue;
                        list.Add(new InstalledPlugin
                        {
                            Prefix = prefix.ToUpperInvariant(),
                            Name = S(k, "Name"),
                            Version = S(k, "Version"),
                            Description = S(k, "Description"),
                            Bot = S(k, "Bot"),
                            Code = S(k, "Code"),
                            DeactConfirm = S(k, "DeactConfirm"),
                            InstalledAt = S(k, "InstalledAt"),
                            ActivatedAt = S(k, "ActivatedAt"),
                            Files = S(k, "Files").Split(new[] { '|' }, StringSplitOptions.RemoveEmptyEntries),
                        });
                    }
            }
            return list;
        }

        public static InstalledPlugin Get(string prefix) => All().FirstOrDefault(p => p.Prefix == prefix);

        static string Now() => DateTime.Now.ToString("yyyy-MM-dd HH:mm");

        public static void SaveInstalled(PackageInfo pkg, IEnumerable<string> files)
        {
            using (var root = Root(true))
            using (var k = root.CreateSubKey(pkg.Prefix))
            {
                k.SetValue("Name", pkg.Name ?? pkg.Prefix);
                k.SetValue("Version", pkg.Version ?? "");
                k.SetValue("Description", pkg.Description ?? "");
                if (!string.IsNullOrEmpty(pkg.Bot)) k.SetValue("Bot", pkg.Bot);
                k.SetValue("Files", string.Join("|", files));
                k.SetValue("InstalledAt", Now());
            }
        }

        public static void SetCode(string prefix, string code)
        {
            using (var root = Root(true))
            using (var k = root.CreateSubKey(prefix))
            {
                k.SetValue("Code", code);
                k.SetValue("ActivatedAt", Now());
                k.DeleteValue("DeactConfirm", false);
            }
        }

        /// <summary>Kodni o'chiradi va tasdiq kodini eslab qoladi (foydalanuvchi qayta ko'rishi uchun).</summary>
        public static void Deactivate(string prefix, string confirm)
        {
            using (var root = Root(true))
            using (var k = root.CreateSubKey(prefix))
            {
                k.DeleteValue("Code", false);
                k.DeleteValue("ActivatedAt", false);
                k.SetValue("DeactConfirm", confirm);
            }
        }

        public static void Remove(string prefix)
        {
            using (var root = Root(true))
                root.DeleteSubKeyTree(prefix, false);
        }

        public static string BotUrl()
        {
            string bot = All().Select(p => p.Bot).FirstOrDefault(b => !string.IsNullOrWhiteSpace(b));
            return bot ?? AppInfo.DefaultBotUrl;
        }
    }
}
