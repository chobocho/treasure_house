// 슬라이드 p5-v4-opt-useless — 생략할 길이 없는 기본값, C# 4.0
using System;

interface IShape
{
    double Area(double k);
}

class Square : IShape
{
    double IShape.Area(double k = 1.0) { return 4 * k; }

    public int this[int i = 0] { get { return i; } }
}

class Program
{
    static void Main()
    {
        IShape s = new Square();
        Console.WriteLine(s.Area(2.0));
        Console.WriteLine(new Square()[3]);
    }
}
