// 슬라이드 p3-v2-anon-lambda — 익명 메서드와 람다, C# 3.0
using System;

delegate int Op(int x);

class App
{
    static void Main()
    {
        Op a = delegate(int x) { return x + 1; };   // C# 2
        Op b = x => x + 1;                          // C# 3
        Console.WriteLine(a(1) + " " + b(1));
    }
}
