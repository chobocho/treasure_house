// 슬라이드 p11-v10-la-later — 뒤 버전의 람다: 기본값과 params, C# 12
using System;

class App
{
    static void Main()
    {
        var greet = (string who = "world") => $"hello {who}";
        var count = (params int[] xs) => xs.Length;

        Console.WriteLine(greet() + " / " + greet("C#"));
        Console.WriteLine(count() + " " + count(1, 2, 3));
        // not Func<string, string>: a synthesized delegate type
        Console.WriteLine(greet.GetType().Name + " " +
                          count.GetType().Name);
        Console.WriteLine(greet.Method.GetParameters()[0].DefaultValue);
#if BAD
        Func<string, string> f = greet;   // a different delegate type
#endif
    }
}
