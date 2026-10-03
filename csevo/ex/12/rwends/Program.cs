// 슬라이드 p12-v11-raw-ends — 첫 줄바꿈과 끝 줄바꿈, C# 11.0
using System;

class App
{
    static void Show(string s) =>
        Console.WriteLine($"[{s.Replace("\n", "\\n")}] {s.Length}");

    static void Main()
    {
        Show("""
            one line
            """);
        Show("""
            ends with a newline

            """);
        Show("""

            starts with a newline
            """);
        Show("""
            "quoted at both ends"
            """);
        Show("""
            ""two quotes""
            """);
    }
}
