// 슬라이드 p8-v7_1-default-over — 오버로드 앞의 default, C# 7.1
using System;

class App
{
    static void M(int x) { Console.WriteLine("M(int) " + x); }
    static void M(object x) { Console.WriteLine("M(object)"); }

    static void N(int x) { Console.WriteLine("N(int)"); }
    static void N(string x) { Console.WriteLine("N(string)"); }

    static void Main()
    {
        M(default);           // int is better: int converts to object
        M(null);              // only object takes null
        N(null);              // only string takes null
#if BAD
        N(default);           // int and string: neither is better
#endif
    }
}
