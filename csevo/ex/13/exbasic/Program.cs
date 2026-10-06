// 슬라이드 p13-v12-experimental — [Experimental] 특성, C# 12.0
using System;
using System.Diagnostics.CodeAnalysis;

static class Lib
{
    [Experimental("MY001")]
    public static int Fast(int x) => x * 2;

    public static int Slow(int x) => x + x;
}

class App
{
    static void Main()
    {
        Console.WriteLine(Lib.Slow(21));
#if USE
        Console.WriteLine(Lib.Fast(21));    // diagnostic MY001
#endif
#pragma warning disable MY001
        Console.WriteLine(Lib.Fast(21));    // suppressed by id
#pragma warning restore MY001
    }
}
