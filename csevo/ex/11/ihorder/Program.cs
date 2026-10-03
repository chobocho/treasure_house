// 슬라이드 p11-v10-ih-order — 처리기가 받는 인수와 평가 순서, C# 10.0
using System;
using System.Runtime.CompilerServices;

[InterpolatedStringHandler]
public ref struct Line
{
    public Line(int literalLength, int formattedCount,
                Log log, int level, out bool ok)
    {
        ok = level >= log.Min;
        Console.WriteLine($"  handler(log={log.Name}, level={level})"
                          + $" -> ok={ok}");
    }
    public void AppendLiteral(string s) => Console.WriteLine("  lit");
    public void AppendFormatted<T>(T v) => Console.WriteLine("  hole");
}

public class Log
{
    public string Name;
    public int Min = 2;
    public void Write(int level,
        [InterpolatedStringHandlerArgument("", "level")] Line text)
        => Console.WriteLine("  Write");
}

class App
{
    static T Say<T>(string what, T v)
    {
        Console.WriteLine("  eval " + what);
        return v;
    }

    static void Main()
    {
        var log = new Log { Name = "app" };
        Console.WriteLine("level 3:");
        Say("receiver", log)
            .Write(Say("level", 3), $"x={Say("hole", 7)}");
        Console.WriteLine("level 1:");
        Say("receiver", log)
            .Write(Say("level", 1), $"x={Say("hole", 7)}");
    }
}
