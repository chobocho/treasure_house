// 슬라이드 p12-v11-lp-neg — Count 는 음수가 아니라고 본다, C# 11
using System;
using System.Collections.Generic;

class Program
{
    // no arm for Count < 0, and still no CS8509
    static string Size(List<int> xs) => xs switch
    {
        { Count: 0 } => "empty",
        { Count: < 5 } => "small",
        { Count: >= 5 } => "large",
    };

    static void Main()
    {
        Console.WriteLine(Size(new List<int>()));
        Console.WriteLine(Size(new List<int> { 1, 2, 3, 4, 5 }));
        int[] a = { 1 };
#if BAD
        Console.WriteLine(a is { Length: -1 });
#endif
#if BAD2
        Console.WriteLine(a is { Length: < 0 } or [_]);
#endif
        Console.WriteLine(a is { Length: >= 0 });
    }
}
