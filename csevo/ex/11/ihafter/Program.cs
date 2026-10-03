// 슬라이드 p11-v10-ih-argbad — 처리기 인수의 규칙, C# 10.0
using System;
using System.Runtime.CompilerServices;

[InterpolatedStringHandler]
public ref struct H
{
    public H(int literalLength, int formattedCount, int n)
        => Console.WriteLine($"  handler got n={n}");
    public void AppendLiteral(string s) { }
    public void AppendFormatted<T>(T v) { }
}

public class Box
{
#if !WARN
#pragma warning disable CS8947   // 'n' after 'h': see -define:WARN
#endif
    public void Late([InterpolatedStringHandlerArgument("n")] H h,
                     int n) => Console.WriteLine("  Late ran");
#if BAD
    // "" means the receiver: a static method has none
    public static void NoThis(
        [InterpolatedStringHandlerArgument("")] H h) { }
#endif
}

class App
{
    static void Main()
    {
        new Box().Late(n: 2, h: $"{1}");    // named: n goes first
#if LATE
        new Box().Late($"{1}", 2);           // positional: CS8950
#endif
    }
}
