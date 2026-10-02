// 슬라이드 p5-v4-opt-virtual — 기본값은 정적 형식의 선언에서, C# 4.0
using System;

class Base
{
    public virtual void Hello(string who = "base default")
    {
        Console.WriteLine("Base.Hello(" + who + ")");
    }
}

class Derived : Base
{
    public override void Hello(string who = "derived default")
    {
        Console.WriteLine("Derived.Hello(" + who + ")");
    }
}

class Program
{
    static void Main()
    {
        Derived d = new Derived();
        Base b = d;
        d.Hello();
        b.Hello();
        ((dynamic)b).Hello();
    }
}
