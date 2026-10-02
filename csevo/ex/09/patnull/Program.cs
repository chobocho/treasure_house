// 슬라이드 p9-v8-proppat-null — { } 는 null 이 아님, C# 8.0
using System;

class App
{
    static string Check(string s)
    {
        if (s is { Length: 0 }) return "empty";
        if (s is { } t) return "text of " + t.Length;
        return "null";
    }

    static void Main()
    {
        Console.WriteLine(Check(""));
        Console.WriteLine(Check("abc"));
        Console.WriteLine(Check(null));

        int? n = null;
        Console.WriteLine(n is { });        // has a value?
        n = 3;
        Console.WriteLine(n is { } v ? "value " + v : "none");

        object o = null;
        Console.WriteLine("{0} {1}", o is object, o is { });
    }
}
