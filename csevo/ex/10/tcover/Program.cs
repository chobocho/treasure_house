// 슬라이드 p10-v9-tc-over — 조건식과 오버로드, C# 9.0
using System;

class App
{
    static void M(short s) => Console.WriteLine("M(short)");
    static void M(long l) => Console.WriteLine("M(long)");
    static void N(short a, short b) => Console.WriteLine("N(short)");
    static void N(long a, long b) => Console.WriteLine("N(long)");
    static void P(short? s) => Console.WriteLine("P(short?)");
    static void P(long? l) => Console.WriteLine("P(long?)");

    static void Main(string[] args)
    {
        bool b = args.Length == 0;
        M(b ? 1 : 2);                                // ?:
        M(b switch { true => 1, false => 2 });       // switch
#if PAIR
        N(b ? 1 : 2, 1);
#endif
#if NUL
        P(b ? 1 : null);                             // no natural type
#endif
    }
}
