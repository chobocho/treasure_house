// 슬라이드 p12-v11-raw-interp — $ 의 개수가 구멍의 중괄호 수, C# 11.0
using System;

class App
{
    static void Main()
    {
        int n = 7;
        Console.WriteLine($"""n is {n}, "quoted" """);
        Console.WriteLine($$"""{ "n": {{n}} }""");
        Console.WriteLine($$"""X{{{n + 1}}}Z""");        // 2N-1 braces
        Console.WriteLine($$$"""{{ {{{n}}} }}""");
#if FOUR
        Console.WriteLine($$"""{{{{n}}}}""");            // 2N braces
#endif
#if ONE
        Console.WriteLine($"""{ "n": {n} }""");
#endif
#if CLOSE
        Console.WriteLine($"""a}b""");
#endif
#if START
        Console.WriteLine($"""
            n is
{n}
            """);
#endif
    }
}
