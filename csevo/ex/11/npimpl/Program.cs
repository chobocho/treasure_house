// 슬라이드 p11-v10-nonpublic — 공개 아닌 멤버의 암시적 구현, C# 10.0
using System;

// the names follow the C# 8 spec's example
interface IA
{
    internal string MI();                   // non-public, abstract
    protected internal int MP();
    string Show() => $"{MI()} {MP()}";      // public default
}

class C : IA
{
    public string MI() => "C.MI";           // implicit: C# 10
    public int MP() => 1;
}

class D : IA
{
    string IA.MI() => "D.MI";               // explicit: always fine
    int IA.MP() => 2;
}

#if INTERNAL
class E : IA                                // the spec's own case
{
    internal string MI() => "E.MI";
    protected internal int MP() => 3;
}
#endif

class App
{
    static void Main()
    {
        IA[] all = { new C(), new D() };
        foreach (IA a in all)
            Console.WriteLine(a.Show());
        Console.WriteLine(new C().MI());        // also a class member
    }
}
