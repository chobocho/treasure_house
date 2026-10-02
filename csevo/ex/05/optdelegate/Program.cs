// 슬라이드 p5-v4-opt-delegate — 대리자의 기본값, C# 4.0
using System;

class Program
{
    delegate void Printer(string s = "delegate default");

    static void Print(string s = "method default")
    {
        Console.WriteLine(s);
    }

    static void Main()
    {
        Printer p = Print;
        Print();
        p();
#if BAD
        Action a = Print;       // no parameterless Print to bind
#endif
    }
}
