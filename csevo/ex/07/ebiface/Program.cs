// 슬라이드 p7-v6-eb-iface — 인터페이스의 식 본문 멤버, C# 8.0
using System;

interface IShape
{
    double Area { get; }
    string Describe() => "area " + Area.ToString("F1");   // default
}

class Square : IShape
{
    public double Side = 2;
    public double Area => Side * Side;
}

class Program
{
    static void Main()
    {
        IShape s = new Square();
        Console.WriteLine(s.Describe());
    }
}
