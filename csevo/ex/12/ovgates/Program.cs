// 슬라이드 p12-v11-gates-demo — C# 11 의 문자열 기능 넷, C# 11.0
using System;

class App
{
    static void Main()
    {
        string raw = """He said "hi" \o/""";       // raw string literal
        ReadOnlySpan<byte> u8 = "abc"u8;          // UTF-8 literal
        ReadOnlySpan<char> word = "stop".AsSpan();
        bool stop = word is "stop";               // span pattern
        Console.WriteLine($"{raw} {u8.Length} {stop switch
        {
            true => "stop",                       // newline in hole
            false => "go"
        }}");
    }
}
