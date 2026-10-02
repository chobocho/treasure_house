// 슬라이드 p9-v8-dim-trait — 트레이트처럼 섞기, C# 8.0
using System;

interface INamed { string Name { get; } }

interface IWalker : INamed
{
    int Legs { get; }
    string Walk() => Name + " walks on " + Legs + " legs";
}

interface ISwimmer : INamed
{
    string Swim() => Name + " swims";
}

// the class supplies state; the interfaces supply behaviour
class Duck : IWalker, ISwimmer
{
    public string Name => "Duck";
    public int Legs => 2;
}

class Fish : ISwimmer
{
    public string Name => "Fish";
}

class App
{
    static void Main()
    {
        var d = new Duck();
        Console.WriteLine(((IWalker)d).Walk());
        Console.WriteLine(((ISwimmer)d).Swim());
        Console.WriteLine(((ISwimmer)new Fish()).Swim());
    }
}
