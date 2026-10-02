// 슬라이드 p9-v8-dim-diamond — 다이아몬드와 가장 구체적인 구현, C# 8.0
using System;

interface IA { void M() => Console.WriteLine("IA"); }
interface IB : IA { void IA.M() => Console.WriteLine("IB"); }
interface IC : IA { void IA.M() => Console.WriteLine("IC"); }

// fix 1: the class decides
class Both : IB, IC
{
    public void M() => Console.WriteLine("Both decides");
}

// fix 2: a joining interface decides
interface ID : IB, IC
{
    void IA.M() => Console.WriteLine("ID decides");
}
class ViaD : ID { }

#if BAD
class Neither : IB, IC { }        // which one is IA.M?
#endif

class App
{
    static void Main()
    {
        ((IA)new Both()).M();
        ((IA)new ViaD()).M();
    }
}
