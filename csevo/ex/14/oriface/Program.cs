// 슬라이드 p14-v13-or-virt — override·인터페이스 구현의 우선순위, C# 13
using System;
using System.Runtime.CompilerServices;

class Base
{
    [OverloadResolutionPriority(1)]
    public virtual void M(object o) => Console.WriteLine("Base:object");
    public virtual void M(string s) => Console.WriteLine("Base:string");
}

class Derived : Base     // overrides inherit the least-derived priority
{
    public override void M(object o) => Console.WriteLine("D:object");
    public override void M(string s) => Console.WriteLine("D:string");
}

interface I
{
    [OverloadResolutionPriority(1)]
    void N(object o);
    void N(string s);
}

class C : I              // implicit implementations: priority 0
{
    public void N(object o) => Console.WriteLine("C:object");
    public void N(string s) => Console.WriteLine("C:string");
}

class Program
{
    static void Main()
    {
        new Derived().M("x");
        new C().N("x");
        ((I)new C()).N("x");
    }
}
