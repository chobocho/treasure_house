// 슬라이드 p5-v4-var-gate — 제네릭 인터페이스의 변성 선언, C# 4.0
using System;

interface IProducer<out T>
{
    T Produce();
}

class Words : IProducer<string>
{
    public string Produce() { return "word"; }
}

class Program
{
    static void Main()
    {
        IProducer<string> ps = new Words();
        IProducer<object> po = ps;         // covariance
        Console.WriteLine(po.Produce());
        Console.WriteLine(ReferenceEquals(ps, po));
    }
}
