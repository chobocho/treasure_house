// 슬라이드 p9-v8-dim-base — 제안서의 base(IB).M() 은 아직 없다, C# 8.0
using System;

interface IA { void M() => Console.WriteLine("IA"); }
interface IB : IA { void IA.M() => Console.WriteLine("IB"); }
interface IC : IA { void IA.M() => Console.WriteLine("IC"); }

class D : IB, IC
{
#if BAD
    public void M() => base(IB).M();       // proposed syntax
#else
    public void M() => Console.WriteLine("D: copy of IB's code");
#endif
}

class App
{
    static void Main() => ((IA)new D()).M();
}
