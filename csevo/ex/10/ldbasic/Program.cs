// 슬라이드 p10-v9-lambda-discard — 람다의 버리기 매개변수, C# 9.0
using System;

class App
{
    static void Main()
    {
        Func<int, string, int> a = (int _, string _) => 1;
        Func<int, int, int> b = delegate (int _, int _) { return 2; };
        Console.WriteLine(a(0, "x") + b(0, 0));

        int _ = 5;                          // a local named _
        Func<int, int, int> c = (_, _) => _;   // discards: no name
        Console.WriteLine(c(1, 2));
        Func<int, int> d = _ => _ * 10;        // one _: a parameter
        Console.WriteLine(d(3));
    }
}
