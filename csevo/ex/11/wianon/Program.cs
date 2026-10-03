// 슬라이드 p11-v10-wi-anon — 익명 형식의 with, C# 10.0
using System;

class App
{
    static void Main()
    {
        var a = new { Name = "ann", Age = 3 };
        var b = a with { Age = 4 };
        Console.WriteLine(a + " " + b);
        Console.WriteLine(ReferenceEquals(a, b) + " "
            + (a.GetType() == b.GetType()));
        var c = b with { Age = 3 };         // back to a's values
        Console.WriteLine(a.Equals(c) + " " + (a == c));
#if BAD
        var d = a with { City = "x" };
#endif
    }
}
