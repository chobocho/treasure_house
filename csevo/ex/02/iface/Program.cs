// 슬라이드 p2-v1-iface — 인터페이스는 계약만, C# 1.0
using System;

interface IShape
{
    string Name { get; }
    double Area();
}

class Square : IShape
{
    double side;
    public Square(double s) { side = s; }
    public string Name { get { return "square"; } }
    public double Area() { return side * side; }
}

class Circle : IShape
{
    double r;
    public Circle(double r) { this.r = r; }
    public string Name { get { return "circle"; } }
    public double Area() { return 3 * r * r; }      // rough pi
}

class App
{
    static void Main()
    {
        IShape[] shapes = { new Square(2), new Circle(1) };
        foreach (IShape s in shapes)
            Console.WriteLine(s.Name + " " + s.Area());
        object o = shapes[0];
        Console.WriteLine("is IShape: " + (o is IShape));
        Console.WriteLine("interface: " + typeof(IShape).IsInterface);
    }
}
