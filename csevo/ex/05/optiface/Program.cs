// 슬라이드 p5-v4-opt-iface — 인터페이스와 구현의 기본값, C# 4.0
using System;

interface IGreeter
{
    void Hi(string who = "interface default");
}

class Greeter : IGreeter
{
    public void Hi(string who = "class default")
    {
        Console.WriteLine("Hi, " + who);
    }
}

class Program
{
    static void Main()
    {
        Greeter g = new Greeter();
        IGreeter i = g;
        g.Hi();
        i.Hi();
    }
}
