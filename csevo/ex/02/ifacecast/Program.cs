// 슬라이드 p2-v1-ifacecast — 인터페이스 캐스트는 실행 때, C# 1.0
using System;

interface IFly { void Fly(); }

class Bird { }

class Duck : Bird, IFly
{
    public void Fly() { Console.WriteLine("flap"); }
}

class App
{
    static void Main()
    {
        Bird b = new Duck();
        ((IFly)b).Fly();          // Bird is not IFly, still compiles
        b = new Bird();
        string r = b as IFly == null ? "null" : "IFly";
        Console.WriteLine("as: " + r);
        ((IFly)b).Fly();          // a subclass might have had it
    }
}
