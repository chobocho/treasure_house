// 슬라이드 p10-v9-pm-regex — 생성기가 채울 자리, C# 9.0
using System;
using System.Text.RegularExpressions;

partial class App
{
    // In a real build the regex source generator writes the body.
    [GeneratedRegex("(dog|cat|fish)")]
    private static partial Regex Pet();

    static void Main() => Console.WriteLine(Pet().IsMatch("my cat"));
}
