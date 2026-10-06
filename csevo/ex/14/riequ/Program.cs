// 슬라이드 p14-v13-ri-equ — IEquatable<자신> 구현, C# 13.0
using System;

ref struct Word : IEquatable<Word>       // T = a ref struct
{
    readonly ReadOnlySpan<char> s;
    public Word(ReadOnlySpan<char> s) { this.s = s; }
    public bool Equals(Word other)
        => s.Equals(other.s, StringComparison.OrdinalIgnoreCase);
}

class App
{
    static bool Same<T>(T a, T b)
        where T : IEquatable<T>, allows ref struct
        => a.Equals(b);

    static void Main()
    {
        ReadOnlySpan<char> line = "Span span SPAN";
        var a = new Word(line.Slice(0, 4));
        var b = new Word(line.Slice(5, 4));
        Console.WriteLine(Same(a, b));
        Console.WriteLine(Same(a, new Word("Spam")));
        Console.WriteLine(Same(3, 3));
    }
}
