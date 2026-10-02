// 슬라이드 p7-v6-exprbody-prop — 식 본문 속성, C# 6.0
using System;

class Circle
{
    double r;

    public Circle(double r)
    {
        this.r = r;
    }

    // get-only properties written with =>
    public double Radius => r;
    public double Area => Math.PI * r * r;
}

class Program
{
    static void Main()
    {
        Circle c = new Circle(2);
        Console.WriteLine(c.Radius);
        Console.WriteLine(c.Area.ToString("F3"));
#if BAD
        c.Area = 1;        // there is no setter
#endif
    }
}
