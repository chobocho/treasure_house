// 슬라이드 p7-v6-interp-null — null 구멍은 빈 문자열, C# 6.0
using System;

class App
{
    static void Main()
    {
        string s = null;
        object o = null;
        int? n = null;
        Console.WriteLine($"[{s}] [{o}] [{n}] [{n,3}]");
        Console.WriteLine($"[{s ?? "none"}] [{n ?? -1}]");
        Console.WriteLine("concat: [" + s + "]");
        try
        {
            Console.WriteLine($"[{s.Length}]");
        }
        catch (NullReferenceException)
        {
            Console.WriteLine("s.Length: NullReferenceException");
        }
    }
}
