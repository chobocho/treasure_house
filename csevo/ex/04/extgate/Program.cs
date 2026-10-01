// 슬라이드 p4-v3-ext-gate — 확장 메서드, C# 3.0
using System;

static class StringExt
{
    public static int WordCount(this string s)
    {
        return s.Split(' ').Length;
    }
}

class App
{
    static void Main()
    {
        string line = "to be or not";
        Console.WriteLine(line.WordCount());               // C# 3
        Console.WriteLine(StringExt.WordCount(line)); // static call
    }
}
