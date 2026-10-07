// 슬라이드 p15-v14-sp-compose — 스팬 변환 뒤의 사용자 정의 변환, C# 14
using System;

readonly struct Word
{
    readonly string text;
    Word(string t) { text = t; }
    public static implicit operator Word(ReadOnlySpan<char> s)
        => new Word(s.Trim().ToString());
    public override string ToString() => "<" + text + ">";
}

class Program
{
    static void Main()
    {
        Word a = "  hi  ".AsSpan();       // always ok
        Console.WriteLine(a);
#if STR
        Word b = "  yo  ";                // string -> span -> Word
        Console.WriteLine(b);
#endif
    }
}
