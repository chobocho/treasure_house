// 슬라이드 p12-v11-spanpat-subsume — 목록 패턴과 섞으면, C# 11.0
using System;

class App
{
    static int Span(ReadOnlySpan<char> s) => s switch
    {
        { Length: 0 } => 0,
        "" => 1,                  // never reached, no diagnostic
        ['A', ..] => 2,
        "ABC" => 3,               // never reached, no diagnostic
        _ => 4,
    };

    static int Str(string s) => s switch
    {
        { Length: 0 } => 0,
        "" => 1,
        ['A', ..] => 2,
        "ABC" => 3,
        _ => 4,
    };

    static void Main()
    {
        foreach (string s in new[] { "", "ABC", "xyz" })
            Console.WriteLine($"{s,-4} span {Span(s)} string {Str(s)}");
    }
}
