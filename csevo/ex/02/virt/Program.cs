// 슬라이드 p2-v1-virtual — virtual 과 override, C# 1.0
using System;

class Shape
{
    public virtual string Area() { return "Shape.Area"; }
    public string Name() { return "Shape.Name"; }    // not virtual
}

class Circle : Shape
{
    public override string Area() { return "Circle.Area"; }
    public new string Name() { return "Circle.Name"; }
}

class App
{
    static void Main()
    {
        Circle c = new Circle();
        Shape s = c;            // same object, base-typed reference
        Console.WriteLine("Circle ref: " + c.Area() + " " + c.Name());
        Console.WriteLine("Shape ref:  " + s.Area() + " " + s.Name());
    }
}
