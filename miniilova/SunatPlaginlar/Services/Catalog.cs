using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Text;
using System.Threading.Tasks;

namespace Sunat.Plaginlar.Services
{
#pragma warning disable CS0649 // maydonlarni DataContractJsonSerializer to'ldiradi
    [DataContract]
    class CatalogPlugin
    {
        [DataMember(Name = "prefix")] public string Prefix;
        [DataMember(Name = "name")] public string Name;
        [DataMember(Name = "slug")] public string Slug;
        [DataMember(Name = "tagline")] public string Tagline;
        [DataMember(Name = "version")] public string Version;
        [DataMember(Name = "price_display")] public string PriceDisplay;
        [DataMember(Name = "corel_versions")] public string CorelVersions;
        [DataMember(Name = "url")] public string Url;
        [DataMember(Name = "buy_url")] public string BuyUrl;
    }

    [DataContract]
    class CatalogData
    {
        [DataMember(Name = "site")] public string Site;
        [DataMember(Name = "plugins")] public List<CatalogPlugin> Plugins;
    }
#pragma warning restore CS0649

    class CatalogResult
    {
        public List<CatalogPlugin> Plugins = new List<CatalogPlugin>();
        public bool FromCache;      // internet yo'q - oxirgi saqlangan ro'yxat
        public bool Failed;         // na internet, na saqlangan ro'yxat
    }

    /// <summary>Plaginlar ro'yxati saytdan: GET {sayt}/api/plaginlar.json. Oxirgi javob diskda saqlanadi.</summary>
    static class Catalog
    {
        static CatalogResult _last;

        static string CachePath => Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SunatCC", "plaginlar.json");

        public static CatalogResult Last => _last;

        internal static CatalogData Parse(byte[] bytes)
        {
            using (var ms = new MemoryStream(bytes))
                return (CatalogData)new DataContractJsonSerializer(typeof(CatalogData)).ReadObject(ms);
        }

        static byte[] Download()
        {
            ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12;
            var req = (HttpWebRequest)WebRequest.Create(AppInfo.SiteUrl + "/api/plaginlar.json");
            req.Timeout = 10000;
            req.UserAgent = AppInfo.Name + "/" + AppInfo.Version;
            using (var resp = req.GetResponse())
            using (var s = resp.GetResponseStream())
            using (var ms = new MemoryStream())
            {
                s.CopyTo(ms);
                return ms.ToArray();
            }
        }

        public static Task<CatalogResult> LoadAsync() => Task.Run(() =>
        {
            var result = new CatalogResult();
            try
            {
                byte[] bytes = Download();
                result.Plugins = Parse(bytes).Plugins ?? new List<CatalogPlugin>();
                try
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(CachePath));
                    File.WriteAllBytes(CachePath, bytes);
                }
                catch { }
            }
            catch
            {
                try
                {
                    result.Plugins = Parse(File.ReadAllBytes(CachePath)).Plugins ?? new List<CatalogPlugin>();
                    result.FromCache = true;
                }
                catch
                {
                    result.Failed = true;
                }
            }
            result.Plugins = result.Plugins.Where(p => !string.IsNullOrEmpty(p.Prefix)).ToList();
            _last = result;
            return result;
        });

        public static string BuyUrl(CatalogPlugin p, string requestId)
        {
            string baseUrl = string.IsNullOrEmpty(p?.BuyUrl) ? AppInfo.SiteUrl + "/" : p.BuyUrl;
            return baseUrl + (baseUrl.Contains("?") ? "&" : "?") + "kod=" + Uri.EscapeDataString(requestId);
        }
    }
}
