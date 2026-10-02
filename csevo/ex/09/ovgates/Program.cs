// 슬라이드 p9-v8-gates-demo — C# 8.0 의 게이트 여섯을 한 파일에, C# 8.0
using System;

class App
{
    static string Kind(object o) => o switch    // switch expression
    {
        int n => "int " + n,
        _ => "other",
    };

    static void Main()
    {
        int[] a = { 1, 2, 3, 4 };
        Console.WriteLine(a[^1]);               // index operator
        Console.WriteLine(a[1..3].Length);      // range operator
        string s = null;
        s ??= "filled";                         // coalescing assignment
        Console.WriteLine(s);
        Console.WriteLine(Kind(42));
        static int Twice(int x) => x * 2;       // static local function
        Console.WriteLine(Twice(21));
    }
}
