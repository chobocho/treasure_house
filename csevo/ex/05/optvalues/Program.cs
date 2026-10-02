// 슬라이드 p5-v4-opt-values — 기본값이 될 수 있는 것, C# 4.0
using System;

enum Color { Red, Green }

class Program
{
    static void M(int i = 1 + 2, string s = null, Color c = Color.Green,
                  TimeSpan t = new TimeSpan(),
                  decimal m = default(decimal),
                  double d = Math.PI, int? n = null)
    {
        Console.WriteLine(i + " " + (s == null) + " " + c + " " + t
                          + " " + m + " " + d + " " + n.HasValue);
    }

#if BAD
    static void Bad1(DateTime when = DateTime.Now) { }
    static void Bad2(int[] a = new int[0]) { }
    static void Bad3(ref int x = 0) { }
#endif

    static void Main()
    {
        M();
    }
}
