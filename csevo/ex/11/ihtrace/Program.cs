// 슬라이드 p11-v10-handler — 보간 문자열 처리기, C# 10.0
using System;
using System.Runtime.CompilerServices;

[InterpolatedStringHandler]
public struct Trace              // a plain struct is enough
{
    public Trace(int literalLength, int formattedCount)
    {
        Console.WriteLine($"  new({literalLength}, {formattedCount})");
    }
    public void AppendLiteral(string s)
    {
        Console.WriteLine($"  AppendLiteral(\"{s}\")");
    }
    public void AppendFormatted<T>(T v)
    {
        Console.WriteLine($"  AppendFormatted<{typeof(T).Name}>({v})");
    }
    public void AppendFormatted<T>(T v, int alignment = 0,
                                   string format = null)
    {
        Console.WriteLine($"  AppendFormatted<{typeof(T).Name}>" +
                          $"({v}, {alignment}, {format ?? "null"})");
    }
    public void AppendFormatted(string s)
    {
        Console.WriteLine($"  AppendFormatted(string \"{s}\")");
    }
}

class App
{
    static void Show(Trace t) { }

    static void Main()
    {
        int n = 42;
        string s = "hi";
        Console.WriteLine("one string:");
        Show($"{{n}}={n,5:X} s={s}!");
        Console.WriteLine("two strings joined by +:");
        Show($"a{1}" + $"b{n:D3}");
    }
}
