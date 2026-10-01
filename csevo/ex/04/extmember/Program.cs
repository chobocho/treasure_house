// 슬라이드 p4-v3-ext-member — 확장 블록: 확장 속성, C# 14
using System;

static class StringExt
{
    extension(string s)
    {
        public int Words => s.Split(' ').Length;   // extension property
        public bool IsBlank() => s.Trim().Length == 0;
    }

    public static string Shout(this string s) => s.ToUpper(); // C# 3
}

class App
{
    static void Main()
    {
        string line = "to be or not";
        Console.WriteLine(line.Words + " " + "  ".IsBlank()
            + " " + line.Shout());
    }
}
