// 슬라이드 p12-v11-lp-subsume — 같은 원소를 가리키는 두 패턴, C# 11
using System;

class Program
{
    static string M(int[] a)
    {
        switch (a)
        {
            case [_, .., 1]: return "last is 1";
#if BAD
            case [.., _, 1]: return "also last is 1";
#endif
            case [_, 1, ..]: return "a[1] is 1";
            case [.., 1, _]: return "a[^2] is 1";
            default: return "other";
        }
    }

    static void Main()
    {
        Console.WriteLine(M(new[] { 0, 1 }));
        Console.WriteLine(M(new[] { 0, 1, 2 }));
        Console.WriteLine(M(new[] { 0, 0, 1, 2 }));
        Console.WriteLine(M(new[] { 1 }));
        // two names for one element when Length is 3
        int[] t = { 5, 7, 9 };
        Console.WriteLine(t is [_, var b, ..] and [.., var c, _]
            ? b + " " + c : "-");
    }
}
