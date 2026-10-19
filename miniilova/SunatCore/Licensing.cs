// Sunat.cc Plaginlar - litsenziya algoritmlari.
// kalitbot/litsenziya.py va plaginlardagi SunatLicense.bas bilan AYNAN bir xil
// ishlashi shart. Tekshiruv: SunatCore.Tests (testvectors.json bilan).
// Bu faylda maxfiy kalit YO'Q: ActivationCode faqat testlar uchun kalitni parametr sifatida oladi.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace Sunat.Core
{
    public static class Licensing
    {
        public const string Alpha = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        public const string MidSalt = "SunatCC|MID|v1";
        public const string OffSalt = "SunatCC|OFF|v1";
        const long P = 2147483647;

        static readonly HashSet<string> BadUuids = new HashSet<string> { "03000200-0400-0500-0006-000700080009" };
        static readonly HashSet<string> BadBoards = new HashSet<string>
        {
            "DEFAULT STRING", "TO BE FILLED BY O.E.M.", "NONE", "N/A", "NA", "NOT APPLICABLE",
            "SYSTEM SERIAL NUMBER", "BASE BOARD SERIAL NUMBER", "SERIAL NUMBER", "INVALID",
            "NOT AVAILABLE", "123456789", "OEM", "O.E.M.", "DEFAULT",
        };

        // Ikki qismli xesh (mod 2^31-1), 16 ta hex belgi
        public static string HashHex(string s)
        {
            long h1 = 7, h2 = 13;
            foreach (char ch in s)
            {
                long c = ch;
                h1 = (h1 * 131 + c) % P;
                h2 = (h2 * 257 + c + 1) % P;
            }
            return h1.ToString("X8") + h2.ToString("X8");
        }

        static string Reverse(string s)
        {
            var a = s.ToCharArray();
            Array.Reverse(a);
            return new string(a);
        }

        public static string MixCode(string seed, int nChars, string secret)
        {
            string h = HashHex(seed + "|" + secret);
            for (int i = 0; i < 12; i++)
                h = HashHex(h + "|" + secret + "|" + Reverse(h) + seed);
            h += HashHex(h + secret);
            var sb = new StringBuilder();
            for (int i = 0; i < nChars; i++)
            {
                int v = Convert.ToInt32(h.Substring(i * 4 + 2, 2), 16) % 32;
                sb.Append(Alpha[v]);
            }
            return sb.ToString();
        }

        public static string Clean(string text)
        {
            var sb = new StringBuilder();
            foreach (char ch in (text ?? "").ToUpperInvariant())
                if ((ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9')) sb.Append(ch);
            return sb.ToString();
        }

        public static string NormalizeHw(string hw)
        {
            var sb = new StringBuilder();
            foreach (char ch in (hw ?? "").ToUpperInvariant())
                if ((ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9') || ch == ':' || ch == '-') sb.Append(ch);
            return sb.ToString();
        }

        public static string ChooseHardware(string uuid, string board, string computerName, int volumeSerial)
        {
            string u = (uuid ?? "").Trim().ToUpperInvariant();
            if (u.Length >= 8 && !BadUuids.Contains(u) && u.Any(c => c != '0' && c != 'F' && c != '-'))
                return "UUID:" + u;
            string b = (board ?? "").Trim().ToUpperInvariant();
            if (b.Length >= 4 && !BadBoards.Contains(b) && b.Any(c => c != '0' && c != '.' && c != ' '))
                return "BB:" + b;
            return "PC:" + (computerName ?? "").Trim().ToUpperInvariant() + ":" + volumeSerial;
        }

        static string Fmt8(string c) => c.Substring(0, 4) + "-" + c.Substring(4, 4);

        /// <summary>Uskuna satridan kompyuter ID: XXXX-XXXX</summary>
        public static string MachineId(string hw) => Fmt8(MixCode("mid|" + NormalizeHw(hw), 8, MidSalt));

        public static string RequestId(string prefix, string mid) => prefix + "-" + mid;

        public static char CheckChar(string s)
        {
            long total = 0;
            for (int i = 0; i < s.Length; i++) total += (i + 1) * (long)s[i];
            return Alpha[(int)(total % 32)];
        }

        /// <summary>Faqat testlar uchun: bot shu formula bilan kod beradi.</summary>
        public static string ActivationCode(string prefix, string mid, string secret)
        {
            string seed = prefix + "|" + mid;
            string body = MixCode("act|" + seed, 8, secret) + MixCode("act2|" + seed, 3, secret);
            body += CheckChar(prefix + body);
            return prefix + "-" + body.Substring(0, 4) + "-" + body.Substring(4, 4) + "-" + body.Substring(8, 4);
        }

        /// <summary>Kod ko'rinishi va nazorat belgisi to'g'rimi. To'g'ri bo'lsa TT-XXXX-XXXX-XXXX, aks holda null.</summary>
        public static string NormalizeCode(string code, string prefix)
        {
            string s = Clean(code);
            if (!s.StartsWith(prefix, StringComparison.Ordinal) || s.Length != prefix.Length + 12) return null;
            string body = s.Substring(prefix.Length);
            if (body.Any(ch => Alpha.IndexOf(ch) < 0)) return null;
            if (body[11] != CheckChar(prefix + body.Substring(0, 11))) return null;
            return prefix + "-" + body.Substring(0, 4) + "-" + body.Substring(4, 4) + "-" + body.Substring(8, 4);
        }

        public static string DeactConfirm(string code, string mid) => Fmt8(MixCode("off|" + Clean(code) + "|" + mid, 8, OffSalt));
    }
}
