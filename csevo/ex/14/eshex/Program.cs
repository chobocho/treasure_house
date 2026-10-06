// 슬라이드 p14-v13-es-hex — \x1b 의 함정과 \e, C# 13
using System;

class Program
{
    static void Show(string label, string s)
    {
        Console.Write(label + " length " + s.Length + ":");
        foreach (char c in s)
            Console.Write(" U+" + ((int)c).ToString("X4"));
        Console.WriteLine();
    }

    static void Main()
    {
        Show("\\x1b[0m ", "\x1b[0m");   // '[' is not hex: fine
        Show("\\x1b7   ", "\x1b7");     // ESC then 7?
        Show("\\e7     ", "\e7");
        Show("\\x1bc   ", "\x1bc");     // ESC then c?
        Show("\\ec     ", "\ec");
        Show("\\x1bE1  ", "\x1bE1");    // up to four hex digits
        Show("\\u001b7 ", "\u001b7");   // \u is always four
    }
}
