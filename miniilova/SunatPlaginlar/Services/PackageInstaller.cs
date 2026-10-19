using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Text;
using System.Text.RegularExpressions;

namespace Sunat.Plaginlar.Services
{
#pragma warning disable CS0649 // maydonlarni DataContractJsonSerializer to'ldiradi
    [DataContract]
    class Manifest
    {
        [DataMember(Name = "prefix")] public string Prefix;
        [DataMember(Name = "name")] public string Name;
        [DataMember(Name = "version")] public string Version;
        [DataMember(Name = "description")] public string Description;
        [DataMember(Name = "bot")] public string Bot;
        [DataMember(Name = "files")] public string[] Files;
    }
#pragma warning restore CS0649

    /// <summary>Botdan olingan plagin paketi: ZIP (ichida manifest.json + .gms) yoki ochilgan papkadagi manifest.json.</summary>
    class PackageInfo
    {
        public string Prefix, Name, Version, Description, Bot;
        public string[] Files;
        public string SourcePath;     // ZIP yoki manifest.json
        public string BaseInZip;      // ZIP ichida manifest turgan papka ("" yoki "plagin/")
        public bool IsZip;
    }

    class PackageException : Exception
    {
        public PackageException(string message) : base(message) { }
    }

    static class PackageInstaller
    {
        static readonly Regex PrefixRe = new Regex("^[A-Z]{2,4}$");

        static Manifest Parse(Stream s)
        {
            try
            {
                using (var ms = new MemoryStream())
                {
                    s.CopyTo(ms);
                    var bytes = ms.ToArray();
                    // UTF-8 BOM bo'lsa olib tashlanadi
                    int skip = bytes.Length >= 3 && bytes[0] == 0xEF && bytes[1] == 0xBB && bytes[2] == 0xBF ? 3 : 0;
                    using (var clean = new MemoryStream(bytes, skip, bytes.Length - skip))
                        return (Manifest)new DataContractJsonSerializer(typeof(Manifest)).ReadObject(clean);
                }
            }
            catch (Exception)
            {
                throw new PackageException("manifest.json o'qib bo'lmadi. Paket buzilgan bo'lishi mumkin — botdan qayta yuklab oling.");
            }
        }

        static PackageInfo FromManifest(Manifest m, string source, string baseInZip, bool isZip)
        {
            string prefix = (m?.Prefix ?? "").Trim().ToUpperInvariant();
            if (!PrefixRe.IsMatch(prefix) || m.Files == null || m.Files.Length == 0)
                throw new PackageException("Bu Sunat.cc plagin paketi emas (manifest.json noto'g'ri).");
            return new PackageInfo
            {
                Prefix = prefix,
                Name = string.IsNullOrWhiteSpace(m.Name) ? prefix : m.Name.Trim(),
                Version = m.Version?.Trim() ?? "",
                Description = m.Description?.Trim() ?? "",
                Bot = m.Bot?.Trim() ?? "",
                Files = m.Files.Select(f => f.Replace('\\', '/').Trim()).ToArray(),
                SourcePath = source,
                BaseInZip = baseInZip,
                IsZip = isZip,
            };
        }

        public static PackageInfo Read(string path)
        {
            if (!File.Exists(path)) throw new PackageException("Fayl topilmadi: " + path);
            if (Path.GetFileName(path).Equals("manifest.json", StringComparison.OrdinalIgnoreCase))
            {
                using (var fs = File.OpenRead(path))
                {
                    var info = FromManifest(Parse(fs), path, "", false);
                    string dir = Path.GetDirectoryName(path);
                    foreach (var f in info.Files)
                        if (!File.Exists(Path.Combine(dir, f)))
                            throw new PackageException($"Paketda {f} fayli yo'q.");
                    return info;
                }
            }
            if (!path.EndsWith(".zip", StringComparison.OrdinalIgnoreCase))
                throw new PackageException("Botdan olingan .zip faylni tanlang.");
            try
            {
                using (var zip = ZipFile.OpenRead(path))
                {
                    var entry = zip.Entries
                        .Where(e => e.Name.Equals("manifest.json", StringComparison.OrdinalIgnoreCase))
                        .OrderBy(e => e.FullName.Length).FirstOrDefault();
                    if (entry == null) throw new PackageException("Bu ZIP ichida plagin yo'q (manifest.json topilmadi).");
                    string baseDir = entry.FullName.Substring(0, entry.FullName.Length - entry.Name.Length);
                    PackageInfo info;
                    using (var s = entry.Open()) info = FromManifest(Parse(s), path, baseDir, true);
                    foreach (var f in info.Files)
                        if (FindEntry(zip, baseDir + f) == null)
                            throw new PackageException($"Paketda {f} fayli yo'q.");
                    return info;
                }
            }
            catch (InvalidDataException)
            {
                throw new PackageException("ZIP fayl buzilgan. Botdan qayta yuklab oling.");
            }
        }

        static ZipArchiveEntry FindEntry(ZipArchive zip, string fullName) =>
            zip.Entries.FirstOrDefault(e => e.FullName.Replace('\\', '/').Equals(fullName, StringComparison.OrdinalIgnoreCase));

        /// <summary>Exe yonidagi (ZIP ochilgan papkadagi) paketlarni topadi.</summary>
        public static List<PackageInfo> FindNearby(string dir)
        {
            var found = new List<PackageInfo>();
            try
            {
                var candidates = Directory.EnumerateFiles(dir, "manifest.json", SearchOption.TopDirectoryOnly)
                    .Concat(Directory.EnumerateDirectories(dir).SelectMany(d => Directory.EnumerateFiles(d, "manifest.json")))
                    .Concat(Directory.EnumerateFiles(dir, "*.zip"));
                foreach (var c in candidates.Take(20))
                    try { found.Add(Read(c)); } catch { }
            }
            catch { }
            return found.GroupBy(p => p.Prefix).Select(g => g.First()).ToList();
        }

        /// <summary>Paket fayllarini har bir GMS papkaga nusxalaydi. O'rnatilgan fayllar ro'yxatini qaytaradi.</summary>
        public static List<string> Install(PackageInfo pkg, IEnumerable<string> gmsDirs)
        {
            var installed = new List<string>();
            ZipArchive zip = pkg.IsZip ? ZipFile.OpenRead(pkg.SourcePath) : null;
            try
            {
                foreach (string dir in gmsDirs)
                {
                    Directory.CreateDirectory(dir);
                    foreach (string f in pkg.Files)
                    {
                        string target = Path.Combine(dir, Path.GetFileName(f));
                        if (zip != null) FindEntry(zip, pkg.BaseInZip + f).ExtractToFile(target, true);
                        else File.Copy(Path.Combine(Path.GetDirectoryName(pkg.SourcePath), f), target, true);
                        installed.Add(target);
                    }
                }
            }
            finally
            {
                zip?.Dispose();
            }
            return installed;
        }

        public static string Explain(Exception ex)
        {
            if (ex is PackageException) return ex.Message;
            if (ex is UnauthorizedAccessException)
                return "Bu papkaga yozishga ruxsat yo'q. Dasturni administrator sifatida qayta oching yoki foydalanuvchi papkasini tanlang.";
            if (ex is IOException)
                return "Fayl band: CorelDRAW ochiq bo'lishi mumkin. CorelDRAW'ni yopib, qayta urinib ko'ring.\n(" + ex.Message + ")";
            return ex.Message;
        }
    }
}
