// 슬라이드 p11-v10-ns-il — 형식 이름과 IL 바이트의 해시, C# 10.0
using System;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;

class App
{
    static void Main()
    {
        var t = typeof(Shop.Cart);
        var il = t.GetMethods(BindingFlags.Instance
                | BindingFlags.Public | BindingFlags.NonPublic
                | BindingFlags.DeclaredOnly)
            .OrderBy(m => m.Name)
            .SelectMany(m => m.GetMethodBody().GetILAsByteArray())
            .ToArray();
        Console.WriteLine(t.FullName + " " + il.Length + " IL bytes");
        var hash = SHA256.HashData(il);
        Console.WriteLine(Convert.ToHexString(hash)[..16]);
    }
}
