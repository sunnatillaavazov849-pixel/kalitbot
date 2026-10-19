using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace Sunat.Plaginlar.Services
{
    class CorelInstall
    {
        public string Root;          // C:\Program Files\Corel\CorelDRAW Graphics Suite 2020
        public int Major;            // 22, 23, ...
        public string Year;          // "2020"
        public string ProgramGms;    // Root\Draw\GMS (administrator huquqi kerak)
        public string UserGms;       // %APPDATA%\Corel\<...>\Draw\GMS (huquq kerak emas)
        public bool UserProfileExists;  // CorelDRAW shu foydalanuvchida kamida bir marta ochilgan

        public bool Manual;          // foydalanuvchi qo'lda qo'shgan GMS papka

        public string Title => Manual ? "Qo'lda qo'shilgan papka" : "CorelDRAW " + (string.IsNullOrEmpty(Year) ? "" : Year + " ") + (Major > 0 ? $"(v{Major})" : "");
        /// <summary>Standart o'rnatish joyi: foydalanuvchi papkasi (bor bo'lsa), aks holda dastur papkasi.</summary>
        public string DefaultGms => UserProfileExists ? UserGms : ProgramGms;
    }

    /// <summary>
    /// O'rnatilgan CorelDRAW versiyalarini topadi (2020 = v22 ... 2026).
    /// Yo'llar qattiq yozilmagan: reyestr va Program Files\Corel ichidan qidiriladi.
    /// </summary>
    static class CorelLocator
    {
        // Corel ichki versiya raqami -> yil (2022 va 2023 ikkalasi ham 24.x)
        static readonly Dictionary<int, string> Years = new Dictionary<int, string>
        {
            { 22, "2020" }, { 23, "2021" }, { 24, "2022/2023" }, { 25, "2024" }, { 26, "2025" }, { 27, "2026" }, { 28, "2027" },
        };

        static readonly Regex YearInName = new Regex(@"\b(20[2-3]\d)\b");

        public static List<CorelInstall> Locate()
        {
            var roots = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var r in FromRegistry()) roots.Add(r);
            foreach (var r in FromProgramFiles()) roots.Add(r);

            var list = new List<CorelInstall>();
            foreach (var root in roots)
            {
                var ci = Describe(root);
                if (ci.Major == 0 || ci.Major >= 22) list.Add(ci);   // 2020 va undan yangilari
            }
            list = list.OrderByDescending(c => c.Major).ThenBy(c => c.Root).ToList();
            foreach (var dir in ManualDirs())
                list.Add(new CorelInstall { Root = dir, ProgramGms = dir, UserGms = dir, UserProfileExists = true, Manual = true });
            return list;
        }

        // ---------------------------------------------------------- qo'lda qo'shilgan GMS papkalar
        const string SettingsKey = @"Software\SunatCC\PlaginlarSozlama";

        public static List<string> ManualDirs()
        {
            try
            {
                using (var k = Registry.CurrentUser.OpenSubKey(SettingsKey))
                    return ((k?.GetValue("ManualGms") as string[]) ?? new string[0]).Where(d => !string.IsNullOrWhiteSpace(d)).ToList();
            }
            catch { return new List<string>(); }
        }

        public static void SetManualDirs(IEnumerable<string> dirs)
        {
            using (var k = Registry.CurrentUser.CreateSubKey(SettingsKey))
                k.SetValue("ManualGms", dirs.Distinct(StringComparer.OrdinalIgnoreCase).ToArray(), RegistryValueKind.MultiString);
        }

        static string Exe(string root)
        {
            foreach (var sub in new[] { "Programs64", "Programs" })
            {
                string p = Path.Combine(root, sub, "CorelDRW.exe");
                if (File.Exists(p)) return p;
            }
            return null;
        }

        static bool IsRoot(string dir) =>
            Directory.Exists(dir) && (Exe(dir) != null || Directory.Exists(Path.Combine(dir, "Draw", "GMS")));

        static IEnumerable<string> FromProgramFiles()
        {
            var bases = new[]
            {
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),
                Environment.GetEnvironmentVariable("ProgramW6432"),
            }.Where(b => !string.IsNullOrEmpty(b)).Distinct(StringComparer.OrdinalIgnoreCase);

            foreach (var b in bases)
            {
                string corel = Path.Combine(b, "Corel");
                if (!Directory.Exists(corel)) continue;
                IEnumerable<string> level1;
                try { level1 = Directory.GetDirectories(corel); } catch { continue; }
                foreach (var d1 in level1)
                {
                    if (IsRoot(d1)) { yield return d1; continue; }
                    // yangi versiyalar: ...\CorelDRAW Graphics Suite\27
                    string[] level2;
                    try { level2 = Directory.GetDirectories(d1); } catch { continue; }
                    foreach (var d2 in level2)
                        if (IsRoot(d2)) yield return d2;
                }
            }
        }

        static IEnumerable<string> FromRegistry()
        {
            var found = new List<string>();
            foreach (var view in new[] { RegistryView.Registry64, RegistryView.Registry32 })
            {
                try
                {
                    using (var hklm = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, view))
                    using (var cdr = hklm.OpenSubKey(@"SOFTWARE\Corel\CorelDRAW"))
                    {
                        if (cdr == null) continue;
                        foreach (var ver in cdr.GetSubKeyNames().Where(n => Regex.IsMatch(n, @"^\d+\.\d+$")))
                            using (var k = cdr.OpenSubKey(ver))
                                CollectPaths(k, found, 0);
                    }
                }
                catch { }
            }
            // reyestrdagi istalgan yo'ldan yuqoriga qarab CorelDRAW ildizini qidiramiz
            foreach (var p in found.Distinct(StringComparer.OrdinalIgnoreCase))
            {
                string dir = p;
                for (int i = 0; i < 4 && !string.IsNullOrEmpty(dir); i++)
                {
                    if (IsRoot(dir)) { yield return dir.TrimEnd('\\'); break; }
                    dir = Path.GetDirectoryName(dir.TrimEnd('\\'));
                }
            }
        }

        static void CollectPaths(RegistryKey k, List<string> found, int depth)
        {
            if (k == null || depth > 2) return;
            foreach (var name in k.GetValueNames())
                if (k.GetValue(name) is string s && s.Length > 3 && s.IndexOf(":\\", StringComparison.Ordinal) == 1)
                {
                    string path = s.Trim().Trim('"');
                    if (File.Exists(path)) path = Path.GetDirectoryName(path);
                    if (Directory.Exists(path)) found.Add(path);
                }
            foreach (var sub in k.GetSubKeyNames().Take(30))
                try { using (var sk = k.OpenSubKey(sub)) CollectPaths(sk, found, depth + 1); } catch { }
        }

        static CorelInstall Describe(string root)
        {
            var ci = new CorelInstall { Root = root, ProgramGms = Path.Combine(root, "Draw", "GMS") };
            string exe = Exe(root);
            if (exe != null)
                try { ci.Major = FileVersionInfo.GetVersionInfo(exe).FileMajorPart; } catch { }

            // papka nomidan: "...Suite 2020" yoki "...Suite\27"
            var ym = YearInName.Match(root);
            string leaf = Path.GetFileName(root.TrimEnd('\\'));
            if (ci.Major == 0 && int.TryParse(leaf, out int n) && n >= 20 && n < 40) ci.Major = n;
            if (ym.Success) ci.Year = ym.Groups[1].Value;
            else if (Years.TryGetValue(ci.Major, out var y)) ci.Year = y;
            if (ci.Major == 0 && ym.Success)
            {
                var kv = Years.FirstOrDefault(p => p.Value.Contains(ym.Groups[1].Value));
                ci.Major = kv.Key;
            }

            // foydalanuvchi papkasi: %APPDATA%\Corel\<Program Files\Corel dan keyingi qism>
            string appdata = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string rel = RelativeToCorel(root);
            string profile = Path.Combine(appdata, "Corel", rel);
            ci.UserGms = Path.Combine(profile, "Draw", "GMS");
            ci.UserProfileExists = Directory.Exists(profile);
            return ci;
        }

        static string RelativeToCorel(string root)
        {
            string marker = "\\Corel\\";
            int i = root.IndexOf(marker, StringComparison.OrdinalIgnoreCase);
            return i >= 0 ? root.Substring(i + marker.Length).TrimEnd('\\') : Path.GetFileName(root.TrimEnd('\\'));
        }
    }
}
