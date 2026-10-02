// 슬라이드 p9-v8-dim-derived — 파생 인터페이스의 재정의, C# 8.0
using System;

interface IA
{
    void M() => Console.WriteLine("IA.M");
}

interface IB : IA
{
    void IA.M() => Console.WriteLine("IB overrides IA.M");
}

interface IC : IA
{
#if NONEW
    void M() => Console.WriteLine("IC.M, a new member");
#else
    new void M() => Console.WriteLine("IC.M, a new member");
#endif
}

class B : IB { }
class C : IC { }

class App
{
    static void Main()
    {
        ((IA)new B()).M();
        ((IB)new B()).M();
        ((IA)new C()).M();
        ((IC)new C()).M();
    }
}
