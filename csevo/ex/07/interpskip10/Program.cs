// 슬라이드 p7-v6-interp-skip10 — 구멍을 건너뛰는 처리기, C# 10.0
using System;
using System.Runtime.CompilerServices;
using System.Text;

[InterpolatedStringHandler]
public ref struct LevelHandler
{
    StringBuilder sb;
    public LevelHandler(int literalLength, int formattedCount,
        Logger logger, out bool enabled)
    {
        enabled = logger.Enabled;
        sb = enabled ? new StringBuilder() : null;
    }
    public void AppendLiteral(string s) => sb.Append(s);
    public void AppendFormatted<T>(T value) => sb.Append(value);
    public string Text => sb?.ToString();
}

public class Logger
{
    public bool Enabled;
    public void Debug([InterpolatedStringHandlerArgument("")]
        LevelHandler h) => Console.WriteLine("log: " + (h.Text ?? "-"));
}

class App
{
    static int calls;
    static int Expensive() => ++calls;

    static void Main()
    {
        var log = new Logger { Enabled = false };
        log.Debug($"value {Expensive()}");
        log.Enabled = true;
        log.Debug($"value {Expensive()}");
        Console.WriteLine("Expensive() ran " + calls + " time(s)");
    }
}
