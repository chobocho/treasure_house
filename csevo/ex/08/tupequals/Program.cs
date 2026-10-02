// 슬라이드 p8-v7-tuple-equals — 7.3 전의 비교는 Equals, C# 7.0
using System;

class App
{
    static void Main()
    {
        var a = (1, "x");
        (int n, string s) b = (1, "x");     // other names, same type
        Console.WriteLine(a.Equals(b));
        Console.WriteLine(a.GetHashCode() == b.GetHashCode());
        Console.WriteLine(a.Equals((1, "y")));
        object boxed = a;
        Console.WriteLine(boxed.Equals(b));
        Console.WriteLine(a.CompareTo((1, "w")) > 0);
#if BAD
        Console.WriteLine(a == b);
#endif
    }
}
