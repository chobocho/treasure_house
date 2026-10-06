// 슬라이드 p13-v12-al-global — 별칭을 쓰는 다른 파일, C# 12.0
using System;

class App
{
    static Money Total(Lines lines)
    {
        Money sum = 0;
        foreach (var l in lines) sum += l.Price * l.Qty;
        return sum;
    }

    static void Main()
    {
        Lines order = [("pen", 1.5m, 2), ("ink", 4m, 1)];
        Console.WriteLine($"{order.Length} lines, {Total(order)}");
    }
}
