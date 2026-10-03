// 슬라이드 p11-v10-ih-local — 처리기 형식의 지역 변수, C# 10.0
using System;
using System.Runtime.CompilerServices;

[InterpolatedStringHandler]
public class Parts                    // a class works too
{
    public int Count;
    public Parts(int literalLength, int formattedCount)
        => Console.WriteLine(
               $"  new Parts({literalLength}, {formattedCount})");
    public void AppendLiteral(string s) => Count++;
    public void AppendFormatted<T>(T v) => Count++;
}

class App
{
    static void Main()
    {
        int a = 1, b = 2;
        Parts p = $"a={a}, b={b}";            // a handler local
        Console.WriteLine($"  {p.Count} parts");
        var q = (Parts)$"{a}{b}";             // a cast also converts
        Console.WriteLine($"  {q.Count} parts");
        var s = $"{a}{b}";                    // var: still a string
        Console.WriteLine($"  {s.GetType().Name}");
    }
}
