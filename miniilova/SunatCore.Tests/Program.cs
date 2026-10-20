using System;
using System.IO;
using System.Text.Json;
using Sunat.Core;

static class Program
{
    static int failed, passed;

    static void Eq(string what, string expected, string actual)
    {
        if (expected == actual) { passed++; return; }
        failed++;
        Console.WriteLine($"XATO {what}: kutilgan {expected}, chiqdi {actual}");
    }

    static int Main(string[] args)
    {
        string path = args.Length > 0 ? args[0] : Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "testvectors.json");
        var root = JsonDocument.Parse(File.ReadAllText(path)).RootElement;
        string secret = root.GetProperty("secret").GetString();

        foreach (var c in root.GetProperty("choose").EnumerateArray())
            Eq("ChooseHardware", c.GetProperty("hw").GetString(),
               Licensing.ChooseHardware(c.GetProperty("uuid").GetString(), c.GetProperty("board").GetString(),
                                        c.GetProperty("name").GetString(), c.GetProperty("volume").GetInt32()));
        foreach (var m in root.GetProperty("machine_ids").EnumerateArray())
            Eq("MachineId " + m.GetProperty("hw").GetString(), m.GetProperty("mid").GetString(),
               Licensing.MachineId(m.GetProperty("hw").GetString()));
        foreach (var c in root.GetProperty("codes").EnumerateArray())
        {
            string prefix = c.GetProperty("prefix").GetString(), code = c.GetProperty("code").GetString();
            Eq("ActivationCode", code, Licensing.ActivationCode(prefix, c.GetProperty("mid").GetString(), secret));
            Eq("NormalizeCode", code, Licensing.NormalizeCode(code.ToLowerInvariant().Replace("-", " "), prefix));
            Eq("NormalizeCode(xato)", null, Licensing.NormalizeCode(code.Substring(0, code.Length - 1) + (code.EndsWith("A") ? "B" : "A"), prefix));
        }
        foreach (var d in root.GetProperty("deact").EnumerateArray())
            Eq("DeactConfirm", d.GetProperty("confirm").GetString(),
               Licensing.DeactConfirm(d.GetProperty("code").GetString(), d.GetProperty("mid").GetString()));

        // 2-argument: tools/zip_yasash.py yasagan ZIP (ixtiyoriy)
        if (args.Length > 1)
        {
            var pkg = Sunat.Plaginlar.Services.PackageInstaller.Read(args[1]);
            Eq("ZIP prefiks", "TT", pkg.Prefix);
            Eq("ZIP nom", "Tez-Tez", pkg.Name);
            Eq("ZIP fayl", "TezTez.gms", string.Join(",", pkg.Files));
            string dir = Path.Combine(Path.GetTempPath(), "sunat_test_gms");
            if (Directory.Exists(dir)) Directory.Delete(dir, true);
            var files = Sunat.Plaginlar.Services.PackageInstaller.Install(pkg, new[] { dir });
            Eq("ZIP o'rnatish", "gms-ichi", File.ReadAllText(files[0]));
        }

        // saytning haqiqiy JSON javobi (miniilova/sample_catalog.json)
        string catPath = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(path)), "sample_catalog.json");
        var cat = Sunat.Plaginlar.Services.Catalog.Parse(File.ReadAllBytes(catPath));
        Eq("Katalog: birinchi plagin", "TT", cat.Plugins[0].Prefix);
        Eq("Katalog: narx", "150 000 so'm", cat.Plugins[0].PriceDisplay);
        Eq("Katalog: sotib olish havolasi", cat.Plugins[0].BuyUrl + "?kod=TT-K7QM-3XPA",
           Sunat.Plaginlar.Services.Catalog.BuyUrl(cat.Plugins[0], "TT-K7QM-3XPA"));

        Console.WriteLine($"{passed} ta to'g'ri, {failed} ta xato");
        return failed == 0 ? 0 : 1;
    }
}
