// 슬라이드 p14-v13-esc — 새 이스케이프 시퀀스 \e, C# 13
using System;

class Program
{
    static void Main()
    {
        char e = '\e';
        Console.WriteLine((int)e);              // 27
        Console.WriteLine(e == '\u001b');
        Console.WriteLine(e == '\U0000001b');
        Console.WriteLine(e == '\x1b');
        Console.WriteLine(e == (char)0x1b);

        string bold = "\e[1m";                  // ANSI: bold on
        Console.WriteLine(bold.Length + " "
            + Convert.ToHexString(
                System.Text.Encoding.ASCII.GetBytes(bold)));
    }
}
