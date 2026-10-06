// 슬라이드 p13-v12-ld-values — 무엇을 기본값으로 쓸 수 있나, C# 12
using System;

readonly record struct Pt(int X);

class Program
{
    const int Two = 2;

    static void Main()
    {
        var f = (int a = Two * 3, string s = null, Pt p = default,
                 Pt q = new(), DayOfWeek d = DayOfWeek.Friday) =>
            a + " " + (s ?? "null") + " " + p.X + " " + q.X + " " + d;
        Console.WriteLine(f());
#if BAD
        var g = (int now = Environment.TickCount) => now;
#endif
#if BAD2
        var h = (ref int r = 0) => r;
#endif
#if BAD3
        var k = (int a = 1, int b) => a + b;
#endif
    }
}
