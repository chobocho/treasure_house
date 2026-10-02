// 슬라이드 p10-v9-pat-notprec — not 은 가장 가까운 패턴만, C# 9.0
using System;

class App
{
    static void Main()
    {
        foreach (int x in new[] { 1, 2, 3 })
        {
            bool wrong = x is not 1 or 2;     // (not 1) or 2
            bool right = x is not (1 or 2);
            bool also = x is not 1 and not 2;
            Console.WriteLine($"{x}: {wrong} {right} {also}");
        }
    }
}
