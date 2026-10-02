// 슬라이드 p9-v8-nrt-bang — ! 는 경고만 끈다, C# 8.0
#nullable enable
using System;

class App
{
    static string? Find(int id) => id == 1 ? "Ada" : null;

    static void Main()
    {
        string a = Find(1)!;               // "trust me": no warning
        string b = Find(2)!;               // same promise, broken
        Console.WriteLine(a.Length);
        Console.WriteLine("no warning so far");
        Console.WriteLine(b.Length);       // NullReferenceException
    }
}
