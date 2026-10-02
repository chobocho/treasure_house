// 슬라이드 p9-v8-nrt-gate — nullable 참조 형식, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;

class App
{
    static readonly Dictionary<int, string> names =
        new Dictionary<int, string> { { 1, "Ada" } };

    // string? : "may be null" is now part of the signature
    static string? Find(int id)
    {
        return names.TryGetValue(id, out string? n) ? n : null;
    }

    static void Main()
    {
        string? a = Find(1), b = Find(2);
        Console.WriteLine(a?.Length);
        if (b != null) Console.WriteLine(b.Length);
        else Console.WriteLine("no name for 2");
    }
}
