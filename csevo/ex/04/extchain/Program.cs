// 슬라이드 p4-v3-ext-chain — 왼쪽에서 오른쪽으로 읽히는 사슬, C# 3.0
using System;

static class Text
{
    public static string Squash(this string s)
    {
        return s.Replace("  ", " ");
    }
    public static string Cap(this string s)
    {
        return s.Substring(0, 1).ToUpper() + s.Substring(1);
    }
    public static string Dot(this string s) { return s + "."; }
}

class App
{
    static void Main()
    {
        string raw = "  hello  world ";
        // read inside-out: the last step is written first
        Console.WriteLine(Text.Dot(Text.Cap(Text.Squash(raw.Trim()))));
        // read in the order it runs
        Console.WriteLine(raw.Trim().Squash().Cap().Dot());
    }
}
