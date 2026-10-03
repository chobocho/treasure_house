// 슬라이드 p12-v11-nameof-caller — 호출자 식과 nameof, C# 11.0
using System;
using System.Runtime.CompilerServices;

static class Check
{
    public static void That(bool condition,
        [CallerArgumentExpression(nameof(condition))]
        string expr = null)
    {
        Console.WriteLine((condition ? "ok:     " : "failed: ") + expr);
    }
}

class App
{
    static void Main()
    {
        int width = 80, height = -1;
        Check.That(width > 0);
        Check.That(height > 0 && height < 1000);
    }
}
