// 슬라이드 p13-v12-pc-base — 기반 클래스에 인수 넘기기, C# 12.0
using System;

class Shape(string kind)
{
    public string Kind => kind;
}

class Circle(double r) : Shape("circle")
{
    public double Area => Math.Round(Math.PI * r * r, 2);
}

class Square(double side) : Shape($"square {side}")
{
}

class Labeled(string kind, string label) : Shape(kind)
{
    public string Label { get; } = label;
}

class App
{
    static void Main()
    {
        var c = new Circle(2);
        Console.WriteLine($"{c.Kind} {c.Area}");
        Console.WriteLine(new Square(3).Kind);
        var l = new Labeled("dot", "A");
        Console.WriteLine($"{l.Kind} {l.Label}");
    }
}
