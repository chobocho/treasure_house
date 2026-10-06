// 슬라이드 p14-v13-or-neg — 음수 우선순위로 옛 판을 뒤로, C# 13
using System;
using System.Runtime.CompilerServices;

static class Check
{
#if !NOPRI
    [OverloadResolutionPriority(-1)]
#endif
    public static void That(bool ok)
        => Console.WriteLine(ok ? "ok" : "failed");

    public static void That(bool ok,
        [CallerArgumentExpression(nameof(ok))] string expr = "")
        => Console.WriteLine(ok ? "ok" : "failed: " + expr);
}

class Program
{
    static void Main()
    {
        int n = 3;
        Check.That(n > 0);
        Check.That(n > 5);
        Check.That(n * 2 == 7);
    }
}
