// 슬라이드 p14-v13-refiface — 인터페이스를 구현하는 ref struct, C# 13.0
using System;

interface ICounter
{
    int Count(char c);
}

ref struct SpanText : ICounter        // C# 13: allowed
{
    readonly ReadOnlySpan<char> text;
    public SpanText(ReadOnlySpan<char> t) { text = t; }
    public int Count(char c) => text.Count(c);
}

class StringText : ICounter
{
    readonly string text;
    public StringText(string t) { text = t; }
    public int Count(char c) => text.Split(c).Length - 1;
}

class App
{
    // one algorithm for both — no boxing of the ref struct
    static int Vowels<T>(T t) where T : ICounter, allows ref struct
        => t.Count('a') + t.Count('e') + t.Count('o');

    static void Main()
    {
        ReadOnlySpan<char> line = "one example of text";
        Console.WriteLine(Vowels(new SpanText(line.Slice(4, 7))));
        Console.WriteLine(Vowels(new StringText("one example")));
        Console.WriteLine(new SpanText(line).Count('e'));
    }
}
