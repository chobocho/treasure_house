// 슬라이드 p12-v11-lp-exhaust — 목록 패턴과 빠짐없는 switch, C# 11
using System;

class Program
{
    static string Size(int[] a) => a switch
    {
        [] => "0",
#if !BAD
        [_] => "1",
#endif
        [_, _, ..] => "2+",
    };

    static string Ends(int[] a) => a switch
    {
        [] => "empty",
        [< 0, ..] => "neg first",
        [.., >= 0] => "non-neg last",
#if !BAD2
        [_, .., < 0] => "neg last",
#endif
    };

    static void Main()
    {
        Console.WriteLine(Size(new[] { 4 }) + " " + Size(new int[3]));
        Console.WriteLine(Ends(new[] { -1 }) + ", "
            + Ends(new[] { 2 }));
        Console.WriteLine(Ends(new[] { 3, -2 }));
    }
}
