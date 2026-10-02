// 슬라이드 p9-v8-range-string — 문자열의 범위는 Substring, C# 8.0
using System;

class App
{
    static void Main()
    {
        string s = "ID-042-KR";
        string head = s[..2];
        string tail = s[^2..];
        Console.WriteLine("{0} / {1} / {2}", head, s[3..6], tail);
        Console.WriteLine(s[^1]);                 // a char
        // Substring(0, Length) gives back the same object
        Console.WriteLine("s[..] is s: {0}", ReferenceEquals(s[..], s));
        // no new string: slice a span instead
        ReadOnlySpan<char> mid = s.AsSpan()[3..6];
        Console.WriteLine(int.Parse(mid) + 1);
    }
}
