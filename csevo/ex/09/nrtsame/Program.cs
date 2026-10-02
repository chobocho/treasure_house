// 슬라이드 p9-v8-nrt-sametype — string? 과 string 은 같은 형식, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;

class App
{
    static string M(string s) => "M(string)";
#if DUP
    static string M(string? s) => "M(string?)";   // same signature
#endif

    static void Main()
    {
        string? a = "x";
        string b = "y";
        Console.WriteLine(a.GetType() == b.GetType());
        Console.WriteLine(typeof(List<string?>) ==
            typeof(List<string>));
        Console.WriteLine(new List<string?>() is List<string>);
        Console.WriteLine(M(b));
#if BAD
        Console.WriteLine(typeof(string?));
#endif
    }
}
