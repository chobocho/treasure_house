// 슬라이드 p10-v9-tn-over — 오버로드가 늘면 깨지는 new(), C# 9.0
using System;

class A { }
class B { }

class App
{
    static void M(A a) => Console.WriteLine("M(A)");
#if B2
    static void M(B b) => Console.WriteLine("M(B)");   // added later
#endif

    static void Main()
    {
        M(new A());
        M(new());                      // target: the only M
    }
}
