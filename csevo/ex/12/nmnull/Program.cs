// 슬라이드 p12-v11-nameof-nullable — nullable 특성과 nameof, C# 11.0
using System;
using System.Diagnostics.CodeAnalysis;

static class Text
{
    [return: NotNullIfNotNull(nameof(s))]
    public static string? Trim(string? s) => s?.Trim();

#if STALE
    [return: NotNullIfNotNull("text")]          // renamed parameter
    public static string? Upper(string? s) => s?.ToUpperInvariant();
#endif
}

class App
{
    static void Main()
    {
        string a = Text.Trim("  ada  ");           // no warning
        Console.WriteLine($"[{a}] {a.Length}");
#if NULLARG
        string b = Text.Trim(null);                // may be null
#endif
#if STALE
        string c = Text.Upper("ada");
#endif
    }
}
