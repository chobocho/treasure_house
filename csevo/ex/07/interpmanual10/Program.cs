// 슬라이드 p7-v6-interp-manual10 — 처리기를 손으로 부르기, C# 10.0
using System;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        string name = "Ada";
        int n = 255;

        string a = $"{name}: {n,5:X}!";

        var h = new DefaultInterpolatedStringHandler(3, 2);
        h.AppendFormatted(name);
        h.AppendLiteral(": ");
        h.AppendFormatted(n, 5, "X");
        h.AppendLiteral("!");
        string b = h.ToStringAndClear();

        Console.WriteLine(a);
        Console.WriteLine(b);
        Console.WriteLine(a == b);
    }
}
