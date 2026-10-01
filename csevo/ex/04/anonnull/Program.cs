// 슬라이드 p4-v3-anon-null — 형식 없는 식은 속성이 못 된다, C# 3.0
using System;

class App
{
    static void Nothing() { }

    static void Main()
    {
        var a = new { Name = null };
        var b = new { F = x => x };
        var c = new { R = Nothing() };
        var ok = new { Name = (string)null, Count = 0 };
        Console.WriteLine(ok);
    }
}
