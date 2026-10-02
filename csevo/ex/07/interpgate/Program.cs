// 슬라이드 p7-v6-interp-gate — 문자열 보간, C# 6.0
using System;

class App
{
    static void Main()
    {
        string name = "Ada";
        int items = 3;
        decimal total = 41.5m;

        string a = string.Format("{0} bought {1} items for {2}",
            name, items, total);
        string b = $"{name} bought {items} items for {total}";

        Console.WriteLine(a);
        Console.WriteLine(b);
        Console.WriteLine(a == b);
    }
}
