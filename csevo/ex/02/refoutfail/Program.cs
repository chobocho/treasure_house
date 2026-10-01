// 슬라이드 p2-v1-refoutfail — 확정 대입 규칙, C# 1.0
using System;

class App
{
    static void Inc(ref int a) { a++; }

    static void Get(bool ok, out int v)
    {
        if (ok) v = 1;                // not assigned when !ok
    }

    static void Main()
    {
        int a;
        Inc(ref a);                   // ref needs a value first
        int b = 0;
        Inc(b);                       // ref missing at the call
        int c;
        Console.WriteLine(c);         // read before assignment
    }
}
