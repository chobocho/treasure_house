// 슬라이드 p9-v8-dim-classwin — 클래스가 인터페이스를 이긴다, C# 8.0
using System;

interface IA { void M(); }

interface IB : IA
{
    void IA.M() => Console.WriteLine("IB");
}

class Base : IA
{
    void IA.M() => Console.WriteLine("Base");
}

class Derived : Base, IB { }      // Base's IA.M or IB's?

class App
{
    static void Main()
    {
        IA a = new Derived();
        a.M();
    }
}
