// 슬라이드 p2-v1-hiding — new virtual 이 사슬을 끊는다, C# 1.0
using System;

class A
{
    public virtual void F() { Console.WriteLine("A.F"); }
}
class B : A
{
    public override void F() { Console.WriteLine("B.F"); }
}
class C : B
{
    public new virtual void F() { Console.WriteLine("C.F"); }
}
class D : C
{
    public override void F() { Console.WriteLine("D.F"); }
}

class App
{
    static void Main()
    {
        D d = new D();
        A a = d;
        B b = d;
        C c = d;
        a.F();        // the A chain ends at B.F
        b.F();
        c.F();        // the C chain is new and reaches D.F
        d.F();
    }
}
