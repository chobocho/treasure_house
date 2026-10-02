// 슬라이드 p9-v8-nrt-ifnotnull — NotNullIfNotNull, C# 8.0
#nullable enable
using System;
using System.Diagnostics.CodeAnalysis;

class App
{
    // null in, null out; text in, text out
#if BAD
    [return: NotNullIfNotNull(nameof(s))]   // C# 11 scope rule
#else
    [return: NotNullIfNotNull("s")]
#endif
    static string? Trim(string? s) => s?.Trim();

    static void Main()
    {
        string a = Trim("  hi  ");            // no warning
        string? b = Trim(null);
        Console.WriteLine("[" + a + "] " + (b == null));
    }
}
