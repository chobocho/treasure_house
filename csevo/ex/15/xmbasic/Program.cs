// 슬라이드 p15-v14-ext — 확장 블록 extension(string s), C# 14
using System;

static class TextExt
{
    // C# 3: the receiver is the first parameter, marked 'this'
    public static int WordCount(this string s) => s.Split(' ').Length;

    // C# 14: the receiver is declared once for the whole block
    extension(string s)
    {
        public string Initials()
        {
            string r = "";
            foreach (string w in s.Split(' ')) r += char.ToUpper(w[0]);
            return r;
        }
        public string Shout() => s.ToUpper() + "!";
    }
}

class Program
{
    static void Main()
    {
        string line = "to be or not";
        Console.WriteLine(line.WordCount() + " " + line.Initials()
            + " " + line.Shout());
        Console.WriteLine(TextExt.Initials(line));   // a static call
    }
}
