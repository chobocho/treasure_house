// 슬라이드 p7-v6-determ — 결정적 컴파일(-deterministic), C# 6.0
using System;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;

class App
{
    static void Main()
    {
        Assembly me = typeof(App).Assembly;
        byte[] dll = File.ReadAllBytes(me.Location);
        byte[] hash = SHA256.Create().ComputeHash(dll);
        Console.WriteLine("bytes  " + dll.Length);
        Console.WriteLine("sha256 " +
            BitConverter.ToString(hash, 0, 8).Replace("-", ""));
        Guid mvid = me.ManifestModule.ModuleVersionId;
        Console.WriteLine("mvid   " + mvid);
        // PE header: TimeDateStamp at e_lfanew + 8
        int pe = BitConverter.ToInt32(dll, 0x3C);
        uint stamp = BitConverter.ToUInt32(dll, pe + 8);
        Console.WriteLine("stamp  0x" + stamp.ToString("X8"));
    }
}
