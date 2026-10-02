// 슬라이드 p9-v8-nrt-bclret — .NET 10 의 주석이 바꾸는 경고, C# 8.0
#nullable enable
using System;

class App
{
    static void Main()
    {
        object o = 42;
        string a = o.ToString();           // CS8600
        string b = Environment.GetEnvironmentVariable("X");  // CS8600
        string c = Console.ReadLine();     // CS8600
        string d = o.GetType().Name;       // fine
        string e = string.Concat("x", null);   // fine
        Console.WriteLine(a + "|" + (b ?? "-") + "|" + (c ?? "-")
            + "|" + d + "|" + e);
    }
}
