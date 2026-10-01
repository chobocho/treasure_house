// 슬라이드 p4-v3-partial-later — 확장된 partial 메서드, C# 9
using System;

partial class Parser
{
    public partial int Count(string s);  // modifier + return value
}

partial class Parser
{
    public partial int Count(string s)   // implementation required
    {
        return s.Split(' ').Length;
    }
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Parser().Count("a b c"));
    }
}
