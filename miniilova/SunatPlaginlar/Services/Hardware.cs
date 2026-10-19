using System;
using System.IO;
using System.Management;
using System.Runtime.InteropServices;
using System.Text;
using Sunat.Core;

namespace Sunat.Plaginlar.Services
{
    /// <summary>Kompyuter ID. Plagindagi SunatLicense.bas ham aynan shu qiymatlarni o'qiydi.</summary>
    static class Hardware
    {
        static string _mid;

        public static string MachineId => _mid ?? (_mid = Licensing.MachineId(HardwareString()));

        public static string HardwareString() =>
            Licensing.ChooseHardware(
                Wmi("Win32_ComputerSystemProduct", "UUID"),
                Wmi("Win32_BaseBoard", "SerialNumber"),
                Environment.GetEnvironmentVariable("COMPUTERNAME") ?? Environment.MachineName,
                SystemDriveSerial());

        static string Wmi(string cls, string prop)
        {
            try
            {
                using (var s = new ManagementObjectSearcher($"SELECT {prop} FROM {cls}"))
                    foreach (ManagementBaseObject o in s.Get())
                    {
                        string v = o[prop]?.ToString();
                        if (!string.IsNullOrWhiteSpace(v)) return v;
                    }
            }
            catch { }
            return "";
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        static extern bool GetVolumeInformation(string root, StringBuilder name, int nameSize, out uint serial,
            out uint maxLen, out uint flags, StringBuilder fs, int fsSize);

        // VBA dagi fso.GetDrive(Environ("SystemDrive")).SerialNumber bilan bir xil (ishorali 32-bit)
        static int SystemDriveSerial()
        {
            try
            {
                string drive = Environment.GetEnvironmentVariable("SystemDrive") ?? "C:";
                if (GetVolumeInformation(drive + "\\", null, 0, out uint serial, out _, out _, null, 0))
                    return unchecked((int)serial);
            }
            catch { }
            return 0;
        }
    }
}
