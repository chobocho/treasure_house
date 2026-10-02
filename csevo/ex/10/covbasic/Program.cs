// 슬라이드 p10-v9-covariant — 공변 반환 형식, C# 9.0
using System;

class Food
{
    public override string ToString() => GetType().Name;
}
class Meat : Food { }

abstract class Animal
{
    public abstract Food GetFood();
    public abstract Animal Self { get; }      // get-only property
}

class Tiger : Animal
{
    public override Meat GetFood() => new Meat();
    public override Tiger Self => this;
    public void Roar() => Console.WriteLine("roar");
}

class App
{
    static void Main()
    {
        Tiger t = new Tiger();
        Meat m = t.GetFood();                 // no cast
        t.Self.Roar();                        // Tiger, not Animal
        Animal a = t;
        Console.WriteLine(m + " " + a.GetFood() + " " +
                          a.Self.GetType().Name);
    }
}
