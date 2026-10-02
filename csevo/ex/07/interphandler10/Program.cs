// 슬라이드 p7-v6-interp-handler10 — 보간 문자열 처리기, C# 10.0
using System;
using System.Runtime.CompilerServices;
using System.Text;

[InterpolatedStringHandler]
public ref struct TraceHandler
{
    StringBuilder sb;
    public TraceHandler(int literalLength, int formattedCount)
    {
        Console.WriteLine($"  ctor({literalLength}, {formattedCount})");
        sb = new StringBuilder();
    }
    public void AppendLiteral(string s)
    {
        Console.WriteLine($"  AppendLiteral(\"{s}\")");
        sb.Append(s);
    }
    public void AppendFormatted<T>(T value, string format = null)
    {
        Console.WriteLine($"  AppendFormatted<{typeof(T).Name}>" +
            $"({value}, {format ?? "null"})");
        IFormattable f = value as IFormattable;
        sb.Append(f != null ? f.ToString(format, null) : value + "");
    }
    public override string ToString() => sb.ToString();
}

class App
{
    static void Log(TraceHandler h) => Console.WriteLine(h.ToString());

    static void Main()
    {
        int n = 3;
        double t = 0.5;
        Log($"n={n}, t={t:F2}!");
    }
}
