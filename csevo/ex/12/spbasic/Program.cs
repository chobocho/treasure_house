// 슬라이드 p12-v11-spanpat — 스팬을 상수 문자열 패턴으로, C# 11.0
using System;

class App
{
    static bool IsYes(ReadOnlySpan<char> s) => s is "y" or "yes";

    static int Method(ReadOnlySpan<char> verb) => verb switch
    {
        "GET" => 1,
        "PUT" => 2,
        "DELETE" => 3,
        _ => 0,
    };

    static void Main()
    {
        string line = "GET /index.html";
        ReadOnlySpan<char> verb = line.AsSpan(0, line.IndexOf(' '));
        Console.WriteLine(Method(verb) + " " + Method("PATCH"));
        Console.WriteLine(IsYes("yes".AsSpan()) + " " + IsYes("no"));

        Span<char> buf = stackalloc char[3];
        "abc".CopyTo(buf);
        buf[0] = 'A';
        Console.WriteLine(buf is "Abc");
    }
}
