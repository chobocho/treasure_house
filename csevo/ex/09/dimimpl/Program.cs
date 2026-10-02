// 슬라이드 p9-v8-dim-impl — 클래스의 구현이 이긴다, C# 8.0
using System;

interface IGreeter
{
    void Hello() => Console.WriteLine("IGreeter.Hello (default)");
}

class Quiet : IGreeter { }

class Loud : IGreeter
{
    public void Hello() => Console.WriteLine("Loud.Hello");
}

class Louder : Loud { }            // inherits Loud.Hello

class Polite : IGreeter
{
    void IGreeter.Hello() => Console.WriteLine("Polite (explicit)");
}

class App
{
    static void Main()
    {
        IGreeter[] all = { new Quiet(), new Loud(), new Louder(),
                           new Polite() };
        foreach (IGreeter g in all)
            g.Hello();
    }
}
